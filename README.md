# Pacific Data Hub MCP

A small, general-purpose MCP server and analyst workflow for Pacific Data Hub
(PDH.stat) data.

The core idea is simple:

```text
question -> AI-written FTS shortlist queries over the full live PDH catalog
-> inspect SDMX structure -> retrieve real data in memory -> analyze
-> write one sourced PowerPoint deck
```

The MCP is intentionally data-source focused: it retrieves the live PDH.stat
catalog, builds an in-memory SQLite FTS shortlist, returns
unranked candidate pools, inspects metadata and codelists, retrieves valid SDMX
data without writing runtime artifacts. The analysis and report-writing behavior lives in
[`skills.md`](skills.md). A small PowerPoint helper is available for agents that
want to write the final `.pptx` from analyst-selected evidence.

## For AI Agents

Start with these files:

- [`skills.md`](skills.md): how to behave as the analyst using PDH data.
- [`AGENTS.md`](AGENTS.md): how the project is structured and how to extend it.
- [`pacific_data/mcp_server.py`](pacific_data/mcp_server.py): the MCP tool surface.
- [`pacific_data/pptx_report.py`](pacific_data/pptx_report.py): optional PowerPoint deck helper.

The intended agent flow is: search the PDH catalogue with FTS, inspect metadata
and codelists, retrieve only relevant rows, check the latest available period,
analyze the data, then produce one sourced PowerPoint deck.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the MCP server:

```bash
python -m pacific_data.mcp_server
```

The MCP does not persist retrieved data, evidence JSON, plans, debug files,
PDFs, or Markdown. The only runtime cache is `runtime/cache/dataflows.xml`, used
to avoid re-fetching the PDH dataflow catalogue on every catalogue search.

The default output style is defined in [`skills.md`](skills.md): a compact
PowerPoint deck with an executive-summary slide followed by one editable native
chart per evidence slide, narrative titles, plain-English subtitles, notes,
source lines, and clear caveats.

The PowerPoint helper includes `inspect_pptx_report()` for smoke checks: it
counts slides, native chart parts, embedded workbooks, and media files so agents
can catch pasted-image charts before delivery.

Example Codex config:

```toml
[mcp_servers.pacific_data]
command = "python"
args = ["-m", "pacific_data.mcp_server"]
enabled = true
tool_timeout_sec = 120
```

## Tools

- `search_pdh_catalog`: run one or multiple FTS shortlist queries over the full live PDH.stat dataflow catalog; results are unranked candidates, 20 per query by default.
- `get_pdh_metadata`: inspect dimensions and codelists for a dataflow.
- `get_pdh_codelist`: browse valid codelist values.
- `retrieve_pdh_data`: retrieve SDMX CSV data and return rows directly.
- `inspect_pdh_data`: summarize retrieved rows.
- `narrow_pdh_data`: filter retrieved rows in memory.

## Web Research

Web research is an analyst responsibility described in [`skills.md`](skills.md),
not part of the PDH MCP. Use it to understand current narratives and claims
worth testing; keep PDH data as the evidence base for quantitative claims.

## Notes

- PDH.stat is SDMX-based and maintained by SPC.
- Default endpoint: `https://stats-sdmx-disseminate.pacificdata.org/rest`
- Catalog discovery uses live SDMX retrieval, a cache of the dataflows XML, and
  an in-memory FTS index. It does not use a checked-in catalog clone.
- There are no topic-specific report routes. Every question follows the same
  general PDH retrieval, analysis, and PowerPoint workflow.
- Report generation should not emit sidecar Word, Markdown, PDF, runtime
  artifacts, JSON plans, or debug files unless explicitly requested.

## Smoke Check

```bash
python -B -m py_compile pacific_data/*.py
```
