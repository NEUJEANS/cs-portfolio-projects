from __future__ import annotations

import argparse
import csv
import json
import math
import re
import textwrap
from collections import Counter, defaultdict
from html import escape
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>[^ ]+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)'  # common log tail
    r'(?: "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)")?'  # combined log tail
    r'(?P<extra>(?: .+)?)$'  # optional latency token or named timing fields
)

COMMON_LOG_TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"
NAMED_FIELD_START_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
FIELD_NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
NAMED_TIMING_SPLIT_RE = re.compile(r'\s*[,:]\s*')
STATUS_CODE_RE = re.compile(r'^\d{3}$')
TIME_BUCKET_GRANULARITIES = ("minute", "hour")
MISSING_FACET_VALUE = "(missing)"
CARD_ANNOTATION_THEME_PRIORITIES = ("incident", "rollback", "recovery", "deploy", "note")
CARD_ANNOTATION_THEME_ALIASES = {
    "default": "note",
    "info": "note",
    "note": "note",
    "deploy": "deploy",
    "release": "deploy",
    "ship": "deploy",
    "rollback": "rollback",
    "revert": "rollback",
    "incident": "incident",
    "alert": "incident",
    "outage": "incident",
    "recovery": "recovery",
    "recover": "recovery",
    "resolved": "recovery",
}
CARD_ANNOTATION_THEMES: dict[str, dict[str, str]] = {
    "note": {
        "label": "Note",
        "marker_fill": "#334155",
        "line_stroke": "#94a3b8",
        "badge_background": "#e2e8f0",
        "badge_border": "#cbd5e1",
        "badge_text": "#0f172a",
    },
    "deploy": {
        "label": "Deploy",
        "marker_fill": "#2563eb",
        "line_stroke": "#93c5fd",
        "badge_background": "#dbeafe",
        "badge_border": "#93c5fd",
        "badge_text": "#1d4ed8",
    },
    "rollback": {
        "label": "Rollback",
        "marker_fill": "#ea580c",
        "line_stroke": "#fdba74",
        "badge_background": "#ffedd5",
        "badge_border": "#fdba74",
        "badge_text": "#c2410c",
    },
    "incident": {
        "label": "Incident",
        "marker_fill": "#dc2626",
        "line_stroke": "#fca5a5",
        "badge_background": "#fee2e2",
        "badge_border": "#fca5a5",
        "badge_text": "#b91c1c",
    },
    "recovery": {
        "label": "Recovery",
        "marker_fill": "#7c3aed",
        "line_stroke": "#c4b5fd",
        "badge_background": "#ede9fe",
        "badge_border": "#c4b5fd",
        "badge_text": "#6d28d9",
    },
}


@dataclass(frozen=True)
class ParsedLogLine:
    ip: str
    timestamp: datetime | None
    method: str
    path: str
    status: str
    bytes_sent: int
    referrer: str | None = None
    user_agent: str | None = None
    latency_ms: float | None = None
    request_time_ms: float | None = None
    upstream_response_time_ms: float | None = None
    named_fields: dict[str, str] = field(default_factory=dict)


def normalize_latency_ms(raw_latency: str | None) -> float | None:
    if raw_latency in (None, "-"):
        return None
    if "." in raw_latency:
        return round(float(raw_latency) * 1000, 3)
    return round(int(raw_latency) / 1000, 3)


def normalize_named_timing_ms(raw_timing: str | None) -> float | None:
    if raw_timing is None:
        return None

    cleaned = raw_timing.strip().strip('"').strip("'")
    if cleaned in ("", "-"):
        return None

    total_ms = 0.0
    found_value = False
    for part in NAMED_TIMING_SPLIT_RE.split(cleaned):
        item = part.strip()
        if item in ("", "-"):
            continue
        try:
            total_ms += float(item) * 1000
        except ValueError:
            return None
        found_value = True

    if not found_value:
        return None
    return round(total_ms, 3)


def parse_log_timestamp(raw_timestamp: str | None) -> datetime | None:
    if raw_timestamp in (None, ""):
        return None
    try:
        return datetime.strptime(raw_timestamp, COMMON_LOG_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def parse_cli_datetime(raw_value: str) -> datetime | None:
    cleaned = raw_value.strip()
    if not cleaned:
        return None

    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    return parse_log_timestamp(cleaned)


def format_datetime_for_output(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def build_time_window_metadata(
    window_start: datetime | None,
    window_end: datetime | None,
    matched_requests: int,
    excluded_requests: int,
) -> dict[str, str | int] | None:
    if window_start is None and window_end is None:
        return None
    return {
        "start": format_datetime_for_output(window_start),
        "end": format_datetime_for_output(window_end),
        "matched_requests": matched_requests,
        "excluded_requests": excluded_requests,
    }


def get_time_bucket_delta(granularity: str) -> timedelta:
    if granularity == "hour":
        return timedelta(hours=1)
    return timedelta(minutes=1)


def bucket_timestamp(timestamp: datetime, granularity: str) -> datetime:
    normalized = timestamp.astimezone(timezone.utc)
    if granularity == "hour":
        return normalized.replace(minute=0, second=0, microsecond=0)
    return normalized.replace(second=0, microsecond=0)


def build_time_bucket_metadata(
    granularity: str | None,
    bucket_count: int,
) -> dict[str, str | int] | None:
    if granularity is None:
        return None
    return {
        "granularity": granularity,
        "bucket_count": bucket_count,
    }


def normalize_facet_fields(facet_fields: Iterable[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_name in facet_fields or []:
        cleaned = raw_name.strip()
        if not cleaned or cleaned in seen:
            continue
        normalized.append(cleaned)
        seen.add(cleaned)
    return normalized


def build_faceting_metadata(facet_fields: list[str]) -> dict[str, object] | None:
    if not facet_fields:
        return None
    return {
        "fields": facet_fields,
        "missing_value": MISSING_FACET_VALUE,
    }


def resolve_named_field_value(named_fields: dict[str, str], field_name: str) -> str:
    raw_value = named_fields.get(field_name)
    if raw_value is None:
        return MISSING_FACET_VALUE
    cleaned = raw_value.strip()
    if not cleaned:
        return MISSING_FACET_VALUE
    return cleaned


def build_facet_values(named_fields: dict[str, str], facet_fields: list[str]) -> tuple[str, ...]:
    return tuple(resolve_named_field_value(named_fields, field_name) for field_name in facet_fields)


def build_facet_map(facet_fields: list[str], facet_values: tuple[str, ...]) -> dict[str, str]:
    return {field_name: value for field_name, value in zip(facet_fields, facet_values, strict=True)}


def subtract_optional_metric(right: float | int | None, left: float | int | None) -> float | int | None:
    if right is None or left is None:
        return None
    difference = float(right) - float(left)
    if difference.is_integer():
        return int(difference)
    return round(difference, 3)


def build_empty_time_bucket_row(bucket_start: str, granularity: str | None) -> dict[str, object]:
    bucket_end = ""
    if granularity is not None:
        bucket_end = format_datetime_for_output(
            parse_bucket_datetime(bucket_start) + get_time_bucket_delta(granularity)
        )
    return {
        "bucket_start": bucket_start,
        "bucket_end": bucket_end,
        "request_count": 0,
        "error_count": 0,
        "error_rate_pct": 0.0,
        "top_path": None,
        "top_path_count": 0,
        "latency_sample_count": 0,
        "average_latency_ms": None,
        "p95_latency_ms": None,
        "max_latency_ms": None,
        "upstream_latency_sample_count": 0,
        "average_upstream_latency_ms": None,
        "p95_upstream_latency_ms": None,
        "max_upstream_latency_ms": None,
    }


def summarize_release_review_metrics(result: dict) -> dict[str, object]:
    latency_summary = result["latency_summary"] or {}
    upstream_latency_summary = result["upstream_latency_summary"] or {}
    top_path = None
    top_path_count = 0
    if result["top_paths"]:
        top_path, top_path_count = result["top_paths"][0]
    error_count = sum(
        count
        for status, count in result["status_counts"].items()
        if status.startswith(("4", "5"))
    )
    total_requests = result["total_requests"]
    return {
        "request_count": total_requests,
        "error_count": error_count,
        "error_rate_pct": round((error_count / total_requests) * 100, 3)
        if total_requests
        else 0.0,
        "average_latency_ms": latency_summary.get("average_ms"),
        "p95_latency_ms": latency_summary.get("p95_ms"),
        "max_latency_ms": latency_summary.get("max_ms"),
        "average_upstream_latency_ms": upstream_latency_summary.get("average_ms"),
        "p95_upstream_latency_ms": upstream_latency_summary.get("p95_ms"),
        "max_upstream_latency_ms": upstream_latency_summary.get("max_ms"),
        "top_path": top_path,
        "top_path_count": top_path_count,
    }


def build_facet_comparison_bucket_rows(
    left_result: dict,
    right_result: dict,
    *,
    granularity: str | None,
) -> list[dict[str, object]]:
    if granularity is None:
        return []

    left_rows = {row["bucket_start"]: row for row in left_result["time_buckets"]}
    right_rows = {row["bucket_start"]: row for row in right_result["time_buckets"]}
    all_bucket_starts = sorted({*left_rows.keys(), *right_rows.keys()})
    rows: list[dict[str, object]] = []
    for bucket_start in all_bucket_starts:
        left_row = left_rows.get(bucket_start) or build_empty_time_bucket_row(bucket_start, granularity)
        right_row = right_rows.get(bucket_start) or build_empty_time_bucket_row(bucket_start, granularity)
        bucket_end = left_row["bucket_end"] or right_row["bucket_end"]
        rows.append(
            {
                "bucket_start": bucket_start,
                "bucket_end": bucket_end,
                "left_request_count": left_row["request_count"],
                "right_request_count": right_row["request_count"],
                "request_count_delta": right_row["request_count"] - left_row["request_count"],
                "left_error_count": left_row["error_count"],
                "right_error_count": right_row["error_count"],
                "error_count_delta": right_row["error_count"] - left_row["error_count"],
                "left_error_rate_pct": left_row["error_rate_pct"],
                "right_error_rate_pct": right_row["error_rate_pct"],
                "error_rate_pct_delta": subtract_optional_metric(
                    right_row["error_rate_pct"],
                    left_row["error_rate_pct"],
                ),
                "left_average_latency_ms": left_row["average_latency_ms"],
                "right_average_latency_ms": right_row["average_latency_ms"],
                "average_latency_ms_delta": subtract_optional_metric(
                    right_row["average_latency_ms"],
                    left_row["average_latency_ms"],
                ),
                "left_p95_latency_ms": left_row["p95_latency_ms"],
                "right_p95_latency_ms": right_row["p95_latency_ms"],
                "p95_latency_ms_delta": subtract_optional_metric(
                    right_row["p95_latency_ms"],
                    left_row["p95_latency_ms"],
                ),
                "left_max_latency_ms": left_row["max_latency_ms"],
                "right_max_latency_ms": right_row["max_latency_ms"],
                "max_latency_ms_delta": subtract_optional_metric(
                    right_row["max_latency_ms"],
                    left_row["max_latency_ms"],
                ),
                "left_average_upstream_latency_ms": left_row["average_upstream_latency_ms"],
                "right_average_upstream_latency_ms": right_row["average_upstream_latency_ms"],
                "average_upstream_latency_ms_delta": subtract_optional_metric(
                    right_row["average_upstream_latency_ms"],
                    left_row["average_upstream_latency_ms"],
                ),
                "left_p95_upstream_latency_ms": left_row["p95_upstream_latency_ms"],
                "right_p95_upstream_latency_ms": right_row["p95_upstream_latency_ms"],
                "p95_upstream_latency_ms_delta": subtract_optional_metric(
                    right_row["p95_upstream_latency_ms"],
                    left_row["p95_upstream_latency_ms"],
                ),
                "left_max_upstream_latency_ms": left_row["max_upstream_latency_ms"],
                "right_max_upstream_latency_ms": right_row["max_upstream_latency_ms"],
                "max_upstream_latency_ms_delta": subtract_optional_metric(
                    right_row["max_upstream_latency_ms"],
                    left_row["max_upstream_latency_ms"],
                ),
                "left_top_path": left_row["top_path"],
                "right_top_path": right_row["top_path"],
                "left_top_path_count": left_row["top_path_count"],
                "right_top_path_count": right_row["top_path_count"],
            }
        )
    return rows


def format_facet_label(facets: dict[str, str]) -> str:
    return ", ".join(f"{field_name}={value}" for field_name, value in facets.items())


def summarize_time_buckets(
    bucket_rows: dict[datetime, dict[str, object]],
    granularity: str | None,
) -> list[dict]:
    if granularity is None:
        return []

    rows: list[dict] = []
    bucket_delta = get_time_bucket_delta(granularity)
    for bucket_start in sorted(bucket_rows):
        bucket = bucket_rows[bucket_start]
        request_count = int(bucket["request_count"])
        error_count = int(bucket["error_count"])
        path_counts = bucket["path_counts"]
        request_summary = summarize_latencies(bucket["latencies_ms"])
        upstream_summary = summarize_latencies(bucket["upstream_latencies_ms"])
        top_path = None
        top_path_count = 0
        if path_counts:
            top_path, top_path_count = path_counts.most_common(1)[0]

        rows.append(
            {
                "bucket_start": format_datetime_for_output(bucket_start),
                "bucket_end": format_datetime_for_output(bucket_start + bucket_delta),
                "request_count": request_count,
                "error_count": error_count,
                "error_rate_pct": round((error_count / request_count) * 100, 3)
                if request_count
                else 0.0,
                "top_path": top_path,
                "top_path_count": top_path_count,
                "latency_sample_count": request_summary["count"] if request_summary else 0,
                "average_latency_ms": request_summary["average_ms"] if request_summary else None,
                "p95_latency_ms": request_summary["p95_ms"] if request_summary else None,
                "max_latency_ms": request_summary["max_ms"] if request_summary else None,
                "upstream_latency_sample_count": upstream_summary["count"]
                if upstream_summary
                else 0,
                "average_upstream_latency_ms": upstream_summary["average_ms"]
                if upstream_summary
                else None,
                "p95_upstream_latency_ms": upstream_summary["p95_ms"] if upstream_summary else None,
                "max_upstream_latency_ms": upstream_summary["max_ms"] if upstream_summary else None,
            }
        )
    return rows


def summarize_time_bucket_facets(
    bucket_rows: dict[tuple[datetime, tuple[str, ...]], dict[str, object]],
    granularity: str | None,
    facet_fields: list[str],
) -> list[dict]:
    if granularity is None or not facet_fields:
        return []

    rows: list[dict] = []
    bucket_delta = get_time_bucket_delta(granularity)
    for bucket_start, facet_values in sorted(bucket_rows, key=lambda item: (item[0], item[1])):
        bucket = bucket_rows[(bucket_start, facet_values)]
        request_count = int(bucket["request_count"])
        error_count = int(bucket["error_count"])
        path_counts = bucket["path_counts"]
        request_summary = summarize_latencies(bucket["latencies_ms"])
        upstream_summary = summarize_latencies(bucket["upstream_latencies_ms"])
        top_path = None
        top_path_count = 0
        if path_counts:
            top_path, top_path_count = path_counts.most_common(1)[0]
        facets = build_facet_map(facet_fields, facet_values)
        rows.append(
            {
                "bucket_start": format_datetime_for_output(bucket_start),
                "bucket_end": format_datetime_for_output(bucket_start + bucket_delta),
                "facets": facets,
                "facet_label": format_facet_label(facets),
                "request_count": request_count,
                "error_count": error_count,
                "error_rate_pct": round((error_count / request_count) * 100, 3)
                if request_count
                else 0.0,
                "top_path": top_path,
                "top_path_count": top_path_count,
                "latency_sample_count": request_summary["count"] if request_summary else 0,
                "average_latency_ms": request_summary["average_ms"] if request_summary else None,
                "p95_latency_ms": request_summary["p95_ms"] if request_summary else None,
                "max_latency_ms": request_summary["max_ms"] if request_summary else None,
                "upstream_latency_sample_count": upstream_summary["count"]
                if upstream_summary
                else 0,
                "average_upstream_latency_ms": upstream_summary["average_ms"]
                if upstream_summary
                else None,
                "p95_upstream_latency_ms": upstream_summary["p95_ms"] if upstream_summary else None,
                "max_upstream_latency_ms": upstream_summary["max_ms"] if upstream_summary else None,
            }
        )
    return rows


def parse_extra_fields(extra: str | None) -> tuple[str | None, dict[str, str]]:
    if extra is None:
        return None, {}

    tokens = extra.strip().split()
    if not tokens:
        return None, {}

    unnamed_tokens: list[str] = []
    named_fields: dict[str, str] = {}
    current_key: str | None = None
    current_parts: list[str] = []

    def flush_current() -> None:
        nonlocal current_key, current_parts
        if current_key is None:
            return
        named_fields[current_key] = " ".join(current_parts).strip()
        current_key = None
        current_parts = []

    for token in tokens:
        if NAMED_FIELD_START_RE.match(token):
            flush_current()
            current_key, value = token.split("=", 1)
            current_parts = [value]
            continue

        if current_key is not None:
            current_parts.append(token)
        else:
            unnamed_tokens.append(token)

    flush_current()
    unnamed_latency = unnamed_tokens[0] if len(unnamed_tokens) == 1 else None
    return unnamed_latency, named_fields


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    index = (len(ordered) - 1) * ratio
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(ordered[lower], 3)

    lower_value = ordered[lower]
    upper_value = ordered[upper]
    interpolated = lower_value + ((upper_value - lower_value) * (index - lower))
    return round(interpolated, 3)


def summarize_latencies(latencies: list[float]) -> dict | None:
    if not latencies:
        return None

    return {
        "count": len(latencies),
        "average_ms": round(sum(latencies) / len(latencies), 3),
        "p50_ms": percentile(latencies, 0.50),
        "p95_ms": percentile(latencies, 0.95),
        "p99_ms": percentile(latencies, 0.99),
        "max_ms": round(max(latencies), 3),
    }


def summarize_path_latencies(path_latencies: dict[str, list[float]], limit: int) -> list[dict]:
    rows = []
    for path, latencies in path_latencies.items():
        summary = summarize_latencies(latencies)
        if summary is None:
            continue
        rows.append({"path": path, **summary})

    rows.sort(key=lambda row: (-row["average_ms"], -row["count"], row["path"]))
    return rows[:limit]


def summarize_path_latencies_by_facet(
    path_latencies: dict[tuple[str, tuple[str, ...]], list[float]],
    facet_fields: list[str],
    limit: int,
) -> list[dict]:
    rows = []
    for (path, facet_values), latencies in path_latencies.items():
        summary = summarize_latencies(latencies)
        if summary is None:
            continue
        facets = build_facet_map(facet_fields, facet_values)
        rows.append(
            {
                "path": path,
                "facets": facets,
                "facet_label": format_facet_label(facets),
                **summary,
            }
        )

    rows.sort(
        key=lambda row: (
            -row["average_ms"],
            -row["count"],
            row["path"],
            row["facet_label"],
        )
    )
    return rows[:limit]


def normalize_hotspot_filters(
    statuses: Iterable[str] | None = None,
    methods: Iterable[str] | None = None,
) -> dict[str, list[str]] | None:
    normalized_statuses = sorted({status.strip() for status in statuses or [] if status.strip()})
    normalized_methods = sorted(
        {method.strip().upper() for method in methods or [] if method.strip()}
    )
    if not normalized_statuses and not normalized_methods:
        return None
    return {
        "statuses": normalized_statuses,
        "methods": normalized_methods,
    }


def matches_hotspot_filters(
    parsed: ParsedLogLine,
    hotspot_filters: dict[str, list[str]] | None,
) -> bool:
    if hotspot_filters is None:
        return True

    statuses = hotspot_filters["statuses"]
    methods = hotspot_filters["methods"]
    if statuses and parsed.status not in statuses:
        return False
    if methods and parsed.method not in methods:
        return False
    return True


def matches_time_window(
    parsed_timestamp: datetime | None,
    window_start: datetime | None,
    window_end: datetime | None,
) -> bool:
    if window_start is None and window_end is None:
        return True
    if parsed_timestamp is None:
        return False
    if window_start is not None and parsed_timestamp < window_start:
        return False
    if window_end is not None and parsed_timestamp > window_end:
        return False
    return True


def format_hotspot_heading(label: str, hotspot_filters: dict[str, list[str]] | None) -> str:
    if hotspot_filters is None:
        return label

    parts: list[str] = []
    if hotspot_filters["statuses"]:
        parts.append(f"status={','.join(hotspot_filters['statuses'])}")
    if hotspot_filters["methods"]:
        parts.append(f"method={','.join(hotspot_filters['methods'])}")
    return f"{label} (filters: {'; '.join(parts)})"


def format_faceting_heading(label: str, faceting: dict[str, object] | None) -> str:
    if faceting is None:
        return label
    fields = faceting["fields"]
    return f"{label} (facets: {', '.join(fields)})"


def format_bucket_latency_summary(
    sample_count: int,
    average_ms: float | None,
    p95_ms: float | None,
    max_ms: float | None,
) -> str:
    if sample_count == 0:
        return "samples=0"
    return (
        f"samples={sample_count}, avg={average_ms}, p95={p95_ms}, max={max_ms}"
    )


def write_text_output(destination: str | Path, content: str) -> None:
    destination_path = ensure_parent_directory(destination)
    destination_path.write_text(content, encoding="utf-8")


def format_card_metric_value(
    value: float | int | None,
    *,
    suffix: str = "",
    decimals: int = 1,
) -> str:
    if value is None:
        return "n/a"
    numeric = float(value)
    if numeric.is_integer():
        return f"{int(numeric)}{suffix}"
    return f"{numeric:.{decimals}f}{suffix}"


def format_signed_card_metric_value(
    value: float | int | None,
    *,
    suffix: str = "",
    decimals: int = 1,
) -> str:
    if value is None:
        return "n/a"
    prefix = "+" if float(value) > 0 else ""
    return prefix + format_card_metric_value(value, suffix=suffix, decimals=decimals)


def parse_bucket_datetime(raw_value: str) -> datetime:
    return datetime.fromisoformat(raw_value).astimezone(timezone.utc)


def format_bucket_axis_label(raw_value: str) -> str:
    return parse_bucket_datetime(raw_value).strftime("%H:%M")


def format_bucket_range_label(bucket_start: str, bucket_end: str) -> str:
    start = parse_bucket_datetime(bucket_start)
    end = parse_bucket_datetime(bucket_end)
    if start.date() == end.date():
        return f"{start:%Y-%m-%d %H:%M} → {end:%H:%M} UTC"
    return f"{start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M} UTC"


def build_chart_x_positions(*, value_count: int, left: float, width: float) -> list[float]:
    if value_count <= 0:
        return []
    if value_count == 1:
        return [left + (width / 2)]
    step = width / (value_count - 1)
    return [left + (step * index) for index in range(value_count)]


def normalize_card_annotation_theme(raw_theme: str) -> str | None:
    cleaned = raw_theme.strip().lower().replace("_", "-").replace(" ", "-")
    if not cleaned:
        return None
    return CARD_ANNOTATION_THEME_ALIASES.get(cleaned)


def parse_card_annotation_label(raw_label: str) -> tuple[str, str]:
    cleaned = raw_label.strip()
    if not cleaned:
        raise ValueError("--card-annotation labels cannot be empty")
    if "|" in cleaned:
        raw_theme, possible_label = cleaned.split("|", 1)
        normalized_theme = normalize_card_annotation_theme(raw_theme)
        if normalized_theme is None:
            valid_themes = ", ".join(CARD_ANNOTATION_THEMES)
            raise ValueError(
                f"Unknown --card-annotation theme '{raw_theme.strip()}'; use one of: {valid_themes}"
            )
        label = possible_label.strip()
        if not label:
            raise ValueError("--card-annotation labels cannot be empty")
        return normalized_theme, label
    return "note", cleaned


def get_card_annotation_theme(theme_key: str | None) -> dict[str, str]:
    if theme_key in CARD_ANNOTATION_THEMES:
        return CARD_ANNOTATION_THEMES[str(theme_key)]
    return CARD_ANNOTATION_THEMES["note"]


def choose_card_annotation_theme(theme_keys: Iterable[str]) -> tuple[str, list[str]]:
    unique_keys = list(dict.fromkeys(theme_keys))
    if not unique_keys:
        return "note", ["note"]
    priority_map = {name: index for index, name in enumerate(CARD_ANNOTATION_THEME_PRIORITIES)}
    dominant = min(unique_keys, key=lambda key: priority_map.get(key, len(priority_map)))
    return dominant, unique_keys


def build_annotation_marker_chip_html(annotation: dict[str, object]) -> str:
    theme = get_card_annotation_theme(str(annotation.get("theme", "note")))
    return (
        '<span class="annotation-chip" '
        f'style="background: {theme["marker_fill"]};">{escape(str(annotation["marker"]))}</span>'
    )


def build_annotation_theme_badge_html(annotation: dict[str, object]) -> str:
    theme = get_card_annotation_theme(str(annotation.get("theme", "note")))
    theme_count = int(annotation.get("theme_count", 1))
    label = str(annotation.get("theme_label", theme["label"]))
    if theme_count > 1:
        label = f"{label} +{theme_count - 1}"
    title = "Themes: " + str(annotation.get("theme_summary", label))
    return (
        '<span class="annotation-theme" '
        f'style="background: {theme["badge_background"]}; border-color: {theme["badge_border"]}; color: {theme["badge_text"]};" '
        f'title="{escape(title, quote=True)}">{escape(label)}</span>'
    )


def normalize_card_annotations(
    raw_annotations: Iterable[str] | None,
    *,
    time_buckets: list[dict[str, object]],
) -> list[dict[str, object]]:
    raw_items = list(raw_annotations or [])
    if not raw_items:
        return []
    if not time_buckets:
        raise ValueError("--card-annotation requires at least one matched time bucket")

    bucket_ranges = [
        (
            index,
            parse_bucket_datetime(str(bucket["bucket_start"])),
            parse_bucket_datetime(str(bucket["bucket_end"])),
            bucket,
        )
        for index, bucket in enumerate(time_buckets)
    ]
    coverage_label = format_bucket_range_label(
        str(time_buckets[0]["bucket_start"]),
        str(time_buckets[-1]["bucket_end"]),
    )

    grouped_labels: dict[int, list[str]] = defaultdict(list)
    grouped_times: dict[int, list[datetime]] = defaultdict(list)
    grouped_themes: dict[int, list[str]] = defaultdict(list)
    for raw_annotation in raw_items:
        if "=" not in raw_annotation:
            raise ValueError(
                "--card-annotation must use TIMESTAMP=LABEL (or TIMESTAMP=THEME|LABEL, for example "
                "2026-04-18T09:00:30Z=deploy|Deploy started)"
            )
        raw_timestamp, raw_label = raw_annotation.split("=", 1)
        parsed_time = parse_cli_datetime(raw_timestamp.strip())
        if parsed_time is None:
            raise ValueError(
                "--card-annotation timestamps must be ISO-8601 or a common-log timestamp"
            )
        theme_key, label = parse_card_annotation_label(raw_label)

        annotation_time = parsed_time.astimezone(timezone.utc)
        matched_bucket_index: int | None = None
        for index, bucket_start, bucket_end, _bucket in bucket_ranges:
            is_last_bucket = index == len(bucket_ranges) - 1
            if bucket_start <= annotation_time < bucket_end or (
                is_last_bucket and annotation_time == bucket_end
            ):
                matched_bucket_index = index
                break
        if matched_bucket_index is None:
            raise ValueError(
                f"--card-annotation timestamp {raw_timestamp.strip()} falls outside the current "
                f"bucket coverage ({coverage_label})"
            )

        grouped_labels[matched_bucket_index].append(label)
        grouped_times[matched_bucket_index].append(annotation_time)
        grouped_themes[matched_bucket_index].append(theme_key)

    if len(grouped_labels) > 4:
        raise ValueError("--card-annotation supports at most 4 distinct bucket markers per export")

    annotations: list[dict[str, object]] = []
    for marker_index, bucket_index in enumerate(sorted(grouped_labels), start=1):
        bucket = time_buckets[bucket_index]
        event_times = sorted(grouped_times[bucket_index])
        label = " · ".join(grouped_labels[bucket_index])
        dominant_theme, unique_themes = choose_card_annotation_theme(grouped_themes[bucket_index])
        theme = get_card_annotation_theme(dominant_theme)
        theme_summary = ", ".join(
            CARD_ANNOTATION_THEMES[key]["label"] for key in unique_themes
        )
        annotations.append(
            {
                "marker": str(marker_index),
                "bucket_index": bucket_index,
                "bucket_start": str(bucket["bucket_start"]),
                "bucket_end": str(bucket["bucket_end"]),
                "axis_label": format_bucket_axis_label(str(bucket["bucket_start"])),
                "range_label": format_bucket_range_label(
                    str(bucket["bucket_start"]),
                    str(bucket["bucket_end"]),
                ),
                "event_time_label": ", ".join(dt.strftime("%H:%M:%S") for dt in event_times),
                "label": label,
                "short_label": textwrap.shorten(label, width=32, placeholder="…"),
                "theme": dominant_theme,
                "theme_label": theme["label"],
                "theme_summary": theme_summary,
                "theme_count": len(unique_themes),
            }
        )
    return annotations


def build_card_annotation_map(
    annotations: Iterable[dict[str, object]] | None,
) -> dict[str, dict[str, object]]:
    return {
        str(annotation["bucket_start"]): annotation
        for annotation in (annotations or [])
    }


def build_card_annotation_footer_lines(
    annotations: Iterable[dict[str, object]] | None,
) -> list[str]:
    items = [
        f'{annotation["marker"]}. {annotation["axis_label"]} {annotation["short_label"]} [{annotation["theme_label"]}]'
        for annotation in (annotations or [])
    ]
    if not items:
        return []
    chunk_size = 2
    return [
        "Annotations: " + " · ".join(items[index : index + chunk_size])
        for index in range(0, len(items), chunk_size)
    ]


def render_chart_annotations(
    *,
    annotations: Iterable[dict[str, object]] | None,
    chart_left: float,
    chart_top: float,
    chart_width: float,
    chart_height: float,
    marker_fill: str,
    line_stroke: str,
    value_count: int,
) -> list[str]:
    annotations_list = list(annotations or [])
    if not annotations_list or value_count <= 0:
        return []

    x_positions = build_chart_x_positions(value_count=value_count, left=chart_left, width=chart_width)
    chart_bottom = chart_top + chart_height
    parts: list[str] = []
    for annotation in annotations_list:
        bucket_index = int(annotation["bucket_index"])
        if bucket_index >= len(x_positions):
            continue
        theme = get_card_annotation_theme(str(annotation.get("theme", "note")))
        annotation_marker_fill = theme["marker_fill"] or marker_fill
        annotation_line_stroke = theme["line_stroke"] or line_stroke
        x_position = x_positions[bucket_index]
        marker_cy = chart_top + 16
        parts.extend(
            [
                f'<line x1="{x_position:.2f}" y1="{chart_top:.2f}" x2="{x_position:.2f}" y2="{chart_bottom:.2f}" stroke="{annotation_line_stroke}" stroke-width="1.6" stroke-dasharray="6 6" opacity="0.9" />',
                f'<circle cx="{x_position:.2f}" cy="{marker_cy:.2f}" r="10" fill="{annotation_marker_fill}" stroke="#ffffff" stroke-width="1.6" />',
                f'<text x="{x_position:.2f}" y="{marker_cy + 4:.2f}" font-size="11" font-weight="700" text-anchor="middle" fill="#ffffff">{escape(str(annotation["marker"]))}</text>',
            ]
        )
    return parts


def build_time_bucket_card_summary(result: dict) -> dict[str, object]:
    time_buckets = result["time_buckets"]
    time_bucketing = result["time_bucketing"] or {}
    total_requests = sum(bucket["request_count"] for bucket in time_buckets)
    total_errors = sum(bucket["error_count"] for bucket in time_buckets)
    overall_error_rate = round((total_errors / total_requests) * 100, 3) if total_requests else 0.0
    latency_weighted_total = 0.0
    latency_weighted_count = 0
    for bucket in time_buckets:
        sample_count = bucket["latency_sample_count"]
        average_latency = bucket["average_latency_ms"]
        if sample_count and average_latency is not None:
            latency_weighted_total += sample_count * average_latency
            latency_weighted_count += sample_count
    weighted_latency_average = (
        round(latency_weighted_total / latency_weighted_count, 3)
        if latency_weighted_count
        else None
    )

    busiest_bucket = max(
        time_buckets,
        key=lambda bucket: (
            bucket["request_count"],
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )
    highest_error_bucket = max(
        time_buckets,
        key=lambda bucket: (
            bucket["error_rate_pct"],
            bucket["error_count"],
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )
    slowest_bucket = max(
        (bucket for bucket in time_buckets if bucket["average_latency_ms"] is not None),
        key=lambda bucket: (
            bucket["average_latency_ms"],
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )
    if time_buckets:
        coverage_label = format_bucket_range_label(
            time_buckets[0]["bucket_start"],
            time_buckets[-1]["bucket_end"],
        )
    else:
        coverage_label = "No matched buckets"

    return {
        "bucket_count": len(time_buckets),
        "granularity": time_bucketing.get("granularity", "minute"),
        "total_requests": total_requests,
        "total_errors": total_errors,
        "overall_error_rate": overall_error_rate,
        "weighted_latency_average": weighted_latency_average,
        "coverage_label": coverage_label,
        "busiest_bucket": busiest_bucket,
        "highest_error_bucket": highest_error_bucket,
        "slowest_bucket": slowest_bucket,
    }


def build_svg_chart_points(
    values: list[float | None],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    max_scale_value: float | None = None,
) -> list[list[tuple[float, float]]]:
    present_values = [value for value in values if value is not None]
    if not present_values:
        return []

    scale_max_value = max_scale_value if max_scale_value is not None else max(present_values)
    if scale_max_value <= 0:
        scale_max_value = 1.0

    x_positions = build_chart_x_positions(value_count=len(values), left=left, width=width)

    segments: list[list[tuple[float, float]]] = []
    current_segment: list[tuple[float, float]] = []
    for x_position, value in zip(x_positions, values, strict=True):
        if value is None:
            if current_segment:
                segments.append(current_segment)
                current_segment = []
            continue
        y_position = top + height - ((value / scale_max_value) * height)
        current_segment.append((x_position, y_position))
    if current_segment:
        segments.append(current_segment)
    return segments


def render_time_bucket_chart_panel(
    *,
    title: str,
    values: list[float | None],
    bucket_labels: list[str],
    panel_left: float,
    panel_top: float,
    panel_width: float,
    panel_height: float,
    stroke_color: str,
    accent_color: str,
    summary_text: str,
    metric_suffix: str,
    annotations: Iterable[dict[str, object]] | None = None,
) -> list[str]:
    parts = [
        f'<rect x="{panel_left}" y="{panel_top}" width="{panel_width}" height="{panel_height}" rx="22" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
        f'<text x="{panel_left + 20}" y="{panel_top + 34}" font-size="18" font-weight="700" fill="#0f172a">{escape(title)}</text>',
        f'<text x="{panel_left + 20}" y="{panel_top + 58}" font-size="14" fill="#475569">{escape(summary_text)}</text>',
    ]

    chart_left = panel_left + 20
    chart_top = panel_top + 86
    chart_width = panel_width - 40
    chart_height = panel_height - 132
    chart_bottom = chart_top + chart_height
    actual_max_value = max((value for value in values if value is not None), default=0.0)
    display_max_value = actual_max_value * 1.15 if actual_max_value > 0 else 1.0

    for row in range(4):
        y_position = chart_top + (chart_height * row / 3)
        parts.append(
            f'<line x1="{chart_left}" y1="{y_position:.2f}" x2="{chart_left + chart_width}" y2="{y_position:.2f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 5" />'
        )

    parts.append(
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left + chart_width}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="1.5" />'
    )

    parts.extend(
        render_chart_annotations(
            annotations=annotations,
            chart_left=chart_left,
            chart_top=chart_top,
            chart_width=chart_width,
            chart_height=chart_height,
            marker_fill="#0f172a",
            line_stroke="#94a3b8",
            value_count=len(values),
        )
    )

    segments = build_svg_chart_points(
        values,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        max_scale_value=display_max_value,
    )
    for segment in segments:
        if len(segment) >= 2:
            parts.append(
                '<polyline fill="none" '
                f'stroke="{stroke_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
                f'points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in segment)}" />'
            )
        for x_position, y_position in segment:
            parts.append(
                f'<circle cx="{x_position:.2f}" cy="{y_position:.2f}" r="4.5" fill="{accent_color}" stroke="#ffffff" stroke-width="1.5" />'
            )

    parts.extend(
        [
            f'<text x="{chart_left}" y="{chart_bottom + 24}" font-size="12" fill="#64748b">{escape(bucket_labels[0] if bucket_labels else "")}</text>',
            f'<text x="{chart_left + chart_width}" y="{chart_bottom + 24}" font-size="12" text-anchor="end" fill="#64748b">{escape(bucket_labels[-1] if bucket_labels else "")}</text>',
            f'<text x="{chart_left}" y="{chart_top - 10}" font-size="12" fill="#64748b">max {escape(format_card_metric_value(actual_max_value, suffix=metric_suffix))}</text>',
            f'<text x="{chart_left}" y="{chart_bottom + 42}" font-size="12" fill="#64748b">0{escape(metric_suffix)}</text>',
        ]
    )
    return parts


def render_comparison_chart_panel(
    *,
    title: str,
    left_values: list[float | None],
    right_values: list[float | None],
    bucket_labels: list[str],
    panel_left: float,
    panel_top: float,
    panel_width: float,
    panel_height: float,
    left_label: str,
    right_label: str,
    left_stroke_color: str,
    right_stroke_color: str,
    left_accent_color: str,
    right_accent_color: str,
    summary_text: str,
    metric_suffix: str,
    annotations: Iterable[dict[str, object]] | None = None,
) -> list[str]:
    parts = [
        f'<rect x="{panel_left}" y="{panel_top}" width="{panel_width}" height="{panel_height}" rx="22" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
        f'<text x="{panel_left + 20}" y="{panel_top + 34}" font-size="18" font-weight="700" fill="#0f172a">{escape(title)}</text>',
        f'<text x="{panel_left + 20}" y="{panel_top + 58}" font-size="14" fill="#475569">{escape(summary_text)}</text>',
    ]

    legend_y = panel_top + 80
    legend_items = [
        (left_label, left_stroke_color, left_accent_color),
        (right_label, right_stroke_color, right_accent_color),
    ]
    for index, (label, stroke_color, accent_color) in enumerate(legend_items):
        legend_x = panel_left + 20 + (index * 128)
        parts.extend(
            [
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 18}" y2="{legend_y}" stroke="{stroke_color}" stroke-width="3" stroke-linecap="round" />',
                f'<circle cx="{legend_x + 9}" cy="{legend_y}" r="4" fill="{accent_color}" stroke="#ffffff" stroke-width="1.2" />',
                f'<text x="{legend_x + 28}" y="{legend_y + 4}" font-size="12" fill="#64748b">{escape(label)}</text>',
            ]
        )

    chart_left = panel_left + 20
    chart_top = panel_top + 104
    chart_width = panel_width - 40
    chart_height = panel_height - 150
    chart_bottom = chart_top + chart_height
    actual_max_value = max(
        [value for value in left_values if value is not None]
        + [value for value in right_values if value is not None],
        default=0.0,
    )
    display_max_value = actual_max_value * 1.15 if actual_max_value > 0 else 1.0
    has_points = any(value is not None for value in left_values + right_values)

    if not has_points:
        parts.extend(
            [
                f'<rect x="{chart_left}" y="{chart_top}" width="{chart_width}" height="{chart_height}" rx="18" fill="#fff7ed" stroke="#fed7aa" stroke-width="1.2" stroke-dasharray="6 8" />',
                f'<text x="{chart_left + (chart_width / 2):.2f}" y="{chart_top + (chart_height / 2) - 8:.2f}" font-size="15" font-weight="600" text-anchor="middle" fill="#9a3412">No aligned bucket rows</text>',
                f'<text x="{chart_left + (chart_width / 2):.2f}" y="{chart_top + (chart_height / 2) + 16:.2f}" font-size="12" text-anchor="middle" fill="#9a3412">Re-run with --time-bucket minute or --time-bucket hour</text>',
                f'<text x="{chart_left}" y="{chart_bottom + 24}" font-size="12" fill="#64748b">summary-only export</text>',
                f'<text x="{chart_left + chart_width}" y="{chart_bottom + 24}" font-size="12" text-anchor="end" fill="#64748b">bucket charts unavailable</text>',
            ]
        )
        return parts

    for row in range(4):
        y_position = chart_top + (chart_height * row / 3)
        parts.append(
            f'<line x1="{chart_left}" y1="{y_position:.2f}" x2="{chart_left + chart_width}" y2="{y_position:.2f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 5" />'
        )

    parts.append(
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left + chart_width}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="1.5" />'
    )

    parts.extend(
        render_chart_annotations(
            annotations=annotations,
            chart_left=chart_left,
            chart_top=chart_top,
            chart_width=chart_width,
            chart_height=chart_height,
            marker_fill="#9a3412",
            line_stroke="#fdba74",
            value_count=max(len(left_values), len(right_values)),
        )
    )

    series = [
        (left_values, left_stroke_color, left_accent_color),
        (right_values, right_stroke_color, right_accent_color),
    ]
    for values, stroke_color, accent_color in series:
        segments = build_svg_chart_points(
            values,
            left=chart_left,
            top=chart_top,
            width=chart_width,
            height=chart_height,
            max_scale_value=display_max_value,
        )
        for segment in segments:
            if len(segment) >= 2:
                parts.append(
                    '<polyline fill="none" '
                    f'stroke="{stroke_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
                    f'points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in segment)}" />'
                )
            for x_position, y_position in segment:
                parts.append(
                    f'<circle cx="{x_position:.2f}" cy="{y_position:.2f}" r="4.2" fill="{accent_color}" stroke="#ffffff" stroke-width="1.4" />'
                )

    parts.extend(
        [
            f'<text x="{chart_left}" y="{chart_bottom + 24}" font-size="12" fill="#64748b">{escape(bucket_labels[0] if bucket_labels else "")}</text>',
            f'<text x="{chart_left + chart_width}" y="{chart_bottom + 24}" font-size="12" text-anchor="end" fill="#64748b">{escape(bucket_labels[-1] if bucket_labels else "")}</text>',
            f'<text x="{chart_left}" y="{chart_top - 10}" font-size="12" fill="#64748b">max {escape(format_card_metric_value(actual_max_value, suffix=metric_suffix))}</text>',
            f'<text x="{chart_left}" y="{chart_bottom + 42}" font-size="12" fill="#64748b">0{escape(metric_suffix)}</text>',
        ]
    )
    return parts


def format_time_bucket_card_svg(
    result: dict,
    *,
    source_label: str,
    id_prefix: str = "log-trend-card",
    annotations: Iterable[dict[str, object]] | None = None,
) -> str:
    summary = build_time_bucket_card_summary(result)
    time_buckets = result["time_buckets"]
    annotation_items = list(annotations or [])
    width = 1080
    title_id = f"{id_prefix}-title"
    desc_id = f"{id_prefix}-desc"
    bucket_labels = [format_bucket_axis_label(bucket["bucket_start"]) for bucket in time_buckets]
    coverage_label = summary["coverage_label"]
    granularity = summary["granularity"]
    time_window = result["time_window"]
    faceting = result["faceting"]

    requests_summary = "Peak "
    if summary["busiest_bucket"]:
        requests_summary += (
            f"{summary['busiest_bucket']['request_count']} requests at "
            f"{format_bucket_axis_label(summary['busiest_bucket']['bucket_start'])}"
        )
    else:
        requests_summary += "n/a"

    errors_summary = "Peak "
    if summary["highest_error_bucket"]:
        errors_summary += (
            f"{format_card_metric_value(summary['highest_error_bucket']['error_rate_pct'], suffix='%')} at "
            f"{format_bucket_axis_label(summary['highest_error_bucket']['bucket_start'])}"
        )
    else:
        errors_summary += "n/a"

    latency_summary = "Peak "
    if summary["slowest_bucket"]:
        latency_summary += (
            f"{format_card_metric_value(summary['slowest_bucket']['average_latency_ms'], suffix=' ms')} at "
            f"{format_bucket_axis_label(summary['slowest_bucket']['bucket_start'])}"
        )
    else:
        latency_summary += "n/a"

    metric_cards = [
        ("Matched requests", format_card_metric_value(summary["total_requests"]), "inside active buckets"),
        ("Overall error rate", format_card_metric_value(summary["overall_error_rate"], suffix="%"), format_card_metric_value(summary["total_errors"], suffix=" errors", decimals=0)),
        ("Weighted avg latency", format_card_metric_value(summary["weighted_latency_average"], suffix=" ms"), "request-time samples only"),
        ("Buckets", format_card_metric_value(summary["bucket_count"]), f"{granularity} granularity"),
    ]

    card_parts: list[str] = []
    for index, (label, value, note) in enumerate(metric_cards):
        card_left = 54 + (index * 244)
        card_parts.extend(
            [
                f'<rect x="{card_left}" y="110" width="220" height="94" rx="20" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
                f'<text x="{card_left + 18}" y="142" font-size="14" fill="#64748b">{escape(label)}</text>',
                f'<text x="{card_left + 18}" y="174" font-size="28" font-weight="700" fill="#0f172a">{escape(value)}</text>',
                f'<text x="{card_left + 18}" y="194" font-size="12" fill="#64748b">{escape(note)}</text>',
            ]
        )

    chart_parts = []
    chart_specs = [
        {
            "title": "Requests / bucket",
            "values": [float(bucket["request_count"]) for bucket in time_buckets],
            "summary_text": requests_summary,
            "stroke_color": "#2563eb",
            "accent_color": "#1d4ed8",
            "metric_suffix": "",
        },
        {
            "title": "Error rate / bucket",
            "values": [float(bucket["error_rate_pct"]) for bucket in time_buckets],
            "summary_text": errors_summary,
            "stroke_color": "#dc2626",
            "accent_color": "#b91c1c",
            "metric_suffix": "%",
        },
        {
            "title": "Avg latency / bucket",
            "values": [bucket["average_latency_ms"] for bucket in time_buckets],
            "summary_text": latency_summary,
            "stroke_color": "#7c3aed",
            "accent_color": "#6d28d9",
            "metric_suffix": " ms",
        },
    ]
    for index, chart_spec in enumerate(chart_specs):
        panel_left = 54 + (index * 324)
        chart_parts.extend(
            render_time_bucket_chart_panel(
                title=chart_spec["title"],
                values=chart_spec["values"],
                bucket_labels=bucket_labels,
                panel_left=panel_left,
                panel_top=234,
                panel_width=296,
                panel_height=282,
                stroke_color=chart_spec["stroke_color"],
                accent_color=chart_spec["accent_color"],
                summary_text=chart_spec["summary_text"],
                metric_suffix=chart_spec["metric_suffix"],
                annotations=annotation_items,
            )
        )

    footer_lines = [
        f"Coverage: {coverage_label}",
    ]
    if time_window:
        footer_lines.append(
            f"Window filter: {time_window['start'] or '(open)'} → {time_window['end'] or '(open)'}"
        )
    else:
        footer_lines.append("Window filter: full log span")
    if faceting:
        footer_lines.append(
            f"Facet fields available for companion CSV exports: {', '.join(faceting['fields'])}"
        )
    else:
        footer_lines.append("Facet fields: none selected for this run")
    footer_lines.extend(build_card_annotation_footer_lines(annotation_items))

    outer_height = 640 + (44 if annotation_items else 0)
    footer_height = 94 + (44 if annotation_items else 0)
    footer_note_y = 574 + (len(footer_lines) * 22) + 4
    height = 680 + (44 if annotation_items else 0)

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Log trend card for {escape(source_label)}</title>',
            f'  <desc id="{desc_id}">Trend card covering {escape(coverage_label)} at {escape(str(granularity))} granularity</desc>',
            '  <rect width="100%" height="100%" fill="#f8fafc" />',
            f'  <rect x="24" y="20" width="1032" height="{outer_height}" rx="30" fill="#eef2ff" stroke="#c7d2fe" stroke-width="2" />',
            '  <text x="54" y="64" font-size="32" font-weight="700" fill="#0f172a">Observability trend snapshot</text>',
            f'  <text x="54" y="92" font-size="16" fill="#475569">{escape(source_label)} · {escape(str(granularity))} buckets · {escape(str(summary["bucket_count"]))} bucket(s)</text>',
            *card_parts,
            *chart_parts,
            f'  <rect x="54" y="540" width="972" height="{footer_height}" rx="22" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
            *[
                f'<text x="78" y="{574 + (index * 22)}" font-size="14" fill="#334155">{escape(line)}</text>'
                for index, line in enumerate(footer_lines)
            ],
            f'  <text x="78" y="{footer_note_y}" font-size="12" fill="#64748b">Use the standalone HTML companion for a browser-friendly summary table, annotation legend, and quick portfolio caption copy.</text>',
            '</svg>',
        ]
    )


def format_time_bucket_card_html(
    result: dict,
    *,
    source_label: str,
    annotations: Iterable[dict[str, object]] | None = None,
) -> str:
    summary = build_time_bucket_card_summary(result)
    faceting = result["faceting"]
    time_window = result["time_window"]
    annotation_items = list(annotations or [])
    annotation_map = build_card_annotation_map(annotation_items)
    table_rows = []
    for bucket in result["time_buckets"]:
        annotation = annotation_map.get(str(bucket["bucket_start"]))
        annotation_cell = "—"
        if annotation:
            annotation_cell = (
                f'{build_annotation_marker_chip_html(annotation)}'
                f'{build_annotation_theme_badge_html(annotation)} '
                f'{escape(str(annotation["label"]))}'
            )
        table_rows.append(
            "".join(
                [
                    "<tr>",
                    f"<td><code>{escape(bucket['bucket_start'])}</code></td>",
                    f"<td><code>{escape(bucket['bucket_end'])}</code></td>",
                    f"<td>{bucket['request_count']}</td>",
                    f"<td>{escape(format_card_metric_value(bucket['error_rate_pct'], suffix='%'))}</td>",
                    f"<td>{escape(format_card_metric_value(bucket['average_latency_ms'], suffix=' ms'))}</td>",
                    f"<td>{escape(format_card_metric_value(bucket['average_upstream_latency_ms'], suffix=' ms'))}</td>",
                    f"<td><code>{escape(bucket['top_path'] or '(none)')}</code></td>",
                    f"<td>{annotation_cell}</td>",
                    "</tr>",
                ]
            )
        )
    if not table_rows:
        table_rows.append(
            '<tr><td colspan="8">No matched buckets were produced for this run.</td></tr>'
        )

    meta_items = [
        ("Source", source_label),
        ("Granularity", str(summary["granularity"])),
        ("Coverage", str(summary["coverage_label"])),
        ("Matched requests", format_card_metric_value(summary["total_requests"])),
        ("Overall error rate", format_card_metric_value(summary["overall_error_rate"], suffix="%")),
        ("Weighted avg latency", format_card_metric_value(summary["weighted_latency_average"], suffix=" ms")),
    ]
    if time_window:
        meta_items.append(
            (
                "Window filter",
                f"{time_window['start'] or '(open)'} → {time_window['end'] or '(open)'}",
            )
        )
    if faceting:
        meta_items.append(("Facet fields", ", ".join(faceting["fields"])))
        meta_items.append(
            (
                "Facet trend rows",
                format_card_metric_value(len(result["time_bucket_facet_breakdown"])),
            )
        )
    if annotation_items:
        meta_items.append(("Annotation markers", format_card_metric_value(len(annotation_items))))

    meta_html = "".join(
        f'<li><strong>{escape(label)}</strong><br><span>{escape(value)}</span></li>'
        for label, value in meta_items
    )
    annotation_html = ""
    if annotation_items:
        annotation_html = "".join(
            [
                '<section>',
                '  <h2>Annotation markers</h2>',
                '  <p class="caption">These markers pin deploys, incidents, or other callouts onto the shared bucket timeline used by the SVG card.</p>',
                '  <ul class="annotation-list">',
                *[
                    (
                        '    <li>'
                        f'{build_annotation_marker_chip_html(annotation)}'
                        f'{build_annotation_theme_badge_html(annotation)} '
                        f'<strong>{escape(str(annotation["range_label"]))}</strong><br>'
                        f'<span>{escape(str(annotation["label"]))}</span><br>'
                        f'<span class="annotation-time">Events: {escape(str(annotation["event_time_label"]))}</span></li>'
                    )
                    for annotation in annotation_items
                ],
                '  </ul>',
                '</section>',
            ]
        )

    svg_payload = format_time_bucket_card_svg(
        result,
        source_label=source_label,
        id_prefix="log-trend-card-html",
        annotations=annotation_items,
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Log trend card ({escape(source_label)})</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1240px; padding: 0 1rem 3rem; line-height: 1.5; background: #f8fafc; color: #0f172a; }}
    h1, h2 {{ line-height: 1.15; }}
    code {{ font-family: "SFMono-Regular", Consolas, monospace; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.8rem; padding: 0; margin: 1rem 0 1.5rem; }}
    .meta li {{ list-style: none; border: 1px solid rgba(148, 163, 184, 0.32); border-radius: 1rem; padding: 0.85rem 1rem; background: rgba(255, 255, 255, 0.82); }}
    .card-shell {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.2rem; padding: 1rem; background: rgba(255, 255, 255, 0.9); box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08); }}
    svg {{ width: 100%; height: auto; display: block; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: rgba(255, 255, 255, 0.86); }}
    th, td {{ padding: 0.7rem 0.8rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: left; }}
    th {{ font-size: 0.9rem; color: #475569; }}
    .caption {{ color: #475569; margin-top: 0.8rem; }}
    .annotation-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.8rem; list-style: none; padding: 0; margin: 1rem 0 0; }}
    .annotation-list li {{ border: 1px solid rgba(99, 102, 241, 0.22); border-radius: 1rem; padding: 0.85rem 1rem; background: rgba(255, 255, 255, 0.82); }}
    .annotation-chip {{ display: inline-flex; align-items: center; justify-content: center; min-width: 1.5rem; height: 1.5rem; padding: 0 0.35rem; border-radius: 999px; color: #ffffff; font-size: 0.82rem; font-weight: 700; margin-right: 0.45rem; }}
    .annotation-theme {{ display: inline-flex; align-items: center; border: 1px solid transparent; border-radius: 999px; padding: 0.12rem 0.5rem; font-size: 0.78rem; font-weight: 700; margin-right: 0.45rem; vertical-align: middle; }}
    .annotation-time {{ color: #64748b; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Log trend card</h1>
  <p>This browser-friendly artifact turns time-bucket exports into an easy-to-screenshot release / incident summary without requiring notebooks or spreadsheet chart cleanup.</p>
  <ul class="meta">{meta_html}</ul>
  <section class="card-shell">
    {svg_payload}
  </section>
  {annotation_html}
  <section>
    <h2>Bucket summary table</h2>
    <p class="caption">Use this table when you want the exact bucket start/end boundaries plus the request/error/latency values beside the visual sparkline card.</p>
    <table>
      <thead>
        <tr>
          <th>Bucket start</th>
          <th>Bucket end</th>
          <th>Requests</th>
          <th>Error rate</th>
          <th>Avg latency</th>
          <th>Avg upstream latency</th>
          <th>Top path</th>
          <th>Annotation</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
  </section>
</body>
</html>
'''


def build_facet_comparison_card_summary(comparison: dict[str, object]) -> dict[str, object]:
    left = comparison["left"]
    right = comparison["right"]
    delta = comparison["delta"]
    time_buckets = comparison["time_buckets"]
    time_bucketing = comparison["time_bucketing"]
    granularity = "summary"
    if time_bucketing:
        granularity = str(time_bucketing["granularity"])
    coverage_label = "Summary-only comparison"
    if time_buckets:
        coverage_label = format_bucket_range_label(
            time_buckets[0]["bucket_start"],
            time_buckets[-1]["bucket_end"],
        )

    request_gap_bucket = max(
        time_buckets,
        key=lambda bucket: (
            abs(bucket["request_count_delta"]),
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )
    error_gap_bucket = max(
        time_buckets,
        key=lambda bucket: (
            abs(bucket["error_rate_pct_delta"] or 0),
            abs(bucket["error_count_delta"]),
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )
    latency_gap_bucket = max(
        (bucket for bucket in time_buckets if bucket["average_latency_ms_delta"] is not None),
        key=lambda bucket: (
            abs(bucket["average_latency_ms_delta"]),
            -parse_bucket_datetime(bucket["bucket_start"]).timestamp(),
        ),
        default=None,
    )

    return {
        "granularity": granularity,
        "coverage_label": coverage_label,
        "aligned_bucket_count": len(time_buckets),
        "left": left,
        "right": right,
        "delta": delta,
        "request_gap_bucket": request_gap_bucket,
        "error_gap_bucket": error_gap_bucket,
        "latency_gap_bucket": latency_gap_bucket,
    }


def format_facet_comparison_card_svg(
    comparison: dict[str, object],
    *,
    source_label: str,
    time_window: dict[str, str | int] | None = None,
    id_prefix: str = "log-comparison-card",
    annotations: Iterable[dict[str, object]] | None = None,
) -> str:
    summary = build_facet_comparison_card_summary(comparison)
    left = summary["left"]
    right = summary["right"]
    delta = summary["delta"]
    left_summary = left["summary"]
    right_summary = right["summary"]
    time_buckets = comparison["time_buckets"]
    bucket_labels = [format_bucket_axis_label(bucket["bucket_start"]) for bucket in time_buckets]
    annotation_items = list(annotations or [])
    width = 1080
    title_id = f"{id_prefix}-title"
    desc_id = f"{id_prefix}-desc"
    coverage_label = summary["coverage_label"]
    granularity = summary["granularity"]

    requests_summary = f'{left["value"]}: {format_card_metric_value(left_summary["request_count"])} vs {right["value"]}: {format_card_metric_value(right_summary["request_count"])}'
    if summary["request_gap_bucket"]:
        requests_summary = (
            f'Largest gap {format_signed_card_metric_value(summary["request_gap_bucket"]["request_count_delta"])} at '
            f'{format_bucket_axis_label(summary["request_gap_bucket"]["bucket_start"])}'
        )

    errors_summary = f'Overall Δ {format_signed_card_metric_value(delta["error_rate_pct_delta"], suffix=" pp")}'
    if summary["error_gap_bucket"]:
        errors_summary = (
            f'Largest gap {format_signed_card_metric_value(summary["error_gap_bucket"]["error_rate_pct_delta"], suffix=" pp")} at '
            f'{format_bucket_axis_label(summary["error_gap_bucket"]["bucket_start"])}'
        )

    latency_summary = (
        f'{comparison["delta_direction"]}: '
        f'{format_signed_card_metric_value(delta["average_latency_ms_delta"], suffix=" ms")} avg latency'
    )
    if summary["latency_gap_bucket"]:
        latency_summary = (
            f'Largest gap {format_signed_card_metric_value(summary["latency_gap_bucket"]["average_latency_ms_delta"], suffix=" ms")} at '
            f'{format_bucket_axis_label(summary["latency_gap_bucket"]["bucket_start"])}'
        )

    metric_cards = [
        (
            left["label"],
            format_card_metric_value(left_summary["request_count"]),
            f'{format_card_metric_value(left_summary["error_rate_pct"], suffix="%")}'
            f' errors · top {left_summary["top_path"] or "(none)"}',
        ),
        (
            right["label"],
            format_card_metric_value(right_summary["request_count"]),
            f'{format_card_metric_value(right_summary["error_rate_pct"], suffix="%")}'
            f' errors · top {right_summary["top_path"] or "(none)"}',
        ),
        (
            "Error-rate delta",
            format_signed_card_metric_value(delta["error_rate_pct_delta"], suffix=" pp"),
            comparison["delta_direction"],
        ),
        (
            "P95 latency delta",
            format_signed_card_metric_value(delta["p95_latency_ms_delta"], suffix=" ms"),
            f'avg Δ {format_signed_card_metric_value(delta["average_latency_ms_delta"], suffix=" ms")}',
        ),
    ]

    card_parts: list[str] = []
    for index, (label, value, note) in enumerate(metric_cards):
        card_left = 54 + (index * 244)
        card_parts.extend(
            [
                f'<rect x="{card_left}" y="110" width="220" height="94" rx="20" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
                f'<text x="{card_left + 18}" y="142" font-size="14" fill="#64748b">{escape(label)}</text>',
                f'<text x="{card_left + 18}" y="174" font-size="28" font-weight="700" fill="#0f172a">{escape(value)}</text>',
                f'<text x="{card_left + 18}" y="194" font-size="12" fill="#64748b">{escape(note)}</text>',
            ]
        )

    chart_specs = [
        {
            "title": "Requests / bucket",
            "left_values": [float(bucket["left_request_count"]) for bucket in time_buckets],
            "right_values": [float(bucket["right_request_count"]) for bucket in time_buckets],
            "summary_text": requests_summary,
            "metric_suffix": "",
        },
        {
            "title": "Error rate / bucket",
            "left_values": [float(bucket["left_error_rate_pct"]) for bucket in time_buckets],
            "right_values": [float(bucket["right_error_rate_pct"]) for bucket in time_buckets],
            "summary_text": errors_summary,
            "metric_suffix": "%",
        },
        {
            "title": "Avg latency / bucket",
            "left_values": [bucket["left_average_latency_ms"] for bucket in time_buckets],
            "right_values": [bucket["right_average_latency_ms"] for bucket in time_buckets],
            "summary_text": latency_summary,
            "metric_suffix": " ms",
        },
    ]

    chart_parts: list[str] = []
    for index, chart_spec in enumerate(chart_specs):
        panel_left = 54 + (index * 324)
        chart_parts.extend(
            render_comparison_chart_panel(
                title=chart_spec["title"],
                left_values=chart_spec["left_values"],
                right_values=chart_spec["right_values"],
                bucket_labels=bucket_labels,
                panel_left=panel_left,
                panel_top=234,
                panel_width=296,
                panel_height=294,
                left_label=left["value"],
                right_label=right["value"],
                left_stroke_color="#2563eb",
                right_stroke_color="#f97316",
                left_accent_color="#1d4ed8",
                right_accent_color="#ea580c",
                summary_text=chart_spec["summary_text"],
                metric_suffix=chart_spec["metric_suffix"],
                annotations=annotation_items,
            )
        )

    footer_lines = [
        f'Comparison: {left["label"]} vs {right["label"]} ({comparison["delta_direction"]})',
        f'Coverage: {coverage_label}',
    ]
    if time_window:
        footer_lines.append(
            f'Window filter: {time_window["start"] or "(open)"} → {time_window["end"] or "(open)"}'
        )
    else:
        footer_lines.append("Window filter: full log span")
    if comparison["time_bucketing"]:
        footer_lines.append(
            f'Aligned buckets: {summary["aligned_bucket_count"]} ({granularity})'
        )
    else:
        footer_lines.append("Aligned buckets: none (summary-only comparison)")
    footer_lines.extend(build_card_annotation_footer_lines(annotation_items))

    outer_height = 660 + (44 if annotation_items else 0)
    footer_height = 94 + (44 if annotation_items else 0)
    footer_note_y = 588 + (len(footer_lines) * 22) + 4
    height = 700 + (44 if annotation_items else 0)

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Facet comparison card for {escape(source_label)}</title>',
            f'  <desc id="{desc_id}">Comparison card showing {escape(left["label"])} versus {escape(right["label"])} over {escape(coverage_label)}</desc>',
            '  <rect width="100%" height="100%" fill="#fff7ed" />',
            f'  <rect x="24" y="20" width="1032" height="{outer_height}" rx="30" fill="#fff1e6" stroke="#fdba74" stroke-width="2" />',
            '  <text x="54" y="64" font-size="32" font-weight="700" fill="#0f172a">Release comparison snapshot</text>',
            f'  <text x="54" y="92" font-size="16" fill="#475569">{escape(source_label)} · {escape(left["label"])} vs {escape(right["label"])} · {escape(str(summary["aligned_bucket_count"]))} aligned bucket(s)</text>',
            *card_parts,
            *chart_parts,
            f'  <rect x="54" y="554" width="972" height="{footer_height}" rx="22" fill="#ffffff" stroke="#d7dde8" stroke-width="1.5" />',
            *[
                f'<text x="78" y="{588 + (index * 22)}" font-size="14" fill="#334155">{escape(line)}</text>'
                for index, line in enumerate(footer_lines)
            ],
            f'  <text x="78" y="{footer_note_y}" font-size="12" fill="#64748b">Use the HTML companion for a browser-friendly release-review table, annotation legend, and exact per-bucket deltas.</text>',
            '</svg>',
        ]
    )


def format_facet_comparison_card_html(
    comparison: dict[str, object],
    *,
    source_label: str,
    time_window: dict[str, str | int] | None = None,
    annotations: Iterable[dict[str, object]] | None = None,
) -> str:
    summary = build_facet_comparison_card_summary(comparison)
    left = summary["left"]
    right = summary["right"]
    delta = summary["delta"]
    left_summary = left["summary"]
    right_summary = right["summary"]
    annotation_items = list(annotations or [])
    annotation_map = build_card_annotation_map(annotation_items)

    meta_items = [
        ("Source", source_label),
        ("Comparison", f'{left["label"]} vs {right["label"]}'),
        ("Delta direction", comparison["delta_direction"]),
        ("Coverage", str(summary["coverage_label"])),
        ("Aligned buckets", format_card_metric_value(summary["aligned_bucket_count"])),
    ]
    if comparison["time_bucketing"]:
        meta_items.append(("Granularity", str(comparison["time_bucketing"]["granularity"])))
    if time_window:
        meta_items.append(
            (
                "Window filter",
                f'{time_window["start"] or "(open)"} → {time_window["end"] or "(open)"}',
            )
        )
    if annotation_items:
        meta_items.append(("Annotation markers", format_card_metric_value(len(annotation_items))))

    meta_html = "".join(
        f'<li><strong>{escape(label)}</strong><br><span>{escape(value)}</span></li>'
        for label, value in meta_items
    )

    summary_rows = [
        (
            "Requests",
            format_card_metric_value(left_summary["request_count"]),
            format_card_metric_value(right_summary["request_count"]),
            format_signed_card_metric_value(delta["request_count_delta"]),
        ),
        (
            "Errors",
            format_card_metric_value(left_summary["error_count"]),
            format_card_metric_value(right_summary["error_count"]),
            format_signed_card_metric_value(delta["error_count_delta"]),
        ),
        (
            "Error rate",
            format_card_metric_value(left_summary["error_rate_pct"], suffix="%"),
            format_card_metric_value(right_summary["error_rate_pct"], suffix="%"),
            format_signed_card_metric_value(delta["error_rate_pct_delta"], suffix=" pp"),
        ),
        (
            "Avg latency",
            format_card_metric_value(left_summary["average_latency_ms"], suffix=" ms"),
            format_card_metric_value(right_summary["average_latency_ms"], suffix=" ms"),
            format_signed_card_metric_value(delta["average_latency_ms_delta"], suffix=" ms"),
        ),
        (
            "P95 latency",
            format_card_metric_value(left_summary["p95_latency_ms"], suffix=" ms"),
            format_card_metric_value(right_summary["p95_latency_ms"], suffix=" ms"),
            format_signed_card_metric_value(delta["p95_latency_ms_delta"], suffix=" ms"),
        ),
        (
            "Max latency",
            format_card_metric_value(left_summary["max_latency_ms"], suffix=" ms"),
            format_card_metric_value(right_summary["max_latency_ms"], suffix=" ms"),
            format_signed_card_metric_value(delta["max_latency_ms_delta"], suffix=" ms"),
        ),
        (
            "Avg upstream latency",
            format_card_metric_value(left_summary["average_upstream_latency_ms"], suffix=" ms"),
            format_card_metric_value(right_summary["average_upstream_latency_ms"], suffix=" ms"),
            format_signed_card_metric_value(delta["average_upstream_latency_ms_delta"], suffix=" ms"),
        ),
        (
            "P95 upstream latency",
            format_card_metric_value(left_summary["p95_upstream_latency_ms"], suffix=" ms"),
            format_card_metric_value(right_summary["p95_upstream_latency_ms"], suffix=" ms"),
            format_signed_card_metric_value(delta["p95_upstream_latency_ms_delta"], suffix=" ms"),
        ),
        (
            "Top path",
            f'{left_summary["top_path"] or "(none)"} ({left_summary["top_path_count"]})',
            f'{right_summary["top_path"] or "(none)"} ({right_summary["top_path_count"]})',
            "—",
        ),
    ]
    summary_table_rows = "".join(
        "".join(
            [
                "<tr>",
                f"<td>{escape(metric)}</td>",
                f"<td>{escape(left_value)}</td>",
                f"<td>{escape(right_value)}</td>",
                f"<td>{escape(delta_value)}</td>",
                "</tr>",
            ]
        )
        for metric, left_value, right_value, delta_value in summary_rows
    )

    bucket_table_rows = []
    for bucket in comparison["time_buckets"]:
        annotation = annotation_map.get(str(bucket["bucket_start"]))
        annotation_cell = "—"
        if annotation:
            annotation_cell = (
                f'{build_annotation_marker_chip_html(annotation)}'
                f'{build_annotation_theme_badge_html(annotation)} '
                f'{escape(str(annotation["label"]))}'
            )
        bucket_table_rows.append(
            "".join(
                [
                    "<tr>",
                    f'<td><code>{escape(bucket["bucket_start"])}</code></td>',
                    f'<td><code>{escape(bucket["bucket_end"])}</code></td>',
                    f'<td>{bucket["left_request_count"]}</td>',
                    f'<td>{bucket["right_request_count"]}</td>',
                    f'<td>{escape(format_signed_card_metric_value(bucket["request_count_delta"]))}</td>',
                    f'<td>{escape(format_card_metric_value(bucket["left_error_rate_pct"], suffix="%"))}</td>',
                    f'<td>{escape(format_card_metric_value(bucket["right_error_rate_pct"], suffix="%"))}</td>',
                    f'<td>{escape(format_signed_card_metric_value(bucket["error_rate_pct_delta"], suffix=" pp"))}</td>',
                    f'<td>{escape(format_card_metric_value(bucket["left_average_latency_ms"], suffix=" ms"))}</td>',
                    f'<td>{escape(format_card_metric_value(bucket["right_average_latency_ms"], suffix=" ms"))}</td>',
                    f'<td>{escape(format_signed_card_metric_value(bucket["average_latency_ms_delta"], suffix=" ms"))}</td>',
                    f'<td><code>{escape(bucket["left_top_path"] or "(none)")}</code></td>',
                    f'<td><code>{escape(bucket["right_top_path"] or "(none)")}</code></td>',
                    f'<td>{annotation_cell}</td>',
                    "</tr>",
                ]
            )
        )
    if not bucket_table_rows:
        bucket_table_rows.append(
            '<tr><td colspan="14">No aligned bucket rows were produced for this run. Re-run with --time-bucket minute or --time-bucket hour for side-by-side charts and bucket tables.</td></tr>'
        )

    annotation_html = ""
    if annotation_items:
        annotation_html = "".join(
            [
                '<section>',
                '  <h2>Annotation markers</h2>',
                '  <p class="caption">These markers pin deploys, incidents, or other callouts onto the aligned bucket timeline used by the SVG comparison card.</p>',
                '  <ul class="annotation-list">',
                *[
                    (
                        '    <li>'
                        f'{build_annotation_marker_chip_html(annotation)}'
                        f'{build_annotation_theme_badge_html(annotation)} '
                        f'<strong>{escape(str(annotation["range_label"]))}</strong><br>'
                        f'<span>{escape(str(annotation["label"]))}</span><br>'
                        f'<span class="annotation-time">Events: {escape(str(annotation["event_time_label"]))}</span></li>'
                    )
                    for annotation in annotation_items
                ],
                '  </ul>',
                '</section>',
            ]
        )

    svg_payload = format_facet_comparison_card_svg(
        comparison,
        source_label=source_label,
        time_window=time_window,
        id_prefix="log-comparison-card-html",
        annotations=annotation_items,
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Release comparison card ({escape(source_label)})</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1320px; padding: 0 1rem 3rem; line-height: 1.5; background: #fff7ed; color: #0f172a; }}
    h1, h2 {{ line-height: 1.15; }}
    code {{ font-family: "SFMono-Regular", Consolas, monospace; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.8rem; padding: 0; margin: 1rem 0 1.5rem; }}
    .meta li {{ list-style: none; border: 1px solid rgba(148, 163, 184, 0.32); border-radius: 1rem; padding: 0.85rem 1rem; background: rgba(255, 255, 255, 0.82); }}
    .card-shell {{ border: 1px solid rgba(251, 146, 60, 0.28); border-radius: 1.2rem; padding: 1rem; background: rgba(255, 255, 255, 0.92); box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08); }}
    svg {{ width: 100%; height: auto; display: block; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: rgba(255, 255, 255, 0.88); }}
    th, td {{ padding: 0.7rem 0.8rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: left; vertical-align: top; }}
    th {{ font-size: 0.9rem; color: #475569; }}
    .caption {{ color: #475569; margin-top: 0.8rem; }}
    .annotation-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.8rem; list-style: none; padding: 0; margin: 1rem 0 0; }}
    .annotation-list li {{ border: 1px solid rgba(251, 146, 60, 0.28); border-radius: 1rem; padding: 0.85rem 1rem; background: rgba(255, 255, 255, 0.82); }}
    .annotation-chip {{ display: inline-flex; align-items: center; justify-content: center; min-width: 1.5rem; height: 1.5rem; padding: 0 0.35rem; border-radius: 999px; color: #ffffff; font-size: 0.82rem; font-weight: 700; margin-right: 0.45rem; }}
    .annotation-theme {{ display: inline-flex; align-items: center; border: 1px solid transparent; border-radius: 999px; padding: 0.12rem 0.5rem; font-size: 0.78rem; font-weight: 700; margin-right: 0.45rem; vertical-align: middle; }}
    .annotation-time {{ color: #7c2d12; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Release comparison card</h1>
  <p>This browser-friendly artifact turns facet comparisons into a slide-ready release review card with exact summary deltas, aligned per-bucket rows, and optional deploy/incident callouts for screenshots, demos, and portfolio case studies.</p>
  <ul class="meta">{meta_html}</ul>
  <section class="card-shell">
    {svg_payload}
  </section>
  {annotation_html}
  <section>
    <h2>Summary delta table</h2>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>{escape(left["label"])}</th>
          <th>{escape(right["label"])}</th>
          <th>Delta</th>
        </tr>
      </thead>
      <tbody>
        {summary_table_rows}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Aligned bucket rows</h2>
    <p class="caption">Use these rows when you want exact per-bucket request, error-rate, latency, and annotation deltas beside the higher-level comparison card.</p>
    <table>
      <thead>
        <tr>
          <th>Bucket start</th>
          <th>Bucket end</th>
          <th>{escape(left["value"])} requests</th>
          <th>{escape(right["value"])} requests</th>
          <th>Δ requests</th>
          <th>{escape(left["value"])} error rate</th>
          <th>{escape(right["value"])} error rate</th>
          <th>Δ error rate</th>
          <th>{escape(left["value"])} avg latency</th>
          <th>{escape(right["value"])} avg latency</th>
          <th>Δ avg latency</th>
          <th>{escape(left["value"])} top path</th>
          <th>{escape(right["value"])} top path</th>
          <th>Annotation</th>
        </tr>
      </thead>
      <tbody>
        {''.join(bucket_table_rows)}
      </tbody>
    </table>
  </section>
</body>
</html>
'''


def parse_line(line: str) -> ParsedLogLine | None:
    match = LOG_RE.match(line.strip())
    if not match:
        return None

    bytes_raw = match.group("bytes")
    referrer = match.group("referrer")
    user_agent = match.group("user_agent")
    unnamed_latency, named_fields = parse_extra_fields(match.group("extra"))
    request_time_ms = normalize_named_timing_ms(named_fields.get("request_time"))
    upstream_response_time_ms = normalize_named_timing_ms(
        named_fields.get("upstream_response_time")
    )
    primary_latency_ms = request_time_ms
    if primary_latency_ms is None:
        primary_latency_ms = normalize_latency_ms(unnamed_latency)

    return ParsedLogLine(
        ip=match.group("ip"),
        timestamp=parse_log_timestamp(match.group("timestamp")),
        method=match.group("method"),
        path=match.group("path"),
        status=match.group("status"),
        bytes_sent=0 if bytes_raw == "-" else int(bytes_raw),
        referrer=None if referrer in (None, "-") else referrer,
        user_agent=None if user_agent in (None, "-") else user_agent,
        latency_ms=primary_latency_ms,
        request_time_ms=request_time_ms,
        upstream_response_time_ms=upstream_response_time_ms,
        named_fields=named_fields,
    )


def analyze_parsed_lines(
    parsed_lines: Iterable[ParsedLogLine],
    *,
    top_n: int,
    latency_limit: int,
    hotspot_filters: dict[str, list[str]] | None,
    time_bucket_granularity: str | None,
    normalized_facet_fields: list[str],
) -> dict:
    status_counts = Counter()
    ip_counts = Counter()
    path_counts = Counter()
    method_counts = Counter()
    referrer_counts = Counter()
    user_agent_counts = Counter()
    latencies_ms: list[float] = []
    upstream_latencies_ms: list[float] = []
    path_latencies: dict[str, list[float]] = defaultdict(list)
    upstream_path_latencies: dict[str, list[float]] = defaultdict(list)
    path_latencies_by_facet: dict[tuple[str, tuple[str, ...]], list[float]] = defaultdict(list)
    upstream_path_latencies_by_facet: dict[tuple[str, tuple[str, ...]], list[float]] = defaultdict(list)
    time_bucket_rows: dict[datetime, dict[str, object]] = {}
    time_bucket_facet_rows: dict[tuple[datetime, tuple[str, ...]], dict[str, object]] = {}
    total_bytes = 0
    total_requests = 0

    for parsed in parsed_lines:
        facet_values: tuple[str, ...] | None = None
        if normalized_facet_fields:
            facet_values = build_facet_values(parsed.named_fields, normalized_facet_fields)

        total_requests += 1
        total_bytes += parsed.bytes_sent
        status_counts[parsed.status] += 1
        ip_counts[parsed.ip] += 1
        path_counts[parsed.path] += 1
        method_counts[parsed.method] += 1
        if parsed.referrer:
            referrer_counts[parsed.referrer] += 1
        if parsed.user_agent:
            user_agent_counts[parsed.user_agent] += 1
        if parsed.latency_ms is not None:
            latencies_ms.append(parsed.latency_ms)
            if matches_hotspot_filters(parsed, hotspot_filters):
                path_latencies[parsed.path].append(parsed.latency_ms)
                if facet_values is not None:
                    path_latencies_by_facet[(parsed.path, facet_values)].append(parsed.latency_ms)
        if parsed.upstream_response_time_ms is not None:
            upstream_latencies_ms.append(parsed.upstream_response_time_ms)
            if matches_hotspot_filters(parsed, hotspot_filters):
                upstream_path_latencies[parsed.path].append(parsed.upstream_response_time_ms)
                if facet_values is not None:
                    upstream_path_latencies_by_facet[(parsed.path, facet_values)].append(
                        parsed.upstream_response_time_ms
                    )

        if time_bucket_granularity and parsed.timestamp is not None:
            bucket_start = bucket_timestamp(parsed.timestamp, time_bucket_granularity)
            bucket = time_bucket_rows.setdefault(
                bucket_start,
                {
                    "request_count": 0,
                    "error_count": 0,
                    "path_counts": Counter(),
                    "latencies_ms": [],
                    "upstream_latencies_ms": [],
                },
            )
            bucket["request_count"] += 1
            if parsed.status.startswith(("4", "5")):
                bucket["error_count"] += 1
            bucket["path_counts"][parsed.path] += 1
            if parsed.latency_ms is not None:
                bucket["latencies_ms"].append(parsed.latency_ms)
            if parsed.upstream_response_time_ms is not None:
                bucket["upstream_latencies_ms"].append(parsed.upstream_response_time_ms)

            if facet_values is not None:
                facet_bucket = time_bucket_facet_rows.setdefault(
                    (bucket_start, facet_values),
                    {
                        "request_count": 0,
                        "error_count": 0,
                        "path_counts": Counter(),
                        "latencies_ms": [],
                        "upstream_latencies_ms": [],
                    },
                )
                facet_bucket["request_count"] += 1
                if parsed.status.startswith(("4", "5")):
                    facet_bucket["error_count"] += 1
                facet_bucket["path_counts"][parsed.path] += 1
                if parsed.latency_ms is not None:
                    facet_bucket["latencies_ms"].append(parsed.latency_ms)
                if parsed.upstream_response_time_ms is not None:
                    facet_bucket["upstream_latencies_ms"].append(parsed.upstream_response_time_ms)

    average_bytes = round(total_bytes / total_requests, 2) if total_requests else 0.0
    time_buckets = summarize_time_buckets(time_bucket_rows, time_bucket_granularity)
    faceting = build_faceting_metadata(normalized_facet_fields)
    return {
        "total_requests": total_requests,
        "total_bytes": total_bytes,
        "average_bytes": average_bytes,
        "status_counts": dict(status_counts),
        "method_counts": dict(method_counts),
        "top_ips": ip_counts.most_common(top_n),
        "top_paths": path_counts.most_common(top_n),
        "top_referrers": referrer_counts.most_common(top_n),
        "top_user_agents": user_agent_counts.most_common(top_n),
        "latency_summary": summarize_latencies(latencies_ms),
        "upstream_latency_summary": summarize_latencies(upstream_latencies_ms),
        "hotspot_filters": hotspot_filters,
        "faceting": faceting,
        "time_bucketing": build_time_bucket_metadata(
            time_bucket_granularity,
            len(time_buckets),
        ),
        "time_buckets": time_buckets,
        "time_bucket_facet_breakdown": summarize_time_bucket_facets(
            time_bucket_facet_rows,
            time_bucket_granularity,
            normalized_facet_fields,
        ),
        "path_latency_breakdown": summarize_path_latencies(path_latencies, latency_limit),
        "path_latency_facet_breakdown": summarize_path_latencies_by_facet(
            path_latencies_by_facet,
            normalized_facet_fields,
            latency_limit,
        ),
        "upstream_path_latency_breakdown": summarize_path_latencies(
            upstream_path_latencies,
            latency_limit,
        ),
        "upstream_path_latency_facet_breakdown": summarize_path_latencies_by_facet(
            upstream_path_latencies_by_facet,
            normalized_facet_fields,
            latency_limit,
        ),
    }


def build_facet_comparison(
    parsed_lines: list[ParsedLogLine],
    *,
    comparison_field: str | None,
    comparison_values: tuple[str, str] | None,
    top_n: int,
    latency_limit: int,
    hotspot_filters: dict[str, list[str]] | None,
    time_bucket_granularity: str | None,
) -> dict[str, object] | None:
    if comparison_field is None or comparison_values is None:
        return None

    left_value, right_value = comparison_values
    left_lines = [
        parsed
        for parsed in parsed_lines
        if resolve_named_field_value(parsed.named_fields, comparison_field) == left_value
    ]
    right_lines = [
        parsed
        for parsed in parsed_lines
        if resolve_named_field_value(parsed.named_fields, comparison_field) == right_value
    ]

    left_result = analyze_parsed_lines(
        left_lines,
        top_n=top_n,
        latency_limit=latency_limit,
        hotspot_filters=hotspot_filters,
        time_bucket_granularity=time_bucket_granularity,
        normalized_facet_fields=[],
    )
    right_result = analyze_parsed_lines(
        right_lines,
        top_n=top_n,
        latency_limit=latency_limit,
        hotspot_filters=hotspot_filters,
        time_bucket_granularity=time_bucket_granularity,
        normalized_facet_fields=[],
    )

    left_summary = summarize_release_review_metrics(left_result)
    right_summary = summarize_release_review_metrics(right_result)
    time_bucket_rows = build_facet_comparison_bucket_rows(
        left_result,
        right_result,
        granularity=time_bucket_granularity,
    )

    return {
        "field": comparison_field,
        "left": {
            "value": left_value,
            "label": f"{comparison_field}={left_value}",
            "summary": left_summary,
        },
        "right": {
            "value": right_value,
            "label": f"{comparison_field}={right_value}",
            "summary": right_summary,
        },
        "delta_direction": f"{right_value} minus {left_value}",
        "delta": {
            "request_count_delta": right_summary["request_count"] - left_summary["request_count"],
            "error_count_delta": right_summary["error_count"] - left_summary["error_count"],
            "error_rate_pct_delta": subtract_optional_metric(
                right_summary["error_rate_pct"],
                left_summary["error_rate_pct"],
            ),
            "average_latency_ms_delta": subtract_optional_metric(
                right_summary["average_latency_ms"],
                left_summary["average_latency_ms"],
            ),
            "p95_latency_ms_delta": subtract_optional_metric(
                right_summary["p95_latency_ms"],
                left_summary["p95_latency_ms"],
            ),
            "max_latency_ms_delta": subtract_optional_metric(
                right_summary["max_latency_ms"],
                left_summary["max_latency_ms"],
            ),
            "average_upstream_latency_ms_delta": subtract_optional_metric(
                right_summary["average_upstream_latency_ms"],
                left_summary["average_upstream_latency_ms"],
            ),
            "p95_upstream_latency_ms_delta": subtract_optional_metric(
                right_summary["p95_upstream_latency_ms"],
                left_summary["p95_upstream_latency_ms"],
            ),
            "max_upstream_latency_ms_delta": subtract_optional_metric(
                right_summary["max_upstream_latency_ms"],
                left_summary["max_upstream_latency_ms"],
            ),
        },
        "time_bucketing": build_time_bucket_metadata(
            time_bucket_granularity,
            len(time_bucket_rows),
        ),
        "time_buckets": time_bucket_rows,
    }


def analyze_lines(
    lines: Iterable[str],
    top_n: int = 3,
    latency_top_n: int | None = None,
    hotspot_statuses: Iterable[str] | None = None,
    hotspot_methods: Iterable[str] | None = None,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    time_bucket_granularity: str | None = None,
    facet_fields: Iterable[str] | None = None,
    facet_compare_field: str | None = None,
    facet_compare_values: tuple[str, str] | None = None,
) -> dict:
    invalid_lines = 0
    excluded_requests = 0
    parsed_lines: list[ParsedLogLine] = []

    latency_limit = top_n if latency_top_n is None else latency_top_n
    hotspot_filters = normalize_hotspot_filters(hotspot_statuses, hotspot_methods)
    normalized_facet_fields = normalize_facet_fields(facet_fields)

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            invalid_lines += 1
            continue
        if not matches_time_window(parsed.timestamp, window_start, window_end):
            excluded_requests += 1
            continue
        parsed_lines.append(parsed)

    result = analyze_parsed_lines(
        parsed_lines,
        top_n=top_n,
        latency_limit=latency_limit,
        hotspot_filters=hotspot_filters,
        time_bucket_granularity=time_bucket_granularity,
        normalized_facet_fields=normalized_facet_fields,
    )
    result["invalid_lines"] = invalid_lines
    result["time_window"] = build_time_window_metadata(
        window_start,
        window_end,
        matched_requests=result["total_requests"],
        excluded_requests=excluded_requests,
    )
    result["facet_comparison"] = build_facet_comparison(
        parsed_lines,
        comparison_field=facet_compare_field,
        comparison_values=facet_compare_values,
        top_n=top_n,
        latency_limit=latency_limit,
        hotspot_filters=hotspot_filters,
        time_bucket_granularity=time_bucket_granularity,
    )
    return result


def format_text_report(result: dict) -> str:
    lines = [
        "Log Analysis Summary",
        f"Total requests: {result['total_requests']}",
        f"Invalid lines: {result['invalid_lines']}",
        f"Total bytes sent: {result['total_bytes']}",
        f"Average bytes/request: {result['average_bytes']}",
    ]

    time_window = result["time_window"]
    if time_window:
        lines.extend(
            [
                "Time window:",
                f"  Start: {time_window['start'] or '(open)'}",
                f"  End: {time_window['end'] or '(open)'}",
                f"  Matched requests: {time_window['matched_requests']}",
                f"  Excluded requests: {time_window['excluded_requests']}",
            ]
        )

    time_bucketing = result["time_bucketing"]
    if time_bucketing:
        lines.append(f"Time bucket trends ({time_bucketing['granularity']}):")
        if result["time_buckets"]:
            for bucket in result["time_buckets"]:
                top_path = bucket["top_path"]
                top_path_fragment = (
                    f", top_path={top_path} ({bucket['top_path_count']})"
                    if top_path
                    else ""
                )
                lines.append(
                    "  "
                    f"{bucket['bucket_start']} -> requests={bucket['request_count']}, "
                    f"errors={bucket['error_count']} ({bucket['error_rate_pct']}%)"
                    f"{top_path_fragment}"
                )
                lines.append(
                    "    request latency: "
                    + format_bucket_latency_summary(
                        bucket["latency_sample_count"],
                        bucket["average_latency_ms"],
                        bucket["p95_latency_ms"],
                        bucket["max_latency_ms"],
                    )
                )
                lines.append(
                    "    upstream latency: "
                    + format_bucket_latency_summary(
                        bucket["upstream_latency_sample_count"],
                        bucket["average_upstream_latency_ms"],
                        bucket["p95_upstream_latency_ms"],
                        bucket["max_upstream_latency_ms"],
                    )
                )
        else:
            lines.append("  (none)")

    if result["faceting"] and result["time_bucketing"]:
        lines.append(format_faceting_heading("Time bucket facet breakdowns:", result["faceting"]))
        if result["time_bucket_facet_breakdown"]:
            for bucket in result["time_bucket_facet_breakdown"]:
                top_path = bucket["top_path"]
                top_path_fragment = (
                    f", top_path={top_path} ({bucket['top_path_count']})"
                    if top_path
                    else ""
                )
                lines.append(
                    "  "
                    f"{bucket['bucket_start']} | {bucket['facet_label']} -> "
                    f"requests={bucket['request_count']}, "
                    f"errors={bucket['error_count']} ({bucket['error_rate_pct']}%)"
                    f"{top_path_fragment}"
                )
                lines.append(
                    "    request latency: "
                    + format_bucket_latency_summary(
                        bucket["latency_sample_count"],
                        bucket["average_latency_ms"],
                        bucket["p95_latency_ms"],
                        bucket["max_latency_ms"],
                    )
                )
                lines.append(
                    "    upstream latency: "
                    + format_bucket_latency_summary(
                        bucket["upstream_latency_sample_count"],
                        bucket["average_upstream_latency_ms"],
                        bucket["p95_upstream_latency_ms"],
                        bucket["max_upstream_latency_ms"],
                    )
                )
        else:
            lines.append("  (none)")

    facet_comparison = result["facet_comparison"]
    if facet_comparison:
        left = facet_comparison["left"]
        right = facet_comparison["right"]
        left_summary = left["summary"]
        right_summary = right["summary"]
        delta = facet_comparison["delta"]
        lines.append(
            f"Facet comparison ({facet_comparison['field']}): {left['value']} vs {right['value']} "
            f"(delta: {facet_comparison['delta_direction']})"
        )
        lines.append(
            "  "
            f"{left['label']} -> requests={left_summary['request_count']}, "
            f"errors={left_summary['error_count']} ({left_summary['error_rate_pct']}%), "
            f"avg_latency={format_card_metric_value(left_summary['average_latency_ms'], suffix=' ms')}, "
            f"p95_latency={format_card_metric_value(left_summary['p95_latency_ms'], suffix=' ms')}, "
            f"avg_upstream={format_card_metric_value(left_summary['average_upstream_latency_ms'], suffix=' ms')}, "
            f"p95_upstream={format_card_metric_value(left_summary['p95_upstream_latency_ms'], suffix=' ms')}, "
            f"top_path={left_summary['top_path'] or '(none)'} ({left_summary['top_path_count']})"
        )
        lines.append(
            "  "
            f"{right['label']} -> requests={right_summary['request_count']}, "
            f"errors={right_summary['error_count']} ({right_summary['error_rate_pct']}%), "
            f"avg_latency={format_card_metric_value(right_summary['average_latency_ms'], suffix=' ms')}, "
            f"p95_latency={format_card_metric_value(right_summary['p95_latency_ms'], suffix=' ms')}, "
            f"avg_upstream={format_card_metric_value(right_summary['average_upstream_latency_ms'], suffix=' ms')}, "
            f"p95_upstream={format_card_metric_value(right_summary['p95_upstream_latency_ms'], suffix=' ms')}, "
            f"top_path={right_summary['top_path'] or '(none)'} ({right_summary['top_path_count']})"
        )
        lines.append(
            "  "
            f"delta -> requests={delta['request_count_delta']}, "
            f"errors={delta['error_count_delta']}, "
            f"error_rate={format_card_metric_value(delta['error_rate_pct_delta'], suffix=' pp')}, "
            f"avg_latency={format_card_metric_value(delta['average_latency_ms_delta'], suffix=' ms')}, "
            f"p95_latency={format_card_metric_value(delta['p95_latency_ms_delta'], suffix=' ms')}, "
            f"avg_upstream={format_card_metric_value(delta['average_upstream_latency_ms_delta'], suffix=' ms')}, "
            f"p95_upstream={format_card_metric_value(delta['p95_upstream_latency_ms_delta'], suffix=' ms')}"
        )
        if facet_comparison["time_bucketing"]:
            lines.append(
                f"Facet comparison buckets ({facet_comparison['time_bucketing']['granularity']}):"
            )
            if facet_comparison["time_buckets"]:
                for bucket in facet_comparison["time_buckets"]:
                    lines.append(
                        "  "
                        f"{bucket['bucket_start']} -> "
                        f"{left['value']}: requests={bucket['left_request_count']}, error_rate={bucket['left_error_rate_pct']}%, avg_latency={format_card_metric_value(bucket['left_average_latency_ms'], suffix=' ms')} | "
                        f"{right['value']}: requests={bucket['right_request_count']}, error_rate={bucket['right_error_rate_pct']}%, avg_latency={format_card_metric_value(bucket['right_average_latency_ms'], suffix=' ms')} | "
                        f"delta requests={bucket['request_count_delta']}, error_rate={format_card_metric_value(bucket['error_rate_pct_delta'], suffix=' pp')}, avg_latency={format_card_metric_value(bucket['average_latency_ms_delta'], suffix=' ms')}"
                    )
            else:
                lines.append("  (none)")

    lines.append("Status counts:")

    if result["status_counts"]:
        for status, count in sorted(result["status_counts"].items()):
            lines.append(f"  {status}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Method counts:")
    if result["method_counts"]:
        for method, count in sorted(result["method_counts"].items()):
            lines.append(f"  {method}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Top IPs:")
    if result["top_ips"]:
        for ip, count in result["top_ips"]:
            lines.append(f"  {ip}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Top paths:")
    if result["top_paths"]:
        for path, count in result["top_paths"]:
            lines.append(f"  {path}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Top referrers:")
    if result["top_referrers"]:
        for referrer, count in result["top_referrers"]:
            lines.append(f"  {referrer}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Top user agents:")
    if result["top_user_agents"]:
        for user_agent, count in result["top_user_agents"]:
            lines.append(f"  {user_agent}: {count}")
    else:
        lines.append("  (none)")

    lines.append("Latency summary (ms):")
    latency_summary = result["latency_summary"]
    if latency_summary:
        lines.append(f"  Count: {latency_summary['count']}")
        lines.append(f"  Average: {latency_summary['average_ms']}")
        lines.append(f"  p50: {latency_summary['p50_ms']}")
        lines.append(f"  p95: {latency_summary['p95_ms']}")
        lines.append(f"  p99: {latency_summary['p99_ms']}")
        lines.append(f"  Max: {latency_summary['max_ms']}")
    else:
        lines.append("  (none)")

    lines.append("Upstream latency summary (ms):")
    upstream_latency_summary = result["upstream_latency_summary"]
    if upstream_latency_summary:
        lines.append(f"  Count: {upstream_latency_summary['count']}")
        lines.append(f"  Average: {upstream_latency_summary['average_ms']}")
        lines.append(f"  p50: {upstream_latency_summary['p50_ms']}")
        lines.append(f"  p95: {upstream_latency_summary['p95_ms']}")
        lines.append(f"  p99: {upstream_latency_summary['p99_ms']}")
        lines.append(f"  Max: {upstream_latency_summary['max_ms']}")
    else:
        lines.append("  (none)")

    lines.append(format_hotspot_heading("Per-path latency hotspots (ms):", result["hotspot_filters"]))
    if result["path_latency_breakdown"]:
        for row in result["path_latency_breakdown"]:
            lines.append(
                "  "
                f"{row['path']}: count={row['count']}, avg={row['average_ms']}, "
                f"p95={row['p95_ms']}, max={row['max_ms']}"
            )
    else:
        lines.append("  (none)")

    if result["faceting"]:
        lines.append(
            format_faceting_heading(
                format_hotspot_heading(
                    "Per-path latency hotspots by facet (ms):",
                    result["hotspot_filters"],
                ),
                result["faceting"],
            )
        )
        if result["path_latency_facet_breakdown"]:
            for row in result["path_latency_facet_breakdown"]:
                lines.append(
                    "  "
                    f"{row['path']} | {row['facet_label']}: count={row['count']}, "
                    f"avg={row['average_ms']}, p95={row['p95_ms']}, max={row['max_ms']}"
                )
        else:
            lines.append("  (none)")

    lines.append(
        format_hotspot_heading(
            "Per-path upstream latency hotspots (ms):", result["hotspot_filters"]
        )
    )
    if result["upstream_path_latency_breakdown"]:
        for row in result["upstream_path_latency_breakdown"]:
            lines.append(
                "  "
                f"{row['path']}: count={row['count']}, avg={row['average_ms']}, "
                f"p95={row['p95_ms']}, max={row['max_ms']}"
            )
    else:
        lines.append("  (none)")

    if result["faceting"]:
        lines.append(
            format_faceting_heading(
                format_hotspot_heading(
                    "Per-path upstream latency hotspots by facet (ms):",
                    result["hotspot_filters"],
                ),
                result["faceting"],
            )
        )
        if result["upstream_path_latency_facet_breakdown"]:
            for row in result["upstream_path_latency_facet_breakdown"]:
                lines.append(
                    "  "
                    f"{row['path']} | {row['facet_label']}: count={row['count']}, "
                    f"avg={row['average_ms']}, p95={row['p95_ms']}, max={row['max_ms']}"
                )
        else:
            lines.append("  (none)")

    return "\n".join(lines)


def ensure_parent_directory(destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_summary_csv(destination: str | Path, result: dict) -> None:
    rows: list[dict[str, str | int | float]] = [
        {"section": "summary", "metric": "total_requests", "value": result["total_requests"]},
        {"section": "summary", "metric": "invalid_lines", "value": result["invalid_lines"]},
        {"section": "summary", "metric": "total_bytes", "value": result["total_bytes"]},
        {"section": "summary", "metric": "average_bytes", "value": result["average_bytes"]},
    ]

    if result["time_window"]:
        rows.extend(
            [
                {
                    "section": "summary",
                    "metric": "time_window_start",
                    "value": result["time_window"]["start"],
                },
                {
                    "section": "summary",
                    "metric": "time_window_end",
                    "value": result["time_window"]["end"],
                },
                {
                    "section": "summary",
                    "metric": "time_window_matched_requests",
                    "value": result["time_window"]["matched_requests"],
                },
                {
                    "section": "summary",
                    "metric": "time_window_excluded_requests",
                    "value": result["time_window"]["excluded_requests"],
                },
            ]
        )

    if result["time_bucketing"]:
        rows.extend(
            [
                {
                    "section": "summary",
                    "metric": "time_bucket_granularity",
                    "value": result["time_bucketing"]["granularity"],
                },
                {
                    "section": "summary",
                    "metric": "time_bucket_count",
                    "value": result["time_bucketing"]["bucket_count"],
                },
            ]
        )

    if result["faceting"]:
        rows.extend(
            [
                {
                    "section": "summary",
                    "metric": "facet_fields",
                    "value": "|".join(result["faceting"]["fields"]),
                },
                {
                    "section": "summary",
                    "metric": "missing_facet_value",
                    "value": result["faceting"]["missing_value"],
                },
                {
                    "section": "summary",
                    "metric": "path_latency_facet_row_count",
                    "value": len(result["path_latency_facet_breakdown"]),
                },
                {
                    "section": "summary",
                    "metric": "upstream_path_latency_facet_row_count",
                    "value": len(result["upstream_path_latency_facet_breakdown"]),
                },
            ]
        )
        if result["time_bucketing"]:
            rows.append(
                {
                    "section": "summary",
                    "metric": "time_bucket_facet_row_count",
                    "value": len(result["time_bucket_facet_breakdown"]),
                }
            )

    if result["facet_comparison"]:
        rows.extend(
            [
                {
                    "section": "summary",
                    "metric": "facet_compare_field",
                    "value": result["facet_comparison"]["field"],
                },
                {
                    "section": "summary",
                    "metric": "facet_compare_left_value",
                    "value": result["facet_comparison"]["left"]["value"],
                },
                {
                    "section": "summary",
                    "metric": "facet_compare_right_value",
                    "value": result["facet_comparison"]["right"]["value"],
                },
                {
                    "section": "summary",
                    "metric": "facet_compare_delta_direction",
                    "value": result["facet_comparison"]["delta_direction"],
                },
                {
                    "section": "summary",
                    "metric": "facet_compare_bucket_count",
                    "value": len(result["facet_comparison"]["time_buckets"]),
                },
            ]
        )

    for status, count in sorted(result["status_counts"].items()):
        rows.append({"section": "status_counts", "key": status, "count": count})
    for method, count in sorted(result["method_counts"].items()):
        rows.append({"section": "method_counts", "key": method, "count": count})

    for section_name, entries in (
        ("top_ips", result["top_ips"]),
        ("top_paths", result["top_paths"]),
        ("top_referrers", result["top_referrers"]),
        ("top_user_agents", result["top_user_agents"]),
    ):
        for rank, (key, count) in enumerate(entries, start=1):
            rows.append(
                {
                    "section": section_name,
                    "rank": rank,
                    "key": key,
                    "count": count,
                }
            )

    for section_name, summary in (
        ("latency_summary", result["latency_summary"]),
        ("upstream_latency_summary", result["upstream_latency_summary"]),
    ):
        if summary:
            for metric, value in summary.items():
                rows.append({"section": section_name, "metric": metric, "value": value})

    fieldnames = ["section", "metric", "key", "rank", "count", "value"]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_path_latency_csv(
    destination: str | Path,
    rows: list[dict],
    hotspot_filters: dict[str, list[str]] | None = None,
    time_window: dict[str, str | int] | None = None,
) -> None:
    fieldnames = [
        "path",
        "count",
        "average_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "max_ms",
        "status_filter",
        "method_filter",
        "window_start",
        "window_end",
    ]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "status_filter": "|".join(hotspot_filters["statuses"])
                    if hotspot_filters
                    else "",
                    "method_filter": "|".join(hotspot_filters["methods"])
                    if hotspot_filters
                    else "",
                    "window_start": str(time_window["start"]) if time_window else "",
                    "window_end": str(time_window["end"]) if time_window else "",
                }
            )


def write_path_latency_facet_csv(
    destination: str | Path,
    rows: list[dict],
    facet_fields: list[str],
    hotspot_filters: dict[str, list[str]] | None = None,
    time_window: dict[str, str | int] | None = None,
) -> None:
    facet_fieldnames = [f"facet_{field_name}" for field_name in facet_fields]
    fieldnames = [
        "path",
        "facet_label",
        *facet_fieldnames,
        "count",
        "average_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "max_ms",
        "status_filter",
        "method_filter",
        "window_start",
        "window_end",
    ]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            combined_row = {
                **row,
                "status_filter": "|".join(hotspot_filters["statuses"])
                if hotspot_filters
                else "",
                "method_filter": "|".join(hotspot_filters["methods"])
                if hotspot_filters
                else "",
                "window_start": str(time_window["start"]) if time_window else "",
                "window_end": str(time_window["end"]) if time_window else "",
            }
            for field_name in facet_fields:
                combined_row[f"facet_{field_name}"] = row["facets"].get(field_name, "")
            writer.writerow(
                {
                    field: "" if combined_row.get(field) is None else combined_row.get(field, "")
                    for field in fieldnames
                }
            )


def write_time_bucket_csv(
    destination: str | Path,
    rows: list[dict],
    time_bucketing: dict[str, str | int] | None = None,
    time_window: dict[str, str | int] | None = None,
) -> None:
    fieldnames = [
        "granularity",
        "bucket_start",
        "bucket_end",
        "request_count",
        "error_count",
        "error_rate_pct",
        "top_path",
        "top_path_count",
        "latency_sample_count",
        "average_latency_ms",
        "p95_latency_ms",
        "max_latency_ms",
        "upstream_latency_sample_count",
        "average_upstream_latency_ms",
        "p95_upstream_latency_ms",
        "max_upstream_latency_ms",
        "window_start",
        "window_end",
    ]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            combined_row = {
                "granularity": time_bucketing["granularity"] if time_bucketing else "",
                "window_start": str(time_window["start"]) if time_window else "",
                "window_end": str(time_window["end"]) if time_window else "",
                **row,
            }
            writer.writerow(
                {
                    field: "" if combined_row.get(field) is None else combined_row.get(field, "")
                    for field in fieldnames
                }
            )


def write_time_bucket_facet_csv(
    destination: str | Path,
    rows: list[dict],
    facet_fields: list[str],
    time_bucketing: dict[str, str | int] | None = None,
    time_window: dict[str, str | int] | None = None,
) -> None:
    facet_fieldnames = [f"facet_{field_name}" for field_name in facet_fields]
    fieldnames = [
        "granularity",
        "bucket_start",
        "bucket_end",
        "facet_label",
        *facet_fieldnames,
        "request_count",
        "error_count",
        "error_rate_pct",
        "top_path",
        "top_path_count",
        "latency_sample_count",
        "average_latency_ms",
        "p95_latency_ms",
        "max_latency_ms",
        "upstream_latency_sample_count",
        "average_upstream_latency_ms",
        "p95_upstream_latency_ms",
        "max_upstream_latency_ms",
        "window_start",
        "window_end",
    ]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            combined_row = {
                "granularity": time_bucketing["granularity"] if time_bucketing else "",
                "window_start": str(time_window["start"]) if time_window else "",
                "window_end": str(time_window["end"]) if time_window else "",
                **row,
            }
            for field_name in facet_fields:
                combined_row[f"facet_{field_name}"] = row["facets"].get(field_name, "")
            writer.writerow(
                {
                    field: "" if combined_row.get(field) is None else combined_row.get(field, "")
                    for field in fieldnames
                }
            )


def write_facet_comparison_csv(destination: str | Path, comparison: dict[str, object]) -> None:
    fieldnames = [
        "row_type",
        "comparison_field",
        "left_value",
        "right_value",
        "delta_direction",
        "granularity",
        "bucket_start",
        "bucket_end",
        "left_request_count",
        "right_request_count",
        "request_count_delta",
        "left_error_count",
        "right_error_count",
        "error_count_delta",
        "left_error_rate_pct",
        "right_error_rate_pct",
        "error_rate_pct_delta",
        "left_average_latency_ms",
        "right_average_latency_ms",
        "average_latency_ms_delta",
        "left_p95_latency_ms",
        "right_p95_latency_ms",
        "p95_latency_ms_delta",
        "left_max_latency_ms",
        "right_max_latency_ms",
        "max_latency_ms_delta",
        "left_average_upstream_latency_ms",
        "right_average_upstream_latency_ms",
        "average_upstream_latency_ms_delta",
        "left_p95_upstream_latency_ms",
        "right_p95_upstream_latency_ms",
        "p95_upstream_latency_ms_delta",
        "left_max_upstream_latency_ms",
        "right_max_upstream_latency_ms",
        "max_upstream_latency_ms_delta",
        "left_top_path",
        "right_top_path",
        "left_top_path_count",
        "right_top_path_count",
    ]
    destination_path = ensure_parent_directory(destination)
    left = comparison["left"]
    right = comparison["right"]
    left_summary = left["summary"]
    right_summary = right["summary"]
    delta = comparison["delta"]
    granularity = ""
    if comparison["time_bucketing"]:
        granularity = str(comparison["time_bucketing"]["granularity"])

    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "row_type": "summary",
                "comparison_field": comparison["field"],
                "left_value": left["value"],
                "right_value": right["value"],
                "delta_direction": comparison["delta_direction"],
                "granularity": granularity,
                "left_request_count": left_summary["request_count"],
                "right_request_count": right_summary["request_count"],
                "request_count_delta": delta["request_count_delta"],
                "left_error_count": left_summary["error_count"],
                "right_error_count": right_summary["error_count"],
                "error_count_delta": delta["error_count_delta"],
                "left_error_rate_pct": left_summary["error_rate_pct"],
                "right_error_rate_pct": right_summary["error_rate_pct"],
                "error_rate_pct_delta": delta["error_rate_pct_delta"],
                "left_average_latency_ms": left_summary["average_latency_ms"],
                "right_average_latency_ms": right_summary["average_latency_ms"],
                "average_latency_ms_delta": delta["average_latency_ms_delta"],
                "left_p95_latency_ms": left_summary["p95_latency_ms"],
                "right_p95_latency_ms": right_summary["p95_latency_ms"],
                "p95_latency_ms_delta": delta["p95_latency_ms_delta"],
                "left_max_latency_ms": left_summary["max_latency_ms"],
                "right_max_latency_ms": right_summary["max_latency_ms"],
                "max_latency_ms_delta": delta["max_latency_ms_delta"],
                "left_average_upstream_latency_ms": left_summary["average_upstream_latency_ms"],
                "right_average_upstream_latency_ms": right_summary["average_upstream_latency_ms"],
                "average_upstream_latency_ms_delta": delta["average_upstream_latency_ms_delta"],
                "left_p95_upstream_latency_ms": left_summary["p95_upstream_latency_ms"],
                "right_p95_upstream_latency_ms": right_summary["p95_upstream_latency_ms"],
                "p95_upstream_latency_ms_delta": delta["p95_upstream_latency_ms_delta"],
                "left_max_upstream_latency_ms": left_summary["max_upstream_latency_ms"],
                "right_max_upstream_latency_ms": right_summary["max_upstream_latency_ms"],
                "max_upstream_latency_ms_delta": delta["max_upstream_latency_ms_delta"],
                "left_top_path": left_summary["top_path"],
                "right_top_path": right_summary["top_path"],
                "left_top_path_count": left_summary["top_path_count"],
                "right_top_path_count": right_summary["top_path_count"],
            }
        )
        for row in comparison["time_buckets"]:
            writer.writerow(
                {
                    "row_type": "bucket",
                    "comparison_field": comparison["field"],
                    "left_value": left["value"],
                    "right_value": right["value"],
                    "delta_direction": comparison["delta_direction"],
                    "granularity": granularity,
                    **row,
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze common, combined, and latency-augmented web access logs"
    )
    parser.add_argument("logfile", help="Path to an access log file")
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of top entries to show per ranked category",
    )
    parser.add_argument(
        "--latency-paths",
        type=int,
        default=None,
        help="Number of per-path latency rows to include (defaults to --top)",
    )
    parser.add_argument(
        "--summary-csv",
        help="Optional path for a spreadsheet-friendly summary CSV export",
    )
    parser.add_argument(
        "--path-latency-csv",
        help="Optional path for a per-path request-latency breakdown CSV export",
    )
    parser.add_argument(
        "--path-latency-facet-csv",
        help=(
            "Optional path for a per-path request-latency breakdown split by selected "
            "--facet-field values"
        ),
    )
    parser.add_argument(
        "--upstream-path-latency-csv",
        help="Optional path for a per-path upstream-latency breakdown CSV export",
    )
    parser.add_argument(
        "--upstream-path-latency-facet-csv",
        help=(
            "Optional path for a per-path upstream-latency breakdown split by selected "
            "--facet-field values"
        ),
    )
    parser.add_argument(
        "--time-bucket",
        choices=TIME_BUCKET_GRANULARITIES,
        help=(
            "Optional time-series bucketing granularity for matched requests "
            "(minute or hour)"
        ),
    )
    parser.add_argument(
        "--time-bucket-csv",
        help="Optional path for a time-bucket trend CSV export (requires --time-bucket)",
    )
    parser.add_argument(
        "--time-bucket-facet-csv",
        help=(
            "Optional path for a time-bucket trend CSV split by selected --facet-field "
            "values (requires --time-bucket)"
        ),
    )
    parser.add_argument(
        "--time-bucket-card-svg",
        help=(
            "Optional path for a standalone SVG mini trend card rendered from the active "
            "time buckets (requires --time-bucket)"
        ),
    )
    parser.add_argument(
        "--time-bucket-card-html",
        help=(
            "Optional path for a self-contained HTML mini trend card rendered from the "
            "active time buckets (requires --time-bucket)"
        ),
    )
    parser.add_argument(
        "--card-annotation",
        action="append",
        default=[],
        help=(
            "Optional TIMESTAMP=LABEL or TIMESTAMP=THEME|LABEL callout pinned onto matching "
            "card-export buckets (repeatable; themes include deploy, rollback, incident, "
            "recovery, and note; requires --time-bucket and at least one card export flag)"
        ),
    )
    parser.add_argument(
        "--hotspot-status",
        action="append",
        default=[],
        help=(
            "Restrict per-path hotspot breakdowns/CSV exports to matching status codes "
            "(repeatable, e.g. --hotspot-status 500 --hotspot-status 502)"
        ),
    )
    parser.add_argument(
        "--hotspot-method",
        action="append",
        default=[],
        help=(
            "Restrict per-path hotspot breakdowns/CSV exports to matching HTTP methods "
            "(repeatable, e.g. --hotspot-method POST)"
        ),
    )
    parser.add_argument(
        "--facet-field",
        action="append",
        default=[],
        help=(
            "Named log field to surface as a deployment/environment facet in dedicated "
            "breakdowns and exports (repeatable, e.g. --facet-field env --facet-field region)"
        ),
    )
    parser.add_argument(
        "--facet-compare-field",
        help=(
            "Named log field to compare between two values side by side for release reviews "
            "(for example env or release)"
        ),
    )
    parser.add_argument(
        "--facet-compare-values",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help=(
            "Exactly two facet values to compare side by side (for example prod staging)"
        ),
    )
    parser.add_argument(
        "--facet-compare-csv",
        help=(
            "Optional path for a side-by-side facet comparison CSV with summary and aligned "
            "bucket deltas (requires --facet-compare-field and --facet-compare-values)"
        ),
    )
    parser.add_argument(
        "--facet-compare-card-svg",
        help=(
            "Optional path for a standalone SVG comparison card rendered from "
            "--facet-compare-* output (requires --facet-compare-field and "
            "--facet-compare-values)"
        ),
    )
    parser.add_argument(
        "--facet-compare-card-html",
        help=(
            "Optional path for a self-contained HTML comparison card rendered from "
            "--facet-compare-* output (requires --facet-compare-field and "
            "--facet-compare-values)"
        ),
    )
    parser.add_argument(
        "--window-start",
        help=(
            "Inclusive lower time bound for log entries (ISO-8601 or common-log timestamp; "
            'naive ISO values are treated as UTC, for example 2026-04-18T09:00:00Z, '
            '2026-04-18T09:00:00, or "18/Apr/2026:09:00:00 +0000")'
        ),
    )
    parser.add_argument(
        "--window-end",
        help=(
            "Inclusive upper time bound for log entries (ISO-8601 or common-log timestamp; "
            'naive ISO values are treated as UTC, for example 2026-04-18T10:00:00Z, '
            '2026-04-18T10:00:00, or "18/Apr/2026:10:00:00 +0000")'
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.top <= 0:
        parser.error("--top must be greater than 0")
    if args.latency_paths is not None and args.latency_paths <= 0:
        parser.error("--latency-paths must be greater than 0")
    invalid_status_filters = [status for status in args.hotspot_status if not STATUS_CODE_RE.match(status)]
    if invalid_status_filters:
        parser.error(
            "--hotspot-status must be a 3-digit status code "
            f"(received: {', '.join(invalid_status_filters)})"
        )
    if any(not method.strip() for method in args.hotspot_method):
        parser.error("--hotspot-method must not be blank")
    if any(not field_name.strip() for field_name in args.facet_field):
        parser.error("--facet-field must not be blank")
    invalid_facet_fields = [
        field_name for field_name in args.facet_field if not FIELD_NAME_RE.match(field_name.strip())
    ]
    if invalid_facet_fields:
        parser.error(
            "--facet-field must look like a named log field "
            f"(letters/numbers/underscore only; received: {', '.join(invalid_facet_fields)})"
        )
    normalized_facet_compare_field = None
    if args.facet_compare_field is not None:
        normalized_facet_compare_field = args.facet_compare_field.strip()
        if not normalized_facet_compare_field:
            parser.error("--facet-compare-field must not be blank")
        if not FIELD_NAME_RE.match(normalized_facet_compare_field):
            parser.error(
                "--facet-compare-field must look like a named log field "
                f"(letters/numbers/underscore only; received: {args.facet_compare_field})"
            )
    normalized_facet_compare_values = None
    if args.facet_compare_values is not None:
        normalized_facet_compare_values = tuple(value.strip() for value in args.facet_compare_values)
        if any(not value for value in normalized_facet_compare_values):
            parser.error("--facet-compare-values must not contain blank values")
        if normalized_facet_compare_values[0] == normalized_facet_compare_values[1]:
            parser.error("--facet-compare-values must contain two distinct values")
    if args.facet_compare_csv and (
        normalized_facet_compare_field is None or normalized_facet_compare_values is None
    ):
        parser.error(
            "--facet-compare-csv requires --facet-compare-field and --facet-compare-values"
        )
    if (args.facet_compare_card_svg or args.facet_compare_card_html) and (
        normalized_facet_compare_field is None or normalized_facet_compare_values is None
    ):
        parser.error(
            "comparison-card export flags require --facet-compare-field and --facet-compare-values"
        )
    if (normalized_facet_compare_field is None) != (normalized_facet_compare_values is None):
        parser.error(
            "--facet-compare-field and --facet-compare-values must be provided together"
        )
    if args.time_bucket_csv and not args.time_bucket:
        parser.error("--time-bucket-csv requires --time-bucket")
    if args.time_bucket_facet_csv and not args.time_bucket:
        parser.error("--time-bucket-facet-csv requires --time-bucket")
    if args.time_bucket_card_svg and not args.time_bucket:
        parser.error("--time-bucket-card-svg requires --time-bucket")
    if args.time_bucket_card_html and not args.time_bucket:
        parser.error("--time-bucket-card-html requires --time-bucket")
    has_card_exports = any(
        [
            args.time_bucket_card_svg,
            args.time_bucket_card_html,
            args.facet_compare_card_svg,
            args.facet_compare_card_html,
        ]
    )
    if args.card_annotation and not args.time_bucket:
        parser.error("--card-annotation requires --time-bucket")
    if args.card_annotation and not has_card_exports:
        parser.error("--card-annotation requires at least one card export flag")

    normalized_facet_fields = normalize_facet_fields(args.facet_field)
    facet_export_flags = [
        args.path_latency_facet_csv,
        args.upstream_path_latency_facet_csv,
        args.time_bucket_facet_csv,
    ]
    if any(facet_export_flags) and not normalized_facet_fields:
        parser.error(
            "facet-specific export flags require at least one --facet-field"
        )

    window_start = None
    if args.window_start:
        window_start = parse_cli_datetime(args.window_start)
        if window_start is None:
            parser.error(
                "--window-start must be ISO-8601 or a common-log timestamp "
                "(naive ISO values are treated as UTC)"
            )

    window_end = None
    if args.window_end:
        window_end = parse_cli_datetime(args.window_end)
        if window_end is None:
            parser.error(
                "--window-end must be ISO-8601 or a common-log timestamp "
                "(naive ISO values are treated as UTC)"
            )

    if window_start and window_end and window_start > window_end:
        parser.error("--window-start must be less than or equal to --window-end")

    latency_top_n = args.top if args.latency_paths is None else args.latency_paths

    with open(args.logfile, encoding="utf-8") as handle:
        result = analyze_lines(
            handle,
            top_n=args.top,
            latency_top_n=latency_top_n,
            hotspot_statuses=args.hotspot_status,
            hotspot_methods=args.hotspot_method,
            window_start=window_start,
            window_end=window_end,
            time_bucket_granularity=args.time_bucket,
            facet_fields=normalized_facet_fields,
            facet_compare_field=normalized_facet_compare_field,
            facet_compare_values=normalized_facet_compare_values,
        )

    trend_card_annotations = None
    comparison_card_annotations = None
    if args.card_annotation and (args.time_bucket_card_svg or args.time_bucket_card_html):
        trend_card_annotations = normalize_card_annotations(
            args.card_annotation,
            time_buckets=result["time_buckets"],
        )
    if args.card_annotation and (args.facet_compare_card_svg or args.facet_compare_card_html):
        comparison_card_annotations = normalize_card_annotations(
            args.card_annotation,
            time_buckets=result["facet_comparison"]["time_buckets"],
        )

    if args.summary_csv:
        write_summary_csv(args.summary_csv, result)
    if args.path_latency_csv:
        write_path_latency_csv(
            args.path_latency_csv,
            result["path_latency_breakdown"],
            result["hotspot_filters"],
            result["time_window"],
        )
    if args.path_latency_facet_csv:
        write_path_latency_facet_csv(
            args.path_latency_facet_csv,
            result["path_latency_facet_breakdown"],
            normalized_facet_fields,
            result["hotspot_filters"],
            result["time_window"],
        )
    if args.upstream_path_latency_csv:
        write_path_latency_csv(
            args.upstream_path_latency_csv,
            result["upstream_path_latency_breakdown"],
            result["hotspot_filters"],
            result["time_window"],
        )
    if args.upstream_path_latency_facet_csv:
        write_path_latency_facet_csv(
            args.upstream_path_latency_facet_csv,
            result["upstream_path_latency_facet_breakdown"],
            normalized_facet_fields,
            result["hotspot_filters"],
            result["time_window"],
        )
    if args.time_bucket_csv:
        write_time_bucket_csv(
            args.time_bucket_csv,
            result["time_buckets"],
            result["time_bucketing"],
            result["time_window"],
        )
    if args.time_bucket_facet_csv:
        write_time_bucket_facet_csv(
            args.time_bucket_facet_csv,
            result["time_bucket_facet_breakdown"],
            normalized_facet_fields,
            result["time_bucketing"],
            result["time_window"],
        )
    if args.facet_compare_csv and result["facet_comparison"]:
        write_facet_comparison_csv(
            args.facet_compare_csv,
            result["facet_comparison"],
        )
    if args.facet_compare_card_svg and result["facet_comparison"]:
        write_text_output(
            args.facet_compare_card_svg,
            format_facet_comparison_card_svg(
                result["facet_comparison"],
                source_label=Path(args.logfile).name,
                time_window=result["time_window"],
                annotations=comparison_card_annotations,
            ),
        )
    if args.facet_compare_card_html and result["facet_comparison"]:
        write_text_output(
            args.facet_compare_card_html,
            format_facet_comparison_card_html(
                result["facet_comparison"],
                source_label=Path(args.logfile).name,
                time_window=result["time_window"],
                annotations=comparison_card_annotations,
            ),
        )
    if args.time_bucket_card_svg:
        write_text_output(
            args.time_bucket_card_svg,
            format_time_bucket_card_svg(
                result,
                source_label=Path(args.logfile).name,
                annotations=trend_card_annotations,
            ),
        )
    if args.time_bucket_card_html:
        write_text_output(
            args.time_bucket_card_html,
            format_time_bucket_card_html(
                result,
                source_label=Path(args.logfile).name,
                annotations=trend_card_annotations,
            ),
        )

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
