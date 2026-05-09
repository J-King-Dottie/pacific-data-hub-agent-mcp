# Pacific Data Hub Analyst Skill

Use this skill for Pacific Data Hub analysis and PowerPoint slide decks.

## Architecture

- MCP scope: query PDH.stat, inspect metadata/codelists, and retrieve valid data without writing runtime artifacts. The dataflow catalogue XML may be cached; retrieved evidence should not be persisted by default.
- Skill scope: research, analysis, chart selection, narrative, and PowerPoint deck standards.
- Do not add topic-specific report routes. All sectors and countries use the same workflow.

## Workflow

1. Parse the question: geography, topic, sector, time horizon, decision context, comparison set.
2. Run web research every time to understand current narratives, policy context, and claims worth testing. Cite it separately; do not treat snippets as data.
3. Translate the user's wording into better FTS catalogue queries before searching. User questions are often not good retrieval queries; use concise data terms, synonyms, sector terms, indicators, and likely source language. Run multiple different FTS queries when useful to compare candidate pools and decide which datasets are relevant.
4. Treat shortlist results as unranked candidate pools. The AI analyst chooses one or more datasets using the returned catalogue information, then inspects metadata and codelists before retrieval.
5. Retrieve targeted PDH slices with valid SDMX keys and inspect the returned rows before analysis.
6. Check the latest period in every retrieved slice before deciding what to chart. Prefer the most recent relevant data, even if it means using a broader but still meaningful indicator.
7. Analyze direct indicators first, then recent close proxies. Label proxy limits clearly.
8. Build the PowerPoint deck from relevant evidence, not from a pre-decided story or generic context.

## Analysis Rules

- Convert `UNIT_MULT` before comparing values.
- Align units, periods, frequency, country coverage, and definitions.
- Recency is a relevance test. For current questions, do not use old data as normal evidence when more recent relevant evidence exists.
- Prefer latest available observations and high-frequency data for current events. Monthly or quarterly data beats annual data when both answer the question.
- Stale data is exceptional. For current analysis, data more than three years old should usually be excluded from charts unless it is structural context that is essential and no recent proxy exists.
- If stale structural data is used, make it a clearly secondary panel, state the latest period in the title/subtitle or notes, and explain why newer evidence cannot answer that part of the question.
- Use web research to test external narratives, including narratives the data weakens.
- Do not fabricate missing values, policies, companies, market size, or causality.
- Separate facts from interpretation.

## Chart Rules

- Use as many chart-led panels as the relevant evidence supports; do not target a fixed number.
- Put the most decision-relevant chart first; later panels may be less central but must still inform the question.
- Reuse the same dataset when a different angle adds insight: trend, ranking, decomposition, intensity, per-capita, or component mix.
- Prefer time series for momentum, bars for current comparisons, stacked bars for totals split by source/category, and per-capita or intensity views when scale distorts comparison.
- For current questions, chart the latest available period first. Do not lead with historical context when the user is asking what is happening now.
- Avoid charts where the latest observation is old unless the report explicitly needs long-run structural context and the chart is labelled as such.
- Avoid filler charts. Every chart must support a claim.
- Do not add broad context charts unless they directly help answer the question.
- Chart titles must be specific narrative claims, not vague themes. Do not use empty phrases such as "exposure remains", "context matters", or "risk is material" unless the title says what is exposed, to what, and why.
- The subtitle must explain how/why the chart supports the claim in simple human language. Use the fewest words that properly explain the mechanism; do not cut the sentence so short that the reasoning becomes vague. It should name the actual mechanism or comparison: for example, "Diesel still matters because only 11% of electricity came from renewables in the latest data, so higher imported fuel prices can still flow into power costs."
- If the chart cannot support a plain-language "why this matters" sentence, do not include the chart.

## Deck Rules

- Output one compact sourced PowerPoint `.pptx` deck. Do not emit companion Word, Markdown, PDF, runtime artifacts, JSON plans, or debug files for a report run.
- Use an executive summary slide first, then one chart per evidence slide.
- Charts must be native editable PowerPoint charts, not chart screenshots or pasted chart images.
- Do not use line charts with missing periods or categories unless the gaps have been resolved before charting. PowerPoint can make sparse series look like zeroes; use complete line series, split the chart, or use a before/latest column comparison.
- Executive summary slide: concise, directly answering the question.
- Each evidence slide should follow:

```text
Specific narrative claim title
Plain-English how/why subtitle explaining what the chart proves and why it matters; it may be longer when needed for the reasoning to be clear
Figure N. Metric, unit, period, geography, and caveat.
[Editable native PowerPoint chart]
Notes: human-readable assumptions, caveats, source quirks, comparability issues, exclusions, or judgement calls relevant to the chart.
Source: dataset/source name and URL.
```

- Keep slide prose concise, but do not sacrifice meaning. Use the least possible words that still explain the reasoning properly.
- Make important claims traceable to a chart, retrieved data, or cited source.
- Write for a non-specialist reader. Avoid jargon where normal words work. Explain mechanisms directly: prices rise, imports cost more, households pay more, exporters earn less, government has less room, or uncertainty delays investment.
- Each evidence slide needs two distinct jobs: the title states the conclusion; the subtitle explains how the data shows it. If the reader would still ask "why?", the subtitle is too thin.
- Use chart notes for analyst caveats, not mechanical provenance. Include notes when the chart uses imperfect comparisons, mixed years, proxy definitions, exclusions, derived calculations, source caveats, or assumptions made to keep the analysis useful.
- The analyst/model writes chart notes after inspecting the data. Do not rely on generic fallback notes.
- Every chart must make its period obvious. If the latest data year is not recent for the question, the note must say why the chart is still included.
- Explain technical terms in plain English.
- If evidence is incomplete or stale, say so plainly and avoid confident current claims.
- After writing the deck, inspect the saved `.pptx` package or render previews. Confirm chart slides contain native chart parts and embedded workbooks, no pasted chart images, and no obvious text/chart collisions.

## MCP Tools

- `search_pdh_catalog`: run one or several FTS shortlist queries over the full live PDH dataflow catalogue. Results are unranked candidates; default shortlist length is 20 per query; the AI chooses.
- `get_pdh_metadata`: inspect dimensions and codelists.
- `get_pdh_codelist`: find valid codes.
- `retrieve_pdh_data`: retrieve a data slice and return rows directly.
- `inspect_pdh_data`: summarize retrieved data.
- `narrow_pdh_data`: filter retrieved rows for analysis.
