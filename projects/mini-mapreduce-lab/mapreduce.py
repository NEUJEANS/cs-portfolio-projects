#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

KeyValue = tuple[str, int]


@dataclass(slots=True)
class JobResult:
    job: str
    inputs: list[str]
    shard_count: int
    map_records: int
    unique_keys: int
    output: dict[str, int | dict[str, int]]

    def to_json(self) -> str:
        return json.dumps(
            {
                "job": self.job,
                "inputs": self.inputs,
                "shard_count": self.shard_count,
                "map_records": self.map_records,
                "unique_keys": self.unique_keys,
                "output": self.output,
            },
            indent=2,
            sort_keys=True,
        )


def chunked(items: list[str], size: int) -> Iterator[list[str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for index in range(0, len(items), size):
        yield items[index : index + size]


def tokenize(text: str) -> list[str]:
    cleaned = []
    for char in text.lower():
        cleaned.append(char if char.isalnum() else " ")
    return [token for token in "".join(cleaned).split() if token]


def map_wordcount(lines: Iterable[str]) -> Iterator[KeyValue]:
    for line in lines:
        for token in tokenize(line):
            yield token, 1


def map_json_group_count(lines: Iterable[str], field: str) -> Iterator[KeyValue]:
    for raw in lines:
        if not raw.strip():
            continue
        record = json.loads(raw)
        value = record.get(field, "<missing>")
        if value is None:
            value = "<null>"
        yield str(value), 1


def combine(mapped: Iterable[KeyValue]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for key, value in mapped:
        counts[key] += value
    return counts


def reduce_shards(partials: Iterable[Counter[str]]) -> dict[str, int]:
    combined: defaultdict[str, int] = defaultdict(int)
    for partial in partials:
        for key, value in partial.items():
            combined[key] += value
    return dict(sorted(combined.items(), key=lambda item: (-item[1], item[0])))


def read_lines(inputs: list[Path]) -> list[str]:
    lines: list[str] = []
    for path in inputs:
        lines.extend(path.read_text(encoding="utf-8").splitlines())
    return lines


def execute_job(
    job: str,
    inputs: list[Path],
    shard_size: int,
    group_field: str | None = None,
) -> JobResult:
    lines = read_lines(inputs)
    partials: list[Counter[str]] = []
    map_records = 0

    mapper: Callable[[Iterable[str]], Iterator[KeyValue]]
    if job == "wordcount":
        mapper = map_wordcount
    elif job == "json-group-count":
        if not group_field:
            raise ValueError("group_field is required for json-group-count")
        mapper = lambda shard: map_json_group_count(shard, group_field)
    else:
        raise ValueError(f"unsupported job: {job}")

    shards = list(chunked(lines, shard_size)) or [[]]
    for shard in shards:
        mapped = list(mapper(shard))
        map_records += len(mapped)
        partials.append(combine(mapped))

    reduced = reduce_shards(partials)
    return JobResult(
        job=job,
        inputs=[str(path) for path in inputs],
        shard_count=len(shards),
        map_records=map_records,
        unique_keys=len(reduced),
        output=reduced,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny MapReduce-style data processing lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a built-in MapReduce job")
    run_parser.add_argument("job", choices=["wordcount", "json-group-count"])
    run_parser.add_argument("inputs", nargs="+", help="input text or JSONL files")
    run_parser.add_argument("--shard-size", type=int, default=100, help="lines per shard")
    run_parser.add_argument("--group-field", help="JSON field to count for json-group-count")
    run_parser.add_argument("--output", help="optional output JSON path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        if args.job == "json-group-count" and not args.group_field:
            parser.error("--group-field is required for json-group-count")
        result = execute_job(
            job=args.job,
            inputs=[Path(item) for item in args.inputs],
            shard_size=args.shard_size,
            group_field=args.group_field,
        )
        rendered = result.to_json()
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
