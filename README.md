# Pacific Data Hub Agent MCP

A small, general-purpose MCP server and analyst workflow for Pacific Data Hub
(PDH.stat) data.

Produced by [Dottie AI Studio](https://dottieaistudio.com.au/).

The core idea is simple:

```text
question -> AI-written FTS queries over the full live PDH catalog
-> shortlist candidates -> pick relevant data -> inspect SDMX structure
-> retrieve real data -> inspect/narrow rows -> analyze
-> write one sourced PowerPoint deck when reporting
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
- [`.mcp.json`](.mcp.json): project-scoped MCP config.
- [`pacific_data/mcp_server.py`](pacific_data/mcp_server.py): the MCP tool surface.
- [`pacific_data/pptx_report.py`](pacific_data/pptx_report.py): optional PowerPoint deck helper.

The intended agent flow is: write better FTS queries, search the PDH catalogue,
pick relevant data, inspect metadata and codelists, retrieve real rows, inspect
and narrow the data, analyze the evidence, then produce one sourced PowerPoint
deck when reporting.

## Data Coverage

The MCP works against the live PDH.stat SDMX catalogue from the Pacific Data Hub. It is general-purpose across PDH domains rather than energy-specific.

Common discovery areas include:

- energy, electricity, renewables, fuel imports, tariffs, access
- trade, imports, exports, goods, services, food and commodity trade
- national accounts, GDP, balance of payments, prices, inflation
- population, labour, health, education, gender, WASH, agriculture, land
- climate, disasters, environment, Blue Pacific 2050, SDG indicators
- World Bank, ADB, Lowy aid finance, cyber, governance, digital adoption selections where PDH publishes them

Useful query keywords:

`Pacific Data Hub`, `PDH.stat`, `SPC`, `SDMX`, `Pacific islands`, `Fiji`, `Samoa`, `Tonga`, `Vanuatu`, `Solomon Islands`, `Kiribati`, `Tuvalu`, `Palau`, `Nauru`, `Niue`, `Cook Islands`, `Marshall Islands`, `Micronesia`, `Papua New Guinea`, `energy`, `electricity`, `renewable`, `fuel imports`, `trade`, `GDP`, `balance of payments`, `prices`, `population`, `SDG`, `health`, `education`, `climate`, `disasters`.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Example project MCP config is also provided in [`.mcp.json`](.mcp.json).

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
