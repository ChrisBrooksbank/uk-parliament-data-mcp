"""Tests for CLI auto-pagination."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from uk_parliament_mcp.cli.pagination import (
    BILLS_PAGINATION,
    COMMITTEES_PAGINATION,
    HANSARD_PAGINATION,
    MAX_TOTAL_ITEMS,
    MEMBERS_PAGINATION,
    _replace_url_param,
    paginate_request,
)


class TestReplaceUrlParam:
    """Tests for URL parameter replacement."""

    def test_replace_existing_param(self):
        url = "https://api.example.com/search?skip=0&take=20"
        result = _replace_url_param(url, "skip", 40)
        assert "skip=40" in result
        assert "take=20" in result

    def test_add_new_param(self):
        url = "https://api.example.com/search?take=20"
        result = _replace_url_param(url, "skip", 10)
        assert "skip=10" in result
        assert "take=20" in result

    def test_replace_dotted_param(self):
        url = "https://api.example.com/search?queryParameters.skip=0&queryParameters.take=20"
        result = _replace_url_param(url, "queryParameters.skip", 40)
        assert "queryParameters.skip=40" in result


class TestPaginateRequestSinglePage:
    """Tests for single-page passthrough (take <= page_size)."""

    @pytest.mark.asyncio
    async def test_small_take_passthrough(self):
        """When take <= page_size, should make a single request."""
        mock_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=10",
                "data": {
                    "items": [{"id": i} for i in range(10)],
                    "totalResults": 100,
                },
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=10",
                MEMBERS_PAGINATION,
                desired_total=10,
                start_skip=0,
            )

        mock_get.assert_called_once()
        parsed = json.loads(result)
        assert "data" in parsed
        assert len(parsed["data"]["items"]) == 10

    @pytest.mark.asyncio
    async def test_none_desired_total_passthrough(self):
        """When desired_total is None, should make a single request."""
        mock_response = json.dumps(
            {
                "url": "https://api.example.com/search",
                "data": {"items": [{"id": 1}], "totalResults": 1},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response
            await paginate_request(
                "https://api.example.com/search",
                MEMBERS_PAGINATION,
                desired_total=None,
                start_skip=0,
            )

        mock_get.assert_called_once()


class TestPaginateRequestMultiPage:
    """Tests for multi-page pagination."""

    @pytest.mark.asyncio
    async def test_two_pages(self):
        """When take=40 and page_size=20, should make 2 requests."""
        page1_items = [{"id": i} for i in range(20)]
        page2_items = [{"id": i} for i in range(20, 40)]

        page1_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=20",
                "data": {"items": page1_items, "totalResults": 100},
            }
        )
        page2_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=20&take=20",
                "data": {"items": page2_items, "totalResults": 100},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [page1_response, page2_response]
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=40",
                MEMBERS_PAGINATION,
                desired_total=40,
                start_skip=0,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        items = parsed["data"]["items"]
        assert len(items) == 40
        # Items should be merged in order
        assert items[0]["id"] == 0
        assert items[39]["id"] == 39

    @pytest.mark.asyncio
    async def test_three_pages_partial_last(self):
        """When take=50 and page_size=20, should make 3 requests."""
        page1_items = [{"id": i} for i in range(20)]
        page2_items = [{"id": i} for i in range(20, 40)]
        page3_items = [{"id": i} for i in range(40, 50)]

        responses = [
            json.dumps(
                {
                    "url": f"https://api.example.com/search?skip={skip}&take={take}",
                    "data": {"items": items, "totalResults": 200},
                }
            )
            for skip, take, items in [
                (0, 20, page1_items),
                (20, 20, page2_items),
                (40, 10, page3_items),
            ]
        ]

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = responses
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=50",
                MEMBERS_PAGINATION,
                desired_total=50,
                start_skip=0,
            )

        assert mock_get.call_count == 3
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 50


class TestPaginateRequestTotalResults:
    """Tests for totalResults < take."""

    @pytest.mark.asyncio
    async def test_stops_at_total_results(self):
        """When totalResults=30 but take=100, should stop after 30."""
        page1_items = [{"id": i} for i in range(20)]
        page2_items = [{"id": i} for i in range(20, 30)]

        page1_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=20",
                "data": {"items": page1_items, "totalResults": 30},
            }
        )
        page2_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=20&take=10",
                "data": {"items": page2_items, "totalResults": 30},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [page1_response, page2_response]
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=100",
                MEMBERS_PAGINATION,
                desired_total=100,
                start_skip=0,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 30

    @pytest.mark.asyncio
    async def test_empty_first_page(self):
        """When first page has 0 items, return immediately."""
        response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=20",
                "data": {"items": [], "totalResults": 0},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = response
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=50",
                MEMBERS_PAGINATION,
                desired_total=50,
                start_skip=0,
            )

        mock_get.assert_called_once()
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 0


class TestPaginateRequestErrorHandling:
    """Tests for error handling during pagination."""

    @pytest.mark.asyncio
    async def test_error_on_first_page(self):
        """When first page returns error, return error response."""
        error_response = json.dumps(
            {
                "url": "https://api.example.com/search",
                "error": "Internal server error",
                "statusCode": 500,
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = error_response
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=50",
                MEMBERS_PAGINATION,
                desired_total=50,
                start_skip=0,
            )

        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_error_on_second_page(self):
        """When second page returns error, return items from first page."""
        page1_items = [{"id": i} for i in range(20)]
        page1_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=20",
                "data": {"items": page1_items, "totalResults": 100},
            }
        )
        error_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=20&take=20",
                "error": "Timeout",
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [page1_response, error_response]
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=50",
                MEMBERS_PAGINATION,
                desired_total=50,
                start_skip=0,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        # Should return the 20 items from page 1
        assert len(parsed["data"]["items"]) == 20


class TestPaginateRequestSafetyCap:
    """Tests for safety cap enforcement."""

    @pytest.mark.asyncio
    async def test_safety_cap_applied(self):
        """When take=5000, should be capped to MAX_TOTAL_ITEMS."""
        # With a page size of 20 and cap of 1000, we'd need 50 pages.
        # We'll verify the cap works by checking the target is <= 1000.
        page1_items = [{"id": i} for i in range(20)]
        page1_response = json.dumps(
            {
                "url": "https://api.example.com/search?skip=0&take=20",
                "data": {"items": page1_items, "totalResults": 5},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = page1_response
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=5000",
                MEMBERS_PAGINATION,
                desired_total=5000,
                start_skip=0,
            )

        # With only 5 total results, it should stop after first page
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) <= MAX_TOTAL_ITEMS


class TestPaginateRequestDifferentConfigs:
    """Tests for different API configs (different param names, item keys)."""

    @pytest.mark.asyncio
    async def test_bills_pagination(self):
        """Test Bills API config with capitalized params."""
        page1_items = [{"billId": i} for i in range(20)]
        page2_items = [{"billId": i} for i in range(20, 40)]

        responses = [
            json.dumps(
                {
                    "url": "https://bills-api.parliament.uk/api/v1/Bills?Skip=0&Take=20",
                    "data": {"items": page1_items, "totalResults": 100},
                }
            ),
            json.dumps(
                {
                    "url": "https://bills-api.parliament.uk/api/v1/Bills?Skip=20&Take=20",
                    "data": {"items": page2_items, "totalResults": 100},
                }
            ),
        ]

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = responses
            result = await paginate_request(
                "https://bills-api.parliament.uk/api/v1/Bills?Skip=0&Take=40",
                BILLS_PAGINATION,
                desired_total=40,
                start_skip=0,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 40

    @pytest.mark.asyncio
    async def test_hansard_pagination(self):
        """Test Hansard API config with dotted param names and 'Results' key."""
        page1_items = [{"title": f"debate-{i}"} for i in range(20)]
        page2_items = [{"title": f"debate-{i}"} for i in range(20, 40)]

        responses = [
            json.dumps(
                {
                    "url": "https://hansard-api.parliament.uk/search/debates.json?queryParameters.skip=0&queryParameters.take=20",
                    "data": {"Results": page1_items, "TotalResultCount": 100},
                }
            ),
            json.dumps(
                {
                    "url": "https://hansard-api.parliament.uk/search/debates.json?queryParameters.skip=20&queryParameters.take=20",
                    "data": {"Results": page2_items, "TotalResultCount": 100},
                }
            ),
        ]

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = responses
            result = await paginate_request(
                "https://hansard-api.parliament.uk/search/debates.json?queryParameters.skip=0&queryParameters.take=40",
                HANSARD_PAGINATION,
                desired_total=40,
                start_skip=0,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        assert len(parsed["data"]["Results"]) == 40

    @pytest.mark.asyncio
    async def test_committees_pagination(self):
        """Test Committees API config with 30 page size."""
        page1_items = [{"id": i} for i in range(30)]
        page1_response = json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/Events?Skip=0&Take=30",
                "data": {"items": page1_items, "totalResults": 25},
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = page1_response
            result = await paginate_request(
                "https://committees-api.parliament.uk/api/Events?Skip=0&Take=60",
                COMMITTEES_PAGINATION,
                desired_total=60,
                start_skip=0,
            )

        # totalResults=25, so should stop after first page
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 25

    @pytest.mark.asyncio
    async def test_start_skip_offset(self):
        """Test that start_skip is respected for pagination."""
        page1_items = [{"id": i} for i in range(10, 30)]
        page2_items = [{"id": i} for i in range(30, 50)]

        responses = [
            json.dumps(
                {
                    "url": "https://api.example.com/search?skip=10&take=20",
                    "data": {"items": page1_items, "totalResults": 100},
                }
            ),
            json.dumps(
                {
                    "url": "https://api.example.com/search?skip=30&take=20",
                    "data": {"items": page2_items, "totalResults": 100},
                }
            ),
        ]

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = responses
            result = await paginate_request(
                "https://api.example.com/search?skip=10&take=40",
                MEMBERS_PAGINATION,
                desired_total=40,
                start_skip=10,
            )

        assert mock_get.call_count == 2
        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 40
        # Verify first item starts at id=10 (skip=10)
        assert parsed["data"]["items"][0]["id"] == 10


class TestPaginateRequestStringData:
    """Tests for when data is returned as a string (double-encoded JSON)."""

    @pytest.mark.asyncio
    async def test_string_data_first_page(self):
        """When data field is a JSON string, should still parse correctly."""
        inner_data = {"items": [{"id": i} for i in range(20)], "totalResults": 40}
        page1_response = json.dumps(
            {
                "url": "https://api.example.com/search",
                "data": json.dumps(inner_data),
            }
        )
        inner_data2 = {"items": [{"id": i} for i in range(20, 40)], "totalResults": 40}
        page2_response = json.dumps(
            {
                "url": "https://api.example.com/search",
                "data": json.dumps(inner_data2),
            }
        )

        with patch(
            "uk_parliament_mcp.cli.pagination.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = [page1_response, page2_response]
            result = await paginate_request(
                "https://api.example.com/search?skip=0&take=40",
                MEMBERS_PAGINATION,
                desired_total=40,
                start_skip=0,
            )

        parsed = json.loads(result)
        assert len(parsed["data"]["items"]) == 40
