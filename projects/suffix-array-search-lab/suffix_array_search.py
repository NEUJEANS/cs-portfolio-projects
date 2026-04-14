#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class SearchHit:
    position: int
    line: int
    context: str
    match: str


class SuffixArrayIndex:
    def __init__(self, text: str, suffix_array: list[int]):
        self.text = text
        self.suffix_array = suffix_array
        self.line_starts = self._compute_line_starts(text)

    @staticmethod
    def _compute_line_starts(text: str) -> list[int]:
        starts = [0]
        for idx, char in enumerate(text):
            if char == "\n" and idx + 1 < len(text):
                starts.append(idx + 1)
        return starts

    @classmethod
    def build(cls, text: str) -> "SuffixArrayIndex":
        suffix_array = sorted(range(len(text)), key=lambda idx: text[idx:]) if text else []
        return cls(text, suffix_array)

    def save(self, output_path: str | Path) -> None:
        payload = {"text": self.text, "suffix_array": self.suffix_array}
        Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, input_path: str | Path) -> "SuffixArrayIndex":
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        return cls(payload["text"], [int(value) for value in payload["suffix_array"]])

    def _prefix_at(self, suffix_index: int, prefix_len: int) -> str:
        start = self.suffix_array[suffix_index]
        return self.text[start : start + prefix_len]

    def _lower_bound(self, pattern: str) -> int:
        lo, hi = 0, len(self.suffix_array)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._prefix_at(mid, len(pattern)) < pattern:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _upper_bound(self, pattern: str) -> int:
        lo, hi = 0, len(self.suffix_array)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._prefix_at(mid, len(pattern)) <= pattern:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def find_positions(self, pattern: str) -> list[int]:
        if not pattern:
            raise ValueError("pattern must not be empty")
        start = self._lower_bound(pattern)
        end = self._upper_bound(pattern)
        matches = [self.suffix_array[idx] for idx in range(start, end)]
        return sorted(matches)

    def line_number_for(self, position: int) -> int:
        return bisect.bisect_right(self.line_starts, position)

    def keyword_in_context(self, pattern: str, context_chars: int = 30, limit: int | None = None) -> list[SearchHit]:
        if context_chars < 0:
            raise ValueError("context_chars must be >= 0")
        if limit is not None and limit <= 0:
            raise ValueError("limit must be > 0 when provided")

        hits: list[SearchHit] = []
        for pos in self.find_positions(pattern):
            left = max(0, pos - context_chars)
            right = min(len(self.text), pos + len(pattern) + context_chars)
            local_start = pos - left
            local_end = local_start + len(pattern)
            excerpt = self.text[left:right]
            highlighted = f"{excerpt[:local_start]}[{excerpt[local_start:local_end]}]{excerpt[local_end:]}"
            context = highlighted.replace("\n", " ⏎ ")
            hits.append(
                SearchHit(
                    position=pos,
                    line=self.line_number_for(pos),
                    context=context,
                    match=self.text[pos : pos + len(pattern)],
                )
            )
            if limit is not None and len(hits) >= limit:
                break
        return hits


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_build(args: argparse.Namespace) -> int:
    text = read_text(args.input)
    index = SuffixArrayIndex.build(text)
    index.save(args.output)
    print(f"built suffix-array index with {len(index.suffix_array)} suffixes -> {args.output}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    index = SuffixArrayIndex.load(args.index)
    pattern = args.pattern.lower() if args.ignore_case else args.pattern
    search_index = SuffixArrayIndex.build(index.text.lower()) if args.ignore_case else index
    hits = search_index.keyword_in_context(pattern, context_chars=args.context, limit=args.limit)
    if not hits:
        print("no matches")
        return 1
    for hit in hits:
        left = max(0, hit.position - args.context)
        right = min(len(index.text), hit.position + len(args.pattern) + args.context)
        local_start = hit.position - left
        local_end = local_start + len(args.pattern)
        excerpt = index.text[left:right]
        rendered = f"{excerpt[:local_start]}[{excerpt[local_start:local_end]}]{excerpt[local_end:]}".replace("\n", " ⏎ ")
        if args.show_line_numbers:
            print(f"line {index.line_number_for(hit.position)}, pos {hit.position}: {rendered}")
        else:
            print(f"pos {hit.position}: {rendered}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    index = SuffixArrayIndex.load(args.index)
    print(json.dumps({
        "characters": len(index.text),
        "suffixes": len(index.suffix_array),
        "lines": len(index.line_starts),
    }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and query a suffix-array text index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build an index from a text file")
    build_parser.add_argument("--input", required=True)
    build_parser.add_argument("--output", required=True)
    build_parser.set_defaults(func=cmd_build)

    search_parser = subparsers.add_parser("search", help="search an index for a substring")
    search_parser.add_argument("--index", required=True)
    search_parser.add_argument("pattern")
    search_parser.add_argument("--context", type=non_negative_int, default=30)
    search_parser.add_argument("--limit", type=positive_int, default=None)
    search_parser.add_argument("--show-line-numbers", action="store_true")
    search_parser.add_argument("--ignore-case", action="store_true")
    search_parser.set_defaults(func=cmd_search)

    stats_parser = subparsers.add_parser("stats", help="show index metadata")
    stats_parser.add_argument("--index", required=True)
    stats_parser.set_defaults(func=cmd_stats)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
