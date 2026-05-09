from __future__ import annotations

import csv
import json
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from .countries import country_code

BASE_URL = "https://stats-sdmx-disseminate.pacificdata.org/rest"
AGENCY_ID = "SPC"
CACHE_DIR = Path("runtime/cache")
DATAFLOWS_CACHE_PATH = CACHE_DIR / "dataflows.xml"
DATAFLOWS_CACHE_TTL_SECONDS = 86400
_DATAFLOW_CACHE: list[dict[str, Any]] | None = None
_FTS_CONN: sqlite3.Connection | None = None

NS = {
    "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}


class PDHError(RuntimeError):
    pass


def csv_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(text.splitlines()))


def inspect_rows(rows: list[dict[str, Any]], max_values: int = 12) -> dict[str, Any]:
    columns = list(rows[0].keys()) if rows else []
    summary: dict[str, Any] = {"row_count": len(rows), "columns": columns, "sample_rows": rows[:5]}
    for field in ("TIME_PERIOD", "GEO_PICT", "INDICATOR", "COMMODITY", "FREQ", "UNIT_MEASURE"):
        values = sorted({str(row.get(field, "")) for row in rows if str(row.get(field, "")).strip()})
        if values:
            summary[field.lower()] = values[:max_values]
            if len(values) > max_values:
                summary[f"{field.lower()}_truncated"] = len(values) - max_values
    numeric = []
    for row in rows:
        value = str(row.get("OBS_VALUE", "")).strip()
        if not value:
            continue
        try:
            numeric.append(float(value))
        except ValueError:
            pass
    if numeric:
        summary["obs_value_min"] = min(numeric)
        summary["obs_value_max"] = max(numeric)
    periods = [str(row.get("TIME_PERIOD", "")).strip() for row in rows if str(row.get("TIME_PERIOD", "")).strip()]
    if periods:
        summary["period_start"] = min(periods)
        summary["period_end"] = max(periods)
    return summary


@dataclass
class Dataflow:
    id: str
    name: str
    version: str
    annotations: dict[str, list[str]]


def _text(element: ET.Element | None) -> str:
    return "".join(element.itertext()).strip() if element is not None else ""


def _first_name(element: ET.Element) -> str:
    names = element.findall("common:Name", NS)
    if not names:
        return ""
    for name in names:
        if name.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
            return _text(name)
    return _text(names[0])


def _tag_ends(element: ET.Element, suffix: str) -> bool:
    return element.tag.rsplit("}", 1)[-1] == suffix


def _get(url: str, *, timeout: int = 60) -> requests.Response:
    response = requests.get(
        url,
        headers={"User-Agent": "pacific-data-research/0.1"},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise PDHError(f"PDH request failed {response.status_code}: {response.text[:300]} ({url})")
    return response


def _dataflows_xml(refresh: bool = False) -> str:
    url = f"{BASE_URL}/dataflow/{AGENCY_ID}/all/latest?detail=allstubs"
    if (
        not refresh
        and DATAFLOWS_CACHE_PATH.exists()
        and time.time() - DATAFLOWS_CACHE_PATH.stat().st_mtime < DATAFLOWS_CACHE_TTL_SECONDS
    ):
        return DATAFLOWS_CACHE_PATH.read_text(encoding="utf-8")
    text = _get(url).text
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATAFLOWS_CACHE_PATH.write_text(text, encoding="utf-8")
    return text


def _parse_annotations(element: ET.Element) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for annotation in element.findall(".//common:Annotation", NS):
        atype = _text(annotation.find("common:AnnotationType", NS)) or "annotation"
        values = []
        title = _text(annotation.find("common:AnnotationTitle", NS))
        body = _text(annotation.find("common:AnnotationText", NS))
        if title:
            values.append(title)
        if body:
            values.append(body)
        if values:
            result.setdefault(atype, []).extend(values)
    return result


def list_dataflows(refresh: bool = False) -> list[dict[str, Any]]:
    global _DATAFLOW_CACHE
    if _DATAFLOW_CACHE is not None and not refresh:
        return [dict(flow) for flow in _DATAFLOW_CACHE]
    text = _dataflows_xml(refresh=refresh)
    root = ET.fromstring(text.encode("utf-8"))
    flows = []
    for element in root.findall(".//structure:Dataflow", NS):
        flow = Dataflow(
            id=str(element.attrib.get("id", "")),
            name=_first_name(element),
            version=str(element.attrib.get("version", "latest")),
            annotations=_parse_annotations(element),
        )
        if flow.id:
            flows.append(
                {
                    "id": flow.id,
                    "name": flow.name,
                    "version": flow.version,
                    "annotations": flow.annotations,
                }
            )
    _DATAFLOW_CACHE = flows
    return [dict(flow) for flow in flows]


STOPWORDS = {
    "about",
    "across",
    "and",
    "country",
    "data",
    "for",
    "from",
    "latest",
    "over",
    "show",
    "table",
    "tables",
    "the",
    "time",
    "trend",
    "using",
    "what",
    "where",
    "which",
    "with",
}


def _normalize_tokens(query: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9_+-]+", str(query or "").lower())
    return [token for token in raw_tokens if len(token) > 1 and token not in STOPWORDS]


def _catalog_query_text(query: str) -> str:
    tokens = set(_normalize_tokens(query))
    expansions = []
    if tokens & {"electricity", "renewable", "renewables", "generation", "fuel", "power", "tariff"}:
        expansions.append("energy")
    if tokens & {"school", "teacher", "literacy", "enrolment", "enrollment"}:
        expansions.append("education")
    if tokens & {"hospital", "disease", "mortality", "clinic"}:
        expansions.append("health")
    if tokens & {"imports", "exports", "import", "export", "trade"}:
        expansions.append("trade")
    return " ".join([query, *expansions]).strip()


def _fts_match_query(query: str, operator: str) -> str:
    tokens = _normalize_tokens(query)
    if not tokens:
        return ""
    return f" {operator} ".join(f'"{token}"*' for token in tokens)


def _flow_search_text(flow: dict[str, Any]) -> str:
    annotation_text = " ".join(v for values in (flow.get("annotations") or {}).values() for v in values)
    return " ".join([str(flow.get("id", "")), str(flow.get("name", "")), annotation_text])


def ensure_dataflow_fts(refresh: bool = False) -> None:
    global _FTS_CONN
    if _FTS_CONN is not None and not refresh:
        return
    flows = list_dataflows(refresh=refresh)
    if _FTS_CONN is not None:
        _FTS_CONN.close()
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE dataflow_fts USING fts5(
                id,
                name,
                version,
                annotations,
                search_text
            )
            """
        )
        conn.executemany(
            "INSERT INTO dataflow_fts(id, name, version, annotations, search_text) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    str(flow.get("id", "")),
                    str(flow.get("name", "")),
                    str(flow.get("version", "")),
                    json.dumps(flow.get("annotations") or {}, ensure_ascii=False),
                    _flow_search_text(flow),
                )
                for flow in flows
            ],
        )
        conn.commit()
        _FTS_CONN = conn
    finally:
        if _FTS_CONN is not conn:
            conn.close()


def _search_dataflows_fts(query: str, limit: int) -> list[dict[str, Any]]:
    ensure_dataflow_fts(False)
    catalog_query = _catalog_query_text(query)
    strict_query = _fts_match_query(catalog_query, "AND")
    relaxed_query = _fts_match_query(catalog_query, "OR")
    rows: list[sqlite3.Row] = []
    seen: set[str] = set()
    conn = _FTS_CONN
    if conn is None:
        raise PDHError("PDH catalogue FTS index was not initialized")
    conn.row_factory = sqlite3.Row
    for match_query in [strict_query, relaxed_query]:
        if not match_query:
            continue
        for row in conn.execute(
            """
            SELECT id, name, version, annotations, search_text, bm25(dataflow_fts, 4.0, 5.0, 1.0, 1.5, 2.5) AS rank_score
            FROM dataflow_fts
            WHERE dataflow_fts MATCH ?
            ORDER BY rank_score, id
            LIMIT ?
            """,
            (match_query, max(limit * 2, limit)),
        ).fetchall():
            flow_id = str(row["id"] or "")
            if flow_id in seen:
                continue
            seen.add(flow_id)
            rows.append(row)
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break

    # FTS selects the candidate pool. Return a stable unranked shortlist so the
    # analyst/model chooses datasets from the live catalog metadata, not from a
    # search score.
    stable_rows = sorted(rows, key=lambda row: (str(row["name"] or "").lower(), str(row["id"] or "").lower()))
    matches = []
    for row in stable_rows:
        try:
            annotations = json.loads(str(row["annotations"] or "{}"))
        except Exception:
            annotations = {}
        matches.append(
            {
                "id": str(row["id"] or ""),
                "name": str(row["name"] or ""),
                "version": str(row["version"] or "latest"),
                "annotations": annotations,
                "catalog_query": catalog_query,
            }
        )
    return matches


def _score(text: str, terms: list[str]) -> int:
    normalized = re.sub(r"[^a-z0-9_]+", " ", text.lower())
    score = 0
    for term in terms:
        t = term.lower().strip()
        if not t:
            continue
        if t in normalized:
            score += 5
        score += sum(1 for token in t.split() if token and token in normalized)
    return score


def search_dataflows(query: str, country: str | None = None, limit: int = 20) -> dict[str, Any]:
    cc = country_code(country)
    candidates = _search_dataflows_fts(query, limit=max(1, min(limit, 40)))
    return {"query": query, "country": country, "country_code": cc, "matches": candidates[:limit]}


def search_dataflow_shortlists(queries: list[str], country: str | None = None, limit: int = 20) -> dict[str, Any]:
    clean_queries = [query.strip() for query in queries if str(query or "").strip()]
    return {
        "country": country,
        "country_code": country_code(country),
        "shortlists": [search_dataflows(query=query, country=country, limit=limit) for query in clean_queries],
    }


def get_dataflow_metadata(dataflow_id: str, version: str = "latest") -> dict[str, Any]:
    dataflow_id = dataflow_id.strip()
    url = f"{BASE_URL}/dataflow/{AGENCY_ID}/{dataflow_id}/{version}?references=children&detail=full"
    root = ET.fromstring(_get(url).content)
    flow_el = root.find(".//structure:Dataflow", NS)
    dsd_el = root.find(".//structure:DataStructure", NS)
    if flow_el is None:
        raise PDHError(f"Dataflow not found: {dataflow_id}")
    dimensions = []
    if dsd_el is not None:
        dimension_elements = dsd_el.findall(".//structure:DimensionList/structure:Dimension", NS)
        dimension_elements += dsd_el.findall(".//structure:DimensionList/structure:TimeDimension", NS)
        for dim in dimension_elements:
            codelist = None
            for child in dim.iter():
                if _tag_ends(child, "Ref") and child.attrib.get("class") == "Codelist":
                    codelist = {
                        "id": child.attrib.get("id"),
                        "version": child.attrib.get("version"),
                        "agency_id": child.attrib.get("agencyID"),
                    }
                    break
            dimensions.append(
                {
                    "id": dim.attrib.get("id"),
                    "position": int(dim.attrib.get("position", "999")) if dim.attrib.get("position") else None,
                    "codelist": codelist,
                }
            )
    dimensions.sort(key=lambda item: item.get("position") or 999)
    return {
        "id": dataflow_id,
        "name": _first_name(flow_el),
        "version": flow_el.attrib.get("version", version),
        "annotations": _parse_annotations(flow_el),
        "datastructure": {
            "id": dsd_el.attrib.get("id") if dsd_el is not None else None,
            "version": dsd_el.attrib.get("version") if dsd_el is not None else None,
            "name": _first_name(dsd_el) if dsd_el is not None else None,
        },
        "dimensions": dimensions,
        "source_url": url,
    }


def get_codelist_codes(codelist_id: str, version: str = "latest", search: str | None = None, limit: int = 50) -> dict[str, Any]:
    url = f"{BASE_URL}/codelist/{AGENCY_ID}/{codelist_id}/{version}?detail=full"
    root = ET.fromstring(_get(url).content)
    codes = []
    terms = [search or ""]
    for code in root.findall(".//structure:Code", NS):
        item = {"id": code.attrib.get("id"), "name": _first_name(code)}
        if not search or _score(f"{item['id']} {item['name']}", terms):
            codes.append(item)
    return {"codelist_id": codelist_id, "version": version, "codes": codes[:limit], "count": len(codes), "source_url": url}


def build_key(metadata: dict[str, Any], filters: dict[str, Any] | None = None, country: str | None = None) -> str:
    filters = {str(k): v for k, v in (filters or {}).items()}
    cc = country_code(country)
    parts = []
    for dim in metadata.get("dimensions", []):
        dim_id = str(dim.get("id") or "")
        if dim_id == "TIME_PERIOD":
            continue
        value = filters.get(dim_id, "")
        if dim_id in {"GEO_PICT", "GEO", "REF_AREA"} and cc and not value:
            value = cc
        if isinstance(value, list):
            value = "+".join(str(item) for item in value if str(item).strip())
        parts.append(str(value).strip())
    return ".".join(parts)


def retrieve_data(
    dataflow_id: str,
    key: str | None = None,
    filters: dict[str, Any] | None = None,
    country: str | None = None,
    start_period: str | None = None,
    end_period: str | None = None,
    version: str = "latest",
) -> dict[str, Any]:
    metadata = get_dataflow_metadata(dataflow_id, version=version)
    resolved_version = str(metadata.get("version") or version)
    resolved_key = key if key is not None else build_key(metadata, filters=filters, country=country)
    params = {"dimensionAtObservation": "AllDimensions", "format": "csvfile"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    url = f"{BASE_URL}/data/{AGENCY_ID},{dataflow_id},{resolved_version}/{resolved_key}?{urlencode(params)}"
    response = _get(url, timeout=90)
    rows = csv_rows(response.text)
    if not rows:
        raise PDHError(f"No rows returned for {dataflow_id} key={resolved_key}")
    return {
        "kind": "pdh_csv",
        "dataflow_id": dataflow_id,
        "dataflow_name": metadata.get("name"),
        "version": resolved_version,
        "key": resolved_key,
        "filters": filters or {},
        "country": country,
        "start_period": start_period,
        "end_period": end_period,
        "retrieval_url": url,
        "csv": response.text,
        "rows": rows,
        "summary": inspect_rows(rows),
    }


def inspect_data(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        text = str(payload.get("csv") or "")
        rows = csv_rows(text) if text else []
    return {
        "kind": payload.get("kind"),
        "dataflow_id": payload.get("dataflow_id"),
        "dataflow_name": payload.get("dataflow_name"),
        "retrieval_url": payload.get("retrieval_url"),
        "summary": inspect_rows(rows),
    }


def filter_rows(rows: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    normalized = {str(k): {str(x) for x in v} if isinstance(v, list) else {str(v)} for k, v in filters.items()}
    for row in rows:
        keep = True
        for key, allowed in normalized.items():
            if str(row.get(key, "")) not in allowed:
                keep = False
                break
        if keep:
            result.append(row)
    return result
