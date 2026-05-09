from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install MCP dependencies first: pip install -r requirements.txt") from exc

from .pdh_client import (
    filter_rows,
    get_codelist_codes,
    get_dataflow_metadata,
    inspect_data,
    retrieve_data,
    search_dataflow_shortlists,
    search_dataflows,
)

mcp = FastMCP("Pacific Data Hub")


@mcp.tool()
def search_pdh_catalog(query: str = "", queries: list[str] | None = None, country: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Search the PDH.stat dataflow catalog with SQLite FTS.

    Use `query` for one shortlist query, or `queries` for multiple independent
    shortlist queries when the AI analyst wants to compare possible evidence
    angles. Results are unranked candidate pools from the live catalog, backed
    by the dataflows XML cache; default shortlist length is 20 per query.
    """
    if queries:
        return search_dataflow_shortlists(queries=queries, country=country, limit=limit)
    return search_dataflows(query=query, country=country, limit=limit)


@mcp.tool()
def get_pdh_metadata(dataflow_id: str, version: str = "latest") -> dict[str, Any]:
    """Return dimensions, codelists, annotations, and source URL for a dataflow."""
    return get_dataflow_metadata(dataflow_id=dataflow_id, version=version)


@mcp.tool()
def get_pdh_codelist(codelist_id: str, version: str = "latest", search: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Browse a PDH.stat codelist."""
    return get_codelist_codes(codelist_id=codelist_id, version=version, search=search, limit=limit)


@mcp.tool()
def retrieve_pdh_data(
    dataflow_id: str,
    key: str | None = None,
    filters: dict[str, Any] | None = None,
    country: str | None = None,
    start_period: str | None = None,
    end_period: str | None = None,
    version: str = "latest",
) -> dict[str, Any]:
    """Retrieve PDH.stat CSV data and return rows directly without writing files."""
    return retrieve_data(
        dataflow_id=dataflow_id,
        key=key,
        filters=filters,
        country=country,
        start_period=start_period,
        end_period=end_period,
        version=version,
    )


@mcp.tool()
def inspect_pdh_data(payload: dict[str, Any]) -> dict[str, Any]:
    """Summarize retrieved PDH data already returned by retrieve_pdh_data."""
    return inspect_data(payload)


@mcp.tool()
def narrow_pdh_data(payload: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
    """Filter retrieved PDH rows in memory with exact column-value filters."""
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    narrowed = filter_rows(rows, filters)
    return {
        "kind": "pdh_csv_narrowed",
        "filters": filters,
        "dataflow_id": payload.get("dataflow_id"),
        "dataflow_name": payload.get("dataflow_name"),
        "retrieval_url": payload.get("retrieval_url"),
        "rows": narrowed,
        "summary": inspect_data({"rows": narrowed}),
    }


if __name__ == "__main__":
    mcp.run()
