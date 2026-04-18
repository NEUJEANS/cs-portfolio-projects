from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>[^ ]+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)'  # common log tail
    r'(?: "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)")?'  # combined log tail
    r'(?P<extra>(?: .+)?)$'  # optional latency token or named timing fields
)

NAMED_FIELD_START_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
NAMED_TIMING_SPLIT_RE = re.compile(r'\s*[,:]\s*')


@dataclass(frozen=True)
class ParsedLogLine:
    ip: str
    method: str
    path: str
    status: str
    bytes_sent: int
    referrer: str | None = None
    user_agent: str | None = None
    latency_ms: float | None = None
    request_time_ms: float | None = None
    upstream_response_time_ms: float | None = None


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
        method=match.group("method"),
        path=match.group("path"),
        status=match.group("status"),
        bytes_sent=0 if bytes_raw == "-" else int(bytes_raw),
        referrer=None if referrer in (None, "-") else referrer,
        user_agent=None if user_agent in (None, "-") else user_agent,
        latency_ms=primary_latency_ms,
        request_time_ms=request_time_ms,
        upstream_response_time_ms=upstream_response_time_ms,
    )


def analyze_lines(lines: Iterable[str], top_n: int = 3, latency_top_n: int | None = None) -> dict:
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
    total_bytes = 0
    total_requests = 0
    invalid_lines = 0

    latency_limit = top_n if latency_top_n is None else latency_top_n

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            invalid_lines += 1
            continue

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
            path_latencies[parsed.path].append(parsed.latency_ms)
        if parsed.upstream_response_time_ms is not None:
            upstream_latencies_ms.append(parsed.upstream_response_time_ms)
            upstream_path_latencies[parsed.path].append(parsed.upstream_response_time_ms)

    average_bytes = round(total_bytes / total_requests, 2) if total_requests else 0.0
    return {
        "total_requests": total_requests,
        "invalid_lines": invalid_lines,
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
        "path_latency_breakdown": summarize_path_latencies(path_latencies, latency_limit),
        "upstream_path_latency_breakdown": summarize_path_latencies(
            upstream_path_latencies, latency_limit
        ),
    }


def format_text_report(result: dict) -> str:
    lines = [
        "Log Analysis Summary",
        f"Total requests: {result['total_requests']}",
        f"Invalid lines: {result['invalid_lines']}",
        f"Total bytes sent: {result['total_bytes']}",
        f"Average bytes/request: {result['average_bytes']}",
        "Status counts:",
    ]

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

    lines.append("Per-path latency hotspots (ms):")
    if result["path_latency_breakdown"]:
        for row in result["path_latency_breakdown"]:
            lines.append(
                "  "
                f"{row['path']}: count={row['count']}, avg={row['average_ms']}, "
                f"p95={row['p95_ms']}, max={row['max_ms']}"
            )
    else:
        lines.append("  (none)")

    lines.append("Per-path upstream latency hotspots (ms):")
    if result["upstream_path_latency_breakdown"]:
        for row in result["upstream_path_latency_breakdown"]:
            lines.append(
                "  "
                f"{row['path']}: count={row['count']}, avg={row['average_ms']}, "
                f"p95={row['p95_ms']}, max={row['max_ms']}"
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


def write_path_latency_csv(destination: str | Path, rows: list[dict]) -> None:
    fieldnames = ["path", "count", "average_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms"]
    destination_path = ensure_parent_directory(destination)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
        "--upstream-path-latency-csv",
        help="Optional path for a per-path upstream-latency breakdown CSV export",
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

    latency_top_n = args.top if args.latency_paths is None else args.latency_paths

    with open(args.logfile, encoding="utf-8") as handle:
        result = analyze_lines(handle, top_n=args.top, latency_top_n=latency_top_n)

    if args.summary_csv:
        write_summary_csv(args.summary_csv, result)
    if args.path_latency_csv:
        write_path_latency_csv(args.path_latency_csv, result["path_latency_breakdown"])
    if args.upstream_path_latency_csv:
        write_path_latency_csv(
            args.upstream_path_latency_csv,
            result["upstream_path_latency_breakdown"],
        )

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
