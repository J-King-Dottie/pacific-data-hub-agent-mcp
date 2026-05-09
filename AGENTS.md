# Project Agent Guide

This project is a general-purpose Pacific Data Hub research tool.

## Architecture

- `pacific_data/mcp_server.py` is the MCP entrypoint. Keep it focused on PDH.stat operations: catalog search, metadata inspection, codelists, data retrieval, row inspection, and in-memory narrowing.
- `pacific_data/pdh_client.py` contains PDH.stat API, SDMX mechanics, the dataflow XML cache, and the in-memory SQLite FTS index built from the live PDH dataflow catalog.
- `pacific_data/pptx_report.py` provides generic PowerPoint deck rendering from analyst-selected slides using native editable charts.
- `skills.md` is the single source of truth for analyst behavior, deck standards, chart-selection rules, web-research expectations, and PowerPoint output expectations.
- `.mcp.json` is the project-scoped MCP configuration for agents that clone the repo.

## Product Shape

Keep the same broad shape as the Aus Data Agent MCP:

```text
README.md -> agent entrypoint and quick start
AGENTS.md -> project architecture and development guardrails
skills.md -> analyst behavior and evidence standards
.mcp.json -> MCP wiring for agents
MCP server -> source-specific data capabilities
```

The common workflow is:

```text
user question -> AI-written FTS queries -> catalogue shortlist
-> AI picks relevant data -> inspect metadata/structure
-> retrieve real data -> inspect/narrow data -> analyze from evidence
```

## Development Rules

- Do not add topic-specific report routes. Energy, tourism, trade, health, education, climate, and macro questions must use the same general workflow.
- Do not put analyst judgment into the MCP server. The MCP should expose data capabilities, not decide the report story.
- Do not check in or write a cloned PDH catalog. PDH discovery should use live SDMX catalog retrieval, `runtime/cache/dataflows.xml`, and in-memory FTS. Do not cache retrieved data slices by default.
- When changing how reports analyze data, choose charts, use web research, write summaries, or structure PowerPoint decks, update `skills.md` in the same change.
- Keep `skills.md` concise. Prefer clear rules over long examples.
- Do not recreate separate prompt or guide files unless there is a strong runtime need. If one is added, it must point back to `skills.md` and not define conflicting behavior.
- Prefer generic reusable chart/report logic over one-off scripts.
- Label proxies and stale data clearly. Do not make the report more confident than the retrieved evidence supports.
- Recency is part of relevance. For current questions, agents must search for and prefer the latest available PDH observations, including monthly or quarterly data when available.
- Do not chart stale data as ordinary evidence. Data more than three years old should usually be excluded from current-event reports unless it is essential structural context and no recent proxy exists.
- Chart titles must make specific claims in plain English, and subtitles must explain how/why the data supports the claim. Use the fewest words that properly explain the mechanism, not the shortest possible sentence. Avoid vague headings that only name a theme.
- Do not generate generic fallback chart notes in code. Chart notes are analyst/model-authored caveats based on the inspected data and should be omitted when no real caveat has been written.
- Do not pad reports with generic macro/context datasets. Only retrieve and chart context when it is directly relevant to the user's question.

## Intended Flow

1. Use web research for context and narrative awareness.
2. Have the AI translate the user request into concise FTS catalogue queries using likely data/indicator/source wording; each query should return about 20 candidates by default.
3. Treat the returned shortlists as unranked candidate pools; the AI analyst selects one or more datasets, then inspects metadata/codelists.
4. Retrieve valid PDH.stat slices in memory.
5. Analyze using `skills.md`.
6. Produce one compact sourced PowerPoint `.pptx`: executive summary slide first, then one editable native chart per evidence slide. Use `pacific_data/pptx_report.py` if a local helper is useful. Do not leave report sidecars such as Word, Markdown, PDF, runtime artifacts, JSON plans, or debug files unless the user explicitly asks for them.

## Before Merging Report Changes

- Confirm `skills.md` still matches the implemented behavior.
- Confirm there are no hard-coded sector or country report paths.
- Confirm every report chart uses the latest relevant available data, or clearly justifies any stale structural chart.
- Confirm every chart title/subtitle pair says what the data proves and why it matters in simple language. If the subtitle is terse but does not explain the mechanism, rewrite it.
- Run Python compile checks for touched modules.
- Run a small `pptx_report.py` smoke test when PowerPoint generation changed. Use `inspect_pptx_report()` or package inspection to confirm charts are native editable chart parts rather than images.
- Render or otherwise inspect the saved deck when possible. Fix text encoding problems, label collisions, and sparse line charts that could imply missing data is zero.
