#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import importlib.util
import json
import random
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from numbers import Number
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, Iterator

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
KeyValue = tuple[str, JSONValue]
Mapper = Callable[[Iterable[str]], Iterator[KeyValue]]
Reducer = Callable[[str, list[JSONValue]], JSONValue]


def is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
    return False


def normalize_json_value(value: Any, *, context: str) -> JSONValue:
    if not is_json_value(value):
        raise ValueError(f"{context} must return JSON-serializable values")
    return value


def order_output(output: dict[str, JSONValue]) -> dict[str, JSONValue]:
    if all(isinstance(value, Number) and not isinstance(value, bool) for value in output.values()):
        return dict(sorted(output.items(), key=lambda item: (-float(item[1]), item[0])))
    return dict(sorted(output.items()))


@dataclass(slots=True)
class JobResult:
    job: str
    inputs: list[str]
    shard_count: int
    map_records: int
    unique_keys: int
    output: dict[str, JSONValue]
    reducers: int
    reducer_stats: list[dict[str, int]]
    plugin: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "job": self.job,
                "plugin": self.plugin,
                "inputs": self.inputs,
                "shard_count": self.shard_count,
                "map_records": self.map_records,
                "unique_keys": self.unique_keys,
                "reducers": self.reducers,
                "reducer_stats": self.reducer_stats,
                "output": self.output,
            },
            indent=2,
            sort_keys=True,
        )


@dataclass(slots=True)
class BenchmarkResult:
    scenario: str
    seed: int
    total_records: int
    unique_keys: int
    shard_size: int
    reducers: list[int]
    timings_ms: list[dict[str, int | float]]

    def to_json(self) -> str:
        return json.dumps(
            {
                "scenario": self.scenario,
                "seed": self.seed,
                "total_records": self.total_records,
                "unique_keys": self.unique_keys,
                "shard_size": self.shard_size,
                "reducers": self.reducers,
                "timings_ms": self.timings_ms,
            },
            indent=2,
            sort_keys=True,
        )

    def to_csv(self) -> str:
        fieldnames = [
            "scenario",
            "seed",
            "total_records",
            "shard_size",
            "reducers",
            "elapsed_ms",
            "shards",
            "map_records",
            "unique_keys",
            "max_reducer_records",
            "skew_ratio",
        ]
        rows: list[dict[str, object]] = []
        for timing in self.timings_ms:
            row = {
                "scenario": self.scenario,
                "seed": self.seed,
                "total_records": self.total_records,
                "shard_size": self.shard_size,
                **timing,
            }
            rows.append(row)

        from io import StringIO
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()


@dataclass(slots=True)
class PluginJob:
    name: str
    mapper: Mapper
    combiner: Reducer
    reducer: Reducer
    path: Path


BUILTIN_JOBS = ("wordcount", "json-group-count")


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


def stable_partition(key: str, reducers: int) -> int:
    if reducers <= 0:
        raise ValueError("reducers must be positive")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % reducers


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


def sum_reducer(_key: str, values: list[JSONValue]) -> int:
    return sum(int(value) for value in values)


def combine(mapped: Iterable[KeyValue], combiner_fn: Reducer = sum_reducer) -> dict[str, JSONValue]:
    grouped: defaultdict[str, list[JSONValue]] = defaultdict(list)
    for key, value in mapped:
        grouped[key].append(value)
    combined: dict[str, JSONValue] = {}
    for key, values in grouped.items():
        combined[key] = normalize_json_value(combiner_fn(key, values), context="combiner")
    return combined


def build_plugin_job(module: ModuleType, origin: Path, fallback_name: str) -> PluginJob:
    mapper = getattr(module, "map_records", None)
    combiner = getattr(module, "combine_values", None)
    reducer = getattr(module, "reduce_key", None)
    name = getattr(module, "JOB_NAME", fallback_name)
    if not callable(mapper):
        raise ValueError("plugin must define callable map_records(lines)")
    if combiner is not None and not callable(combiner):
        raise ValueError("plugin combine_values must be callable when provided")
    if not callable(reducer):
        raise ValueError("plugin must define callable reduce_key(key, values)")
    return PluginJob(name=str(name), mapper=mapper, combiner=combiner or sum_reducer, reducer=reducer, path=origin)


def load_plugin(plugin_ref: str | Path) -> PluginJob:
    plugin_text = str(plugin_ref)
    candidate_path = Path(plugin_text)
    if candidate_path.exists():
        resolved = candidate_path.resolve()
        module_name = f"mini_mapreduce_plugin_{hashlib.sha256(str(resolved).encode('utf-8')).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ValueError(f"unable to load plugin module: {plugin_text}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return build_plugin_job(module, resolved, resolved.stem)

    try:
        module = importlib.import_module(plugin_text)
    except ModuleNotFoundError as exc:
        raise ValueError(f"plugin does not exist or is not importable: {plugin_text}") from exc

    module_file = getattr(module, "__file__", None)
    origin = Path(module_file).resolve() if module_file else Path(f"<module:{plugin_text}>")
    return build_plugin_job(module, origin, plugin_text.rsplit('.', 1)[-1])


def reduce_shards(
    partials: Iterable[dict[str, JSONValue]],
    reducers: int,
    reducer_fn: Reducer = sum_reducer,
) -> tuple[dict[str, JSONValue], list[dict[str, int]]]:
    if reducers <= 0:
        raise ValueError("reducers must be positive")
    buckets: list[defaultdict[str, list[JSONValue]]] = [defaultdict(list) for _ in range(reducers)]
    for partial in partials:
        for key, value in partial.items():
            buckets[stable_partition(key, reducers)][key].append(value)

    reduced: dict[str, JSONValue] = {}
    reducer_stats: list[dict[str, int]] = []
    for reducer_id, bucket in enumerate(buckets):
        reducer_records = 0
        for key, values in bucket.items():
            reduced[key] = normalize_json_value(reducer_fn(key, list(values)), context="reducer")
            if all(isinstance(value, Number) and not isinstance(value, bool) for value in values):
                reducer_records += sum(int(value) for value in values)
            else:
                reducer_records += len(values)
        reducer_stats.append(
            {
                "reducer": reducer_id,
                "unique_keys": len(bucket),
                "records": reducer_records,
            }
        )

    return order_output(reduced), reducer_stats


def reducer_skew(reducer_stats: list[dict[str, int]]) -> float:
    records = [item["records"] for item in reducer_stats]
    if not records:
        return 0.0
    average = sum(records) / len(records)
    if average == 0:
        return 0.0
    return max(records) / average


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
    reducers: int = 1,
    plugin_path: str | None = None,
) -> JobResult:
    lines = read_lines(inputs)
    partials: list[dict[str, JSONValue]] = []
    map_records = 0
    plugin: PluginJob | None = None

    mapper: Mapper
    combiner_fn: Reducer = sum_reducer
    reducer_fn: Reducer = sum_reducer
    resolved_job_name = job
    if job == "wordcount":
        mapper = map_wordcount
    elif job == "json-group-count":
        if not group_field:
            raise ValueError("group_field is required for json-group-count")
        mapper = lambda shard: map_json_group_count(shard, group_field)
    elif job == "plugin":
        if plugin_path is None:
            raise ValueError("plugin_path is required for plugin jobs")
        plugin = load_plugin(plugin_path)
        mapper = plugin.mapper
        combiner_fn = plugin.combiner
        reducer_fn = plugin.reducer
        resolved_job_name = plugin.name
    else:
        raise ValueError(f"unsupported job: {job}")

    shards = list(chunked(lines, shard_size)) or [[]]
    for shard in shards:
        mapped = [(key, normalize_json_value(value, context="mapper")) for key, value in mapper(shard)]
        map_records += len(mapped)
        partials.append(combine(mapped, combiner_fn=combiner_fn))

    reduced, reducer_stats = reduce_shards(partials, reducers, reducer_fn=reducer_fn)
    return JobResult(
        job=resolved_job_name,
        plugin=str(plugin.path) if plugin else None,
        inputs=[str(path) for path in inputs],
        shard_count=len(shards),
        map_records=map_records,
        unique_keys=len(reduced),
        reducers=reducers,
        reducer_stats=reducer_stats,
        output=reduced,
    )


def build_benchmark_lines(scenario: str, records: int, seed: int) -> list[str]:
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    if scenario == "balanced":
        keys = [f"key-{index:02d}" for index in range(24)]
        return [f"{keys[index % len(keys)]} {keys[(index * 7) % len(keys)]}" for index in range(records)]
    if scenario == "skewed":
        hot_keys = ["hot-key"] * 12 + [f"warm-{index}" for index in range(6)] + [f"cold-{index}" for index in range(18)]
        return [f"{rng.choice(hot_keys)} {rng.choice(hot_keys)}" for _ in range(records)]
    raise ValueError(f"unsupported benchmark scenario: {scenario}")


def benchmark_wordcount(
    scenario: str,
    records: int,
    shard_size: int,
    reducers: list[int],
    seed: int = 42,
) -> BenchmarkResult:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    if not reducers:
        raise ValueError("at least one reducer count is required")
    if any(count <= 0 for count in reducers):
        raise ValueError("reducers must be positive")

    lines = build_benchmark_lines(scenario, records, seed)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", prefix="mini-mapreduce-benchmark-", delete=False) as handle:
        handle.write("\n".join(lines) + "\n")
        input_path = Path(handle.name)

    timings: list[dict[str, int | float]] = []
    unique_keys = 0
    try:
        for reducer_count in reducers:
            started = time.perf_counter()
            result = execute_job("wordcount", [input_path], shard_size=shard_size, reducers=reducer_count)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            unique_keys = result.unique_keys
            timings.append(
                {
                    "reducers": reducer_count,
                    "elapsed_ms": elapsed_ms,
                    "shards": result.shard_count,
                    "map_records": result.map_records,
                    "unique_keys": result.unique_keys,
                    "max_reducer_records": max((item["records"] for item in result.reducer_stats), default=0),
                    "skew_ratio": round(reducer_skew(result.reducer_stats), 3),
                }
            )
    finally:
        input_path.unlink(missing_ok=True)

    return BenchmarkResult(
        scenario=scenario,
        seed=seed,
        total_records=records,
        unique_keys=unique_keys,
        shard_size=shard_size,
        reducers=reducers,
        timings_ms=timings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny MapReduce-style data processing lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a built-in MapReduce job")
    run_parser.add_argument("job", choices=[*BUILTIN_JOBS, "plugin"])
    run_parser.add_argument("inputs", nargs="+", help="input text or JSONL files")
    run_parser.add_argument("--shard-size", type=int, default=100, help="lines per shard")
    run_parser.add_argument("--reducers", type=int, default=1, help="number of reducer buckets to simulate")
    run_parser.add_argument("--group-field", help="JSON field to count for json-group-count")
    run_parser.add_argument("--plugin", help="plugin file path or importable Python module with map_records/reduce_key")
    run_parser.add_argument("--output", help="optional output JSON path")

    benchmark_parser = subparsers.add_parser("benchmark", help="run a synthetic wordcount benchmark")
    benchmark_parser.add_argument("--scenario", choices=["balanced", "skewed"], default="skewed")
    benchmark_parser.add_argument("--records", type=int, default=5000, help="synthetic input line count")
    benchmark_parser.add_argument("--shard-size", type=int, default=250, help="lines per shard")
    benchmark_parser.add_argument("--reducers", type=int, nargs="+", default=[1, 2, 4, 8], help="one or more reducer counts to compare")
    benchmark_parser.add_argument("--seed", type=int, default=42, help="seed for deterministic synthetic data generation")
    benchmark_parser.add_argument("--output", help="optional output JSON path")
    benchmark_parser.add_argument("--csv-output", help="optional benchmark CSV output path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        if args.job == "json-group-count" and not args.group_field:
            parser.error("--group-field is required for json-group-count")
        if args.job == "plugin" and not args.plugin:
            parser.error("--plugin is required for plugin jobs")
        if args.reducers <= 0:
            parser.error("--reducers must be positive")
        result = execute_job(
            job=args.job,
            inputs=[Path(item) for item in args.inputs],
            shard_size=args.shard_size,
            group_field=args.group_field,
            reducers=args.reducers,
            plugin_path=args.plugin if args.plugin else None,
        )
        rendered = result.to_json()
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0

    if args.command == "benchmark":
        if args.records <= 0:
            parser.error("--records must be positive")
        if args.shard_size <= 0:
            parser.error("--shard-size must be positive")
        if any(count <= 0 for count in args.reducers):
            parser.error("--reducers values must be positive")
        result = benchmark_wordcount(
            scenario=args.scenario,
            records=args.records,
            shard_size=args.shard_size,
            reducers=args.reducers,
            seed=args.seed,
        )
        rendered = result.to_json()
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        if args.csv_output:
            Path(args.csv_output).write_text(result.to_csv(), encoding="utf-8")
        return 0

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
