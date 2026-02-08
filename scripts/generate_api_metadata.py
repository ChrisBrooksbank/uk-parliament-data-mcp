#!/usr/bin/env python3
"""Generate compact API metadata JSON from OpenAPI/Swagger spec files.

Reads all 14 spec files from context/ and produces a single api_metadata.json
in src/uk_parliament_mcp/cli/ for distribution with the package.

Usage:
    python scripts/generate_api_metadata.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Mapping from spec filename (without .json) to a short CLI-friendly name
API_NAMES: dict[str, str] = {
    "bills-api": "bills",
    "committees-api": "committees",
    "commonsvotes-api": "commonsvotes",
    "erskinemay-api": "erskinemay",
    "hansard-api": "hansard",
    "interests-api": "interests",
    "lordsvotes-api": "lordsvotes",
    "members-api": "members",
    "oralquestions-api": "oralquestions",
    "parliamentnow-api": "parliamentnow",
    "statutoryinstruments-api": "statutoryinstruments",
    "treaties-api": "treaties",
    "whatson-api": "whatson",
    "writtenquestions-api": "writtenquestions",
}

# Base URLs for APIs that don't declare servers/host in their spec
BASE_URLS: dict[str, str] = {
    "bills": "https://bills-api.parliament.uk",
    "committees": "https://committees-api.parliament.uk",
    "commonsvotes": "https://commonsvotes-api.parliament.uk",
    "erskinemay": "https://erskinemay-api.parliament.uk",
    "hansard": "https://hansard-api.parliament.uk",
    "interests": "https://interests-api.parliament.uk",
    "lordsvotes": "https://lordsvotes-api.parliament.uk",
    "members": "https://members-api.parliament.uk",
    "oralquestions": "https://oralquestionsandmotions-api.parliament.uk",
    "parliamentnow": "https://now-api.parliament.uk",
    "statutoryinstruments": "https://statutoryinstruments-api.parliament.uk",
    "treaties": "https://treaties-api.parliament.uk",
    "whatson": "https://whatson-api.parliament.uk",
    "writtenquestions": "https://writtenquestions-api.parliament.uk",
}


def resolve_ref(ref: str) -> str:
    """Extract the schema name from a $ref string."""
    return ref.rsplit("/", 1)[-1]


def extract_param_type(param: dict) -> tuple[str | None, str | None]:
    """Extract type and format from a parameter, handling both spec formats.

    OpenAPI 3.0: type under param.schema.type
    Swagger 2.0: type as direct param.type
    """
    if "schema" in param:
        schema = param["schema"]
        # Handle allOf refs
        if "allOf" in schema:
            for item in schema["allOf"]:
                if "$ref" in item:
                    return resolve_ref(item["$ref"]), None
            return None, None
        if "$ref" in schema:
            return resolve_ref(schema["$ref"]), None
        return schema.get("type"), schema.get("format")
    return param.get("type"), param.get("format")


def extract_param_enum(param: dict) -> list[str] | None:
    """Extract enum values from a parameter."""
    enum = param["schema"].get("enum") if "schema" in param else param.get("enum")
    return enum if enum else None


def extract_param_default(param: dict) -> str | int | bool | None:
    """Extract default value from a parameter."""
    if "schema" in param:
        return param["schema"].get("default")
    return param.get("default")


def extract_parameter(param: dict) -> dict:
    """Extract a compact parameter representation."""
    ptype, pfmt = extract_param_type(param)
    result: dict = {
        "name": param.get("name", ""),
        "in": param.get("in", ""),
        "required": param.get("required", False),
    }
    if ptype:
        result["type"] = ptype
    if pfmt:
        result["format"] = pfmt
    desc = param.get("description")
    if desc:
        result["description"] = desc
    default = extract_param_default(param)
    if default is not None:
        result["default"] = default
    enum = extract_param_enum(param)
    if enum is not None:
        result["enum"] = enum
    return result


def extract_response_schema(operation: dict, is_swagger: bool) -> str | None:
    """Extract the response schema ref for a 200 response."""
    responses = operation.get("responses", {})
    resp_200 = responses.get("200", {})

    if is_swagger:
        schema = resp_200.get("schema", {})
        if "$ref" in schema:
            return resolve_ref(schema["$ref"])
        if "items" in schema and "$ref" in schema["items"]:
            return resolve_ref(schema["items"]["$ref"]) + "[]"
        return None

    # OpenAPI 3.0: look in content
    content = resp_200.get("content", {})
    for media_type in ("application/json", "text/json", "text/plain"):
        if media_type in content:
            schema = content[media_type].get("schema", {})
            if "$ref" in schema:
                return resolve_ref(schema["$ref"])
            if "items" in schema and "$ref" in schema["items"]:
                return resolve_ref(schema["items"]["$ref"]) + "[]"
            return None
    return None


def extract_endpoint(path: str, method: str, operation: dict, is_swagger: bool) -> dict:
    """Extract a compact endpoint representation."""
    result: dict = {
        "method": method.upper(),
        "path": path,
    }
    summary = operation.get("summary")
    if summary:
        result["summary"] = summary
    desc = operation.get("description")
    if desc:
        result["description"] = desc
    tags = operation.get("tags")
    if tags:
        result["tags"] = tags
    op_id = operation.get("operationId")
    if op_id:
        result["operationId"] = op_id
    params = operation.get("parameters", [])
    if params:
        result["parameters"] = [extract_parameter(p) for p in params]
    response_schema = extract_response_schema(operation, is_swagger)
    if response_schema:
        result["responseSchema"] = response_schema
    return result


def extract_schema_property(name: str, prop: dict) -> dict:
    """Extract a compact schema property representation."""
    result: dict = {"name": name}
    if "$ref" in prop:
        result["type"] = resolve_ref(prop["$ref"])
    elif "type" in prop:
        result["type"] = prop["type"]
        if prop["type"] == "array" and "items" in prop:
            items = prop["items"]
            if "$ref" in items:
                result["itemType"] = resolve_ref(items["$ref"])
            elif "type" in items:
                result["itemType"] = items["type"]
    if prop.get("nullable"):
        result["nullable"] = True
    desc = prop.get("description")
    if desc:
        result["description"] = desc
    enum = prop.get("enum")
    if enum:
        result["enum"] = enum
    fmt = prop.get("format")
    if fmt:
        result["format"] = fmt
    return result


def extract_schema(name: str, schema: dict) -> dict:
    """Extract a compact schema representation."""
    result: dict = {"name": name}
    stype = schema.get("type")
    if stype:
        result["type"] = stype
    desc = schema.get("description")
    if desc:
        result["description"] = desc
    enum = schema.get("enum")
    if enum:
        result["enum"] = enum
    props = schema.get("properties", {})
    if props:
        result["properties"] = [
            extract_schema_property(pname, pdef) for pname, pdef in props.items()
        ]
    return result


def process_spec(spec_path: Path, api_name: str) -> dict:
    """Process a single spec file into compact metadata."""
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    is_swagger = "swagger" in spec
    info = spec.get("info", {})

    # Determine base URL
    base_url = BASE_URLS.get(api_name, "")
    if is_swagger and "host" in spec:
        scheme = "https"
        if "schemes" in spec and spec["schemes"]:
            scheme = "https" if "https" in spec["schemes"] else spec["schemes"][0]
        base_url = f"{scheme}://{spec['host']}"
    elif "servers" in spec and spec["servers"]:
        base_url = spec["servers"][0].get("url", base_url)

    # Extract endpoints
    endpoints = []
    for path, path_item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method in path_item:
                endpoints.append(extract_endpoint(path, method, path_item[method], is_swagger))

    # Extract schemas
    schemas = []
    if is_swagger:
        schema_dict = spec.get("definitions", {})
    else:
        schema_dict = spec.get("components", {}).get("schemas", {})

    for sname, sdef in schema_dict.items():
        schemas.append(extract_schema(sname, sdef))

    return {
        "name": api_name,
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "baseUrl": base_url,
        "specVersion": spec.get("openapi") or spec.get("swagger", ""),
        "endpointCount": len(endpoints),
        "schemaCount": len(schemas),
        "endpoints": endpoints,
        "schemas": schemas,
    }


def main() -> None:
    """Generate api_metadata.json from all spec files."""
    project_root = Path(__file__).resolve().parent.parent
    context_dir = project_root / "context"
    output_path = project_root / "src" / "uk_parliament_mcp" / "cli" / "api_metadata.json"

    if not context_dir.exists():
        print(f"Error: context directory not found at {context_dir}", file=sys.stderr)
        sys.exit(1)

    spec_files = sorted(context_dir.glob("*.json"))
    if not spec_files:
        print(f"Error: no spec files found in {context_dir}", file=sys.stderr)
        sys.exit(1)

    apis = []
    for spec_path in spec_files:
        stem = spec_path.stem
        api_name = API_NAMES.get(stem)
        if api_name is None:
            print(f"Warning: unknown spec file {spec_path.name}, skipping", file=sys.stderr)
            continue
        print(f"Processing {spec_path.name} -> {api_name}")
        apis.append(process_spec(spec_path, api_name))

    metadata = {"apis": apis}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, separators=(",", ":"))

    # Show stats
    total_endpoints = sum(a["endpointCount"] for a in apis)
    total_schemas = sum(a["schemaCount"] for a in apis)
    size_kb = output_path.stat().st_size / 1024
    print(f"\nGenerated {output_path}")
    print(f"  APIs: {len(apis)}")
    print(f"  Endpoints: {total_endpoints}")
    print(f"  Schemas: {total_schemas}")
    print(f"  Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
