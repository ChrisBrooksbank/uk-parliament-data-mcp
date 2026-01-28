"""HTTP client with retry logic for Parliament API requests."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# Configuration constants (matching C# implementation)
HTTP_TIMEOUT = 30.0  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1.0  # seconds

# HTTP status codes that should trigger a retry
TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def build_url(base_url: str, parameters: dict[str, Any]) -> str:
    """
    Build URL with query parameters, filtering out None and empty values.

    Equivalent to C# BaseTools.BuildUrl()

    Args:
        base_url: The base URL without query parameters
        parameters: Dictionary of parameter names to values

    Returns:
        URL with query string, or just base_url if no valid parameters
    """
    valid_params = {
        k: str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in parameters.items()
        if v is not None and v != ""
    }

    if not valid_params:
        return base_url

    return f"{base_url}?{urlencode(valid_params)}"


def _is_retryable_status(status_code: int) -> bool:
    """Check if HTTP status code is transient and should be retried."""
    return status_code in TRANSIENT_STATUS_CODES


class ParliamentHTTPClient:
    """Async HTTP client with retry logic for Parliament APIs."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_result(self, url: str) -> str:
        """
        Make HTTP GET request with retry logic.

        Returns JSON serialized response matching C# format:
        - Success: {"url": "...", "data": "..."}
        - Error: {"url": "...", "error": "...", "statusCode": N}

        Equivalent to C# BaseTools.GetResult()
        """
        client = await self._get_client()

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                logger.info(
                    "Making HTTP request to %s (attempt %d/%d)",
                    url,
                    attempt + 1,
                    MAX_RETRY_ATTEMPTS,
                )

                response = await client.get(url)

                if response.is_success:
                    data = response.text
                    logger.info("Successfully retrieved data from %s", url)
                    return json.dumps({"url": url, "data": data})

                if _is_retryable_status(response.status_code):
                    logger.warning(
                        "Transient failure for %s: %d. Attempt %d/%d",
                        url,
                        response.status_code,
                        attempt + 1,
                        MAX_RETRY_ATTEMPTS,
                    )
                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))
                        continue

                # Non-retryable error or final attempt
                error_message = (
                    f"HTTP request failed with status {response.status_code}: "
                    f"{response.reason_phrase}"
                )
                logger.error("Final failure for %s: %d", url, response.status_code)
                return json.dumps(
                    {"url": url, "error": error_message, "statusCode": response.status_code}
                )

            except httpx.TimeoutException:
                logger.warning(
                    "Request to %s timed out. Attempt %d/%d",
                    url,
                    attempt + 1,
                    MAX_RETRY_ATTEMPTS,
                )
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    return json.dumps(
                        {"url": url, "error": "Request timed out after multiple attempts"}
                    )
                await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))

            except httpx.NetworkError as e:
                logger.warning(
                    "Network error for %s: %s. Attempt %d/%d",
                    url,
                    str(e),
                    attempt + 1,
                    MAX_RETRY_ATTEMPTS,
                )
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    return json.dumps({"url": url, "error": f"Network error: {e!s}"})
                await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))

            except Exception as e:
                logger.error("Unexpected error for %s: %s", url, str(e))
                return json.dumps({"url": url, "error": f"Unexpected error: {e!s}"})

        return json.dumps({"url": url, "error": "Maximum retry attempts exceeded"})


# Global client instance for reuse across tools
_client = ParliamentHTTPClient()


async def get_result(url: str) -> str:
    """Convenience function using global client."""
    return await _client.get_result(url)
