from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>[^ ]+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)$'
)


@dataclass(frozen=True)
class ParsedLogLine:
    ip: str
    method: str
    path: str
    status: str
    bytes_sent: int


def parse_line(line: str) -> ParsedLogLine | None:
    match = LOG_RE.match(line.strip())
    if not match:
        return None

    bytes_raw = match.group("bytes")
    return ParsedLogLine(
        ip=match.group("ip"),
        method=match.group("method"),
        path=match.group("path"),
        status=match.group("status"),
        bytes_sent=0 if bytes_raw == "-" else int(bytes_raw),
    )


def analyze_lines(lines: Iterable[str], top_n: int = 3) -> dict:
    status_counts = Counter()
    ip_counts = Counter()
    path_counts = Counter()
    method_counts = Counter()
    total_bytes = 0
    total_requests = 0
    invalid_lines = 0

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

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze common web access logs")
    parser.add_argument("logfile", help="Path to an access log file")
    parser.add_argument("--top", type=int, default=3, help="Number of top IPs/paths to show")
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

    with open(args.logfile, encoding="utf-8") as handle:
        result = analyze_lines(handle, top_n=args.top)

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
