from __future__ import annotations

import argparse
import csv
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FenwickTree:
    def __init__(self, size: int):
        if size < 1:
            raise ValueError("size must be positive")
        self.size = size
        self.tree = [0] * (size + 1)

    def add(self, index: int, delta: int) -> None:
        if not 1 <= index <= self.size:
            raise IndexError("index out of bounds")
        while index <= self.size:
            self.tree[index] += delta
            index += index & -index

    def prefix_sum(self, index: int) -> int:
        if index < 0:
            return 0
        if index > self.size:
            index = self.size
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= index & -index
        return result

    @classmethod
    def from_values(cls, values: list[int]) -> "FenwickTree":
        fenwick = cls(len(values))
        for offset, value in enumerate(values, start=1):
            fenwick.add(offset, value)
        return fenwick


class RangeFenwick:
    def __init__(self, values: list[int]):
        if not values:
            raise ValueError("values must not be empty")
        self._size = len(values)
        self._tree_a = FenwickTree(self._size)
        self._tree_b = FenwickTree(self._size)
        for index, value in enumerate(values, start=1):
            self._range_add_internal(index, index, value)

    @property
    def size(self) -> int:
        return self._size

    @property
    def values(self) -> list[int]:
        return [self.point_query(index) for index in range(1, self.size + 1)]

    def _apply_internal(self, index: int, delta: int) -> None:
        if index <= 0:
            return
        if index > self.size + 1:
            return
        if index <= self.size:
            self._tree_a.add(index, delta)
            self._tree_b.add(index, delta * (index - 1))

    def _prefix_sum(self, index: int) -> int:
        return self._tree_a.prefix_sum(index) * index - self._tree_b.prefix_sum(index)

    def point_query(self, index: int) -> int:
        return self.range_sum(index, index)

    def point_add(self, index: int, delta: int) -> None:
        self.range_add(index, index, delta)

    def point_set(self, index: int, value: int) -> None:
        self._validate_index(index)
        self.point_add(index, value - self.point_query(index))

    def _range_add_internal(self, left: int, right: int, delta: int) -> None:
        self._apply_internal(left, delta)
        self._apply_internal(right + 1, -delta)

    def range_add(self, left: int, right: int, delta: int) -> None:
        self._validate_range(left, right)
        self._range_add_internal(left, right, delta)

    def prefix_sum(self, index: int) -> int:
        if index < 0:
            return 0
        if index == 0:
            return 0
        if index > self.size:
            index = self.size
        return self._prefix_sum(index)

    def range_sum(self, left: int, right: int) -> int:
        self._validate_range(left, right)
        return self._prefix_sum(right) - self._prefix_sum(left - 1)

    def stats(self) -> dict[str, Any]:
        values = self.values
        total = self.range_sum(1, self.size)
        return {
            "size": self.size,
            "total": total,
            "min": min(values),
            "max": max(values),
            "values": values,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"values": self.values}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RangeFenwick":
        values = data.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("snapshot must include a non-empty values list")
        if not all(type(value) is int for value in values):
            raise ValueError("snapshot values must be integers")
        return cls(values=list(values))

    def _validate_index(self, index: int) -> None:
        if not 1 <= index <= self.size:
            raise IndexError("index out of bounds")

    def _validate_range(self, left: int, right: int) -> None:
        if left > right:
            raise ValueError("left must be <= right")
        self._validate_index(left)
        self._validate_index(right)


class RangeAddSegmentTree:
    def __init__(self, values: list[int]):
        if not values:
            raise ValueError("values must not be empty")
        self.size = len(values)
        self._tree = [0] * (4 * self.size)
        self._lazy = [0] * (4 * self.size)
        self._build(1, 1, self.size, values)

    def _build(self, node: int, left: int, right: int, values: list[int]) -> None:
        if left == right:
            self._tree[node] = values[left - 1]
            return
        mid = (left + right) // 2
        self._build(node * 2, left, mid, values)
        self._build(node * 2 + 1, mid + 1, right, values)
        self._tree[node] = self._tree[node * 2] + self._tree[node * 2 + 1]

    def _apply(self, node: int, left: int, right: int, delta: int) -> None:
        self._tree[node] += (right - left + 1) * delta
        self._lazy[node] += delta

    def _push(self, node: int, left: int, right: int) -> None:
        if self._lazy[node] == 0 or left == right:
            return
        mid = (left + right) // 2
        delta = self._lazy[node]
        self._apply(node * 2, left, mid, delta)
        self._apply(node * 2 + 1, mid + 1, right, delta)
        self._lazy[node] = 0

    def _validate_index(self, index: int) -> None:
        if not 1 <= index <= self.size:
            raise IndexError("index out of bounds")

    def _validate_range(self, left: int, right: int) -> None:
        if left > right:
            raise ValueError("left must be <= right")
        self._validate_index(left)
        self._validate_index(right)

    def _range_add(self, node: int, node_left: int, node_right: int, left: int, right: int, delta: int) -> None:
        if left <= node_left and node_right <= right:
            self._apply(node, node_left, node_right, delta)
            return
        self._push(node, node_left, node_right)
        mid = (node_left + node_right) // 2
        if left <= mid:
            self._range_add(node * 2, node_left, mid, left, right, delta)
        if right > mid:
            self._range_add(node * 2 + 1, mid + 1, node_right, left, right, delta)
        self._tree[node] = self._tree[node * 2] + self._tree[node * 2 + 1]

    def range_add(self, left: int, right: int, delta: int) -> None:
        self._validate_range(left, right)
        self._range_add(1, 1, self.size, left, right, delta)

    def _range_sum(self, node: int, node_left: int, node_right: int, left: int, right: int) -> int:
        if left <= node_left and node_right <= right:
            return self._tree[node]
        self._push(node, node_left, node_right)
        mid = (node_left + node_right) // 2
        total = 0
        if left <= mid:
            total += self._range_sum(node * 2, node_left, mid, left, right)
        if right > mid:
            total += self._range_sum(node * 2 + 1, mid + 1, node_right, left, right)
        return total

    def range_sum(self, left: int, right: int) -> int:
        self._validate_range(left, right)
        return self._range_sum(1, 1, self.size, left, right)

    def point_query(self, index: int) -> int:
        return self.range_sum(index, index)

    def point_set(self, index: int, value: int) -> None:
        self._validate_index(index)
        current = self.point_query(index)
        self.range_add(index, index, value - current)


@dataclass(frozen=True)
class BenchmarkOperation:
    kind: str
    left: int
    right: int
    amount: int | None = None


def load_values(path: Path) -> list[int]:
    values: list[int] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            values.append(int(line))
        except ValueError as exc:
            raise ValueError(f"invalid integer on line {line_number}: {line}") from exc
    if not values:
        raise ValueError("input must contain at least one integer")
    return values


def save_snapshot(path: Path, fenwick: RangeFenwick) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fenwick.to_dict(), indent=2) + "\n")


def load_snapshot(path: Path) -> RangeFenwick:
    return RangeFenwick.from_dict(json.loads(path.read_text()))


def _pick_range(rng: random.Random, *, size: int, max_range_width: int | None) -> tuple[int, int]:
    width_cap = size if max_range_width in (None, 0) else min(size, max_range_width)
    left = rng.randint(1, size)
    width = rng.randint(1, min(width_cap, size - left + 1))
    return left, left + width - 1


def generate_benchmark_values(size: int, *, seed: int, value_min: int, value_max: int) -> list[int]:
    if size < 1:
        raise ValueError("size must be positive")
    if value_min > value_max:
        raise ValueError("value_min must be <= value_max")
    rng = random.Random(seed)
    return [rng.randint(value_min, value_max) for _ in range(size)]


def generate_benchmark_operations(
    *,
    size: int,
    operations: int,
    seed: int,
    query_ratio: float,
    set_ratio: float,
    max_range_width: int | None,
    value_min: int,
    value_max: int,
    delta_min: int,
    delta_max: int,
) -> list[BenchmarkOperation]:
    if size < 1:
        raise ValueError("size must be positive")
    if operations < 1:
        raise ValueError("operations must be positive")
    if not 0 <= query_ratio <= 1:
        raise ValueError("query_ratio must be between 0 and 1")
    if not 0 <= set_ratio <= 1:
        raise ValueError("set_ratio must be between 0 and 1")
    if query_ratio + set_ratio > 1:
        raise ValueError("query_ratio + set_ratio must be <= 1")
    if value_min > value_max:
        raise ValueError("value_min must be <= value_max")
    if delta_min > delta_max:
        raise ValueError("delta_min must be <= delta_max")
    if max_range_width is not None and max_range_width < 1:
        raise ValueError("max_range_width must be positive when provided")

    rng = random.Random(seed)
    generated: list[BenchmarkOperation] = []
    for _ in range(operations):
        selector = rng.random()
        if selector < query_ratio:
            left, right = _pick_range(rng, size=size, max_range_width=max_range_width)
            generated.append(BenchmarkOperation("range_sum", left, right))
        elif selector < query_ratio + set_ratio:
            index = rng.randint(1, size)
            generated.append(BenchmarkOperation("point_set", index, index, rng.randint(value_min, value_max)))
        else:
            left, right = _pick_range(rng, size=size, max_range_width=max_range_width)
            generated.append(BenchmarkOperation("range_add", left, right, rng.randint(delta_min, delta_max)))
    return generated


def _operation_mix(operations: list[BenchmarkOperation]) -> dict[str, int]:
    counts = {"range_sum": 0, "range_add": 0, "point_set": 0}
    for operation in operations:
        counts[operation.kind] += 1
    return counts


def _run_strategy(
    name: str,
    *,
    initial_values: list[int],
    operations: list[BenchmarkOperation],
    repeats: int,
) -> dict[str, Any]:
    if name == "range-fenwick":
        factory = lambda: RangeFenwick(list(initial_values))
    elif name == "segment-tree":
        factory = lambda: RangeAddSegmentTree(list(initial_values))
    else:
        raise ValueError(f"unsupported strategy: {name}")

    kind_timings_ns = {"range_sum": 0, "range_add": 0, "point_set": 0}
    run_seconds: list[float] = []
    query_checksums: list[int] = []
    final_totals: list[int] = []

    for _ in range(repeats):
        structure = factory()
        start_ns = time.perf_counter_ns()
        query_checksum = 0
        for operation in operations:
            op_start_ns = time.perf_counter_ns()
            if operation.kind == "range_sum":
                query_checksum += structure.range_sum(operation.left, operation.right)
            elif operation.kind == "range_add":
                assert operation.amount is not None
                structure.range_add(operation.left, operation.right, operation.amount)
            elif operation.kind == "point_set":
                assert operation.amount is not None
                structure.point_set(operation.left, operation.amount)
            else:
                raise ValueError(f"unsupported benchmark operation: {operation.kind}")
            kind_timings_ns[operation.kind] += time.perf_counter_ns() - op_start_ns
        elapsed_seconds = (time.perf_counter_ns() - start_ns) / 1_000_000_000
        run_seconds.append(elapsed_seconds)
        query_checksums.append(query_checksum)
        final_totals.append(structure.range_sum(1, len(initial_values)))

    if len(set(query_checksums)) != 1 or len(set(final_totals)) != 1:
        raise AssertionError(f"{name} benchmark runs were not deterministic")

    average_seconds = sum(run_seconds) / repeats
    total_operation_count = len(operations)
    mix = _operation_mix(operations)

    result: dict[str, Any] = {
        "strategy": name,
        "repeats": repeats,
        "average_seconds": round(average_seconds, 6),
        "best_seconds": round(min(run_seconds), 6),
        "worst_seconds": round(max(run_seconds), 6),
        "operations": total_operation_count,
        "operations_per_second": round(total_operation_count / average_seconds, 2),
        "query_checksum": query_checksums[0],
        "final_total": final_totals[0],
        "timings": {},
    }
    for kind, count in mix.items():
        kind_seconds = kind_timings_ns[kind] / 1_000_000_000
        result["timings"][kind] = {
            "count": count,
            "total_seconds": round(kind_seconds, 6),
            "average_microseconds": round((kind_seconds / max(count * repeats, 1)) * 1_000_000, 3),
        }
    return result


def run_benchmark(
    *,
    size: int,
    operations: int,
    seed: int,
    repeats: int,
    query_ratio: float,
    set_ratio: float,
    max_range_width: int | None,
    value_min: int,
    value_max: int,
    delta_min: int,
    delta_max: int,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be positive")

    initial_values = generate_benchmark_values(size, seed=seed, value_min=value_min, value_max=value_max)
    workload = generate_benchmark_operations(
        size=size,
        operations=operations,
        seed=seed + 1,
        query_ratio=query_ratio,
        set_ratio=set_ratio,
        max_range_width=max_range_width,
        value_min=value_min,
        value_max=value_max,
        delta_min=delta_min,
        delta_max=delta_max,
    )
    strategy_results = [
        _run_strategy("range-fenwick", initial_values=initial_values, operations=workload, repeats=repeats),
        _run_strategy("segment-tree", initial_values=initial_values, operations=workload, repeats=repeats),
    ]
    baseline_signature = (
        strategy_results[0]["query_checksum"],
        strategy_results[0]["final_total"],
    )
    for result in strategy_results:
        result["verified_against_baseline"] = (
            result["query_checksum"],
            result["final_total"]
        ) == baseline_signature

    sorted_results = sorted(strategy_results, key=lambda item: item["average_seconds"])
    faster = sorted_results[0]
    slower = sorted_results[1]
    speedup = slower["average_seconds"] / faster["average_seconds"] if faster["average_seconds"] else None

    return {
        "size": size,
        "operations": operations,
        "repeats": repeats,
        "seed": seed,
        "query_ratio": query_ratio,
        "set_ratio": set_ratio,
        "range_add_ratio": round(1 - query_ratio - set_ratio, 4),
        "max_range_width": max_range_width,
        "value_min": value_min,
        "value_max": value_max,
        "delta_min": delta_min,
        "delta_max": delta_max,
        "initial_total": sum(initial_values),
        "operation_mix": _operation_mix(workload),
        "correctness_verified": all(result["verified_against_baseline"] for result in strategy_results),
        "faster_strategy": faster["strategy"],
        "speedup": round(speedup, 3) if speedup is not None else None,
        "strategies": strategy_results,
    }


def save_benchmark_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def save_benchmark_csv(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "strategy",
        "average_seconds",
        "best_seconds",
        "worst_seconds",
        "operations",
        "operations_per_second",
        "query_checksum",
        "final_total",
        "verified_against_baseline",
        "range_sum_avg_us",
        "range_add_avg_us",
        "point_set_avg_us",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in payload["strategies"]:
            writer.writerow(
                {
                    "strategy": result["strategy"],
                    "average_seconds": result["average_seconds"],
                    "best_seconds": result["best_seconds"],
                    "worst_seconds": result["worst_seconds"],
                    "operations": result["operations"],
                    "operations_per_second": result["operations_per_second"],
                    "query_checksum": result["query_checksum"],
                    "final_total": result["final_total"],
                    "verified_against_baseline": result["verified_against_baseline"],
                    "range_sum_avg_us": result["timings"]["range_sum"]["average_microseconds"],
                    "range_add_avg_us": result["timings"]["range_add"]["average_microseconds"],
                    "point_set_avg_us": result["timings"]["point_set"]["average_microseconds"],
                }
            )


def render_benchmark_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fenwick vs Segment Tree Benchmark",
        "",
        f"- size: {payload['size']}",
        f"- operations per run: {payload['operations']}",
        f"- repeats: {payload['repeats']}",
        f"- seed: {payload['seed']}",
        f"- correctness verified: {payload['correctness_verified']}",
        f"- faster strategy: {payload['faster_strategy']}",
        f"- relative speedup: {payload['speedup']}x",
        "",
        "## Operation mix",
        "",
        f"- range_sum: {payload['operation_mix']['range_sum']}",
        f"- range_add: {payload['operation_mix']['range_add']}",
        f"- point_set: {payload['operation_mix']['point_set']}",
        "",
        "## Strategy summary",
        "",
        "| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in payload["strategies"]:
        lines.append(
            "| "
            f"{result['strategy']} | "
            f"{result['average_seconds']} | "
            f"{result['operations_per_second']} | "
            f"{result['timings']['range_sum']['average_microseconds']} | "
            f"{result['timings']['range_add']['average_microseconds']} | "
            f"{result['timings']['point_set']['average_microseconds']} | "
            f"{result['verified_against_baseline']} |"
        )
    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            "- The benchmark replays the exact same mixed workload through both data structures.",
            "- Query checksums and final totals must match before the timing comparison is considered valid.",
            "- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_command(args: argparse.Namespace) -> int:
    fenwick = RangeFenwick(load_values(Path(args.input)))
    if args.output:
        save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"output": args.output, **fenwick.stats()}, indent=2))
    return 0


def sum_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    print(json.dumps({"left": args.left, "right": args.right, "sum": fenwick.range_sum(args.left, args.right)}, indent=2))
    return 0


def add_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    fenwick.range_add(args.left, args.right, args.delta)
    save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"left": args.left, "right": args.right, "delta": args.delta, "output": args.output, **fenwick.stats()}, indent=2))
    return 0


def set_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    fenwick.point_set(args.index, args.value)
    save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"index": args.index, "value": args.value, "output": args.output, **fenwick.stats()}, indent=2))
    return 0


def export_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["index,value,prefix_sum"]
    for index, value in enumerate(fenwick.values, start=1):
        lines.append(f"{index},{value},{fenwick.prefix_sum(index)}")
    output.write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": args.output, "rows": fenwick.size}, indent=2))
    return 0


def benchmark_command(args: argparse.Namespace) -> int:
    payload = run_benchmark(
        size=args.size,
        operations=args.operations,
        seed=args.seed,
        repeats=args.repeats,
        query_ratio=args.query_ratio,
        set_ratio=args.set_ratio,
        max_range_width=args.max_range_width,
        value_min=args.value_min,
        value_max=args.value_max,
        delta_min=args.delta_min,
        delta_max=args.delta_max,
    )
    if args.output:
        save_benchmark_json(Path(args.output), payload)
    if args.csv_output:
        save_benchmark_csv(Path(args.csv_output), payload)
    if args.markdown_output:
        output = Path(args.markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_benchmark_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fenwick tree range query lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a snapshot from newline-delimited integers")
    build_parser.add_argument("--input", required=True)
    build_parser.add_argument("--output")
    build_parser.set_defaults(func=build_command)

    sum_parser = subparsers.add_parser("sum", help="query an inclusive range sum")
    sum_parser.add_argument("--snapshot", required=True)
    sum_parser.add_argument("left", type=int)
    sum_parser.add_argument("right", type=int)
    sum_parser.set_defaults(func=sum_command)

    add_parser = subparsers.add_parser("add", help="add a delta to an inclusive range")
    add_parser.add_argument("--snapshot", required=True)
    add_parser.add_argument("--output", required=True)
    add_parser.add_argument("left", type=int)
    add_parser.add_argument("right", type=int)
    add_parser.add_argument("delta", type=int)
    add_parser.set_defaults(func=add_command)

    set_parser = subparsers.add_parser("set", help="set a single index to a new value")
    set_parser.add_argument("--snapshot", required=True)
    set_parser.add_argument("--output", required=True)
    set_parser.add_argument("index", type=int)
    set_parser.add_argument("value", type=int)
    set_parser.set_defaults(func=set_command)

    export_parser = subparsers.add_parser("export", help="export current values and prefix sums")
    export_parser.add_argument("--snapshot", required=True)
    export_parser.add_argument("--output", required=True)
    export_parser.set_defaults(func=export_command)

    benchmark_parser = subparsers.add_parser("benchmark", help="benchmark RangeFenwick against a lazy segment tree")
    benchmark_parser.add_argument("--size", type=int, default=256)
    benchmark_parser.add_argument("--operations", type=int, default=1000)
    benchmark_parser.add_argument("--seed", type=int, default=7)
    benchmark_parser.add_argument("--repeats", type=int, default=3)
    benchmark_parser.add_argument("--query-ratio", type=float, default=0.45)
    benchmark_parser.add_argument("--set-ratio", type=float, default=0.15)
    benchmark_parser.add_argument("--max-range-width", type=int, default=32)
    benchmark_parser.add_argument("--value-min", type=int, default=0)
    benchmark_parser.add_argument("--value-max", type=int, default=200)
    benchmark_parser.add_argument("--delta-min", type=int, default=-20)
    benchmark_parser.add_argument("--delta-max", type=int, default=20)
    benchmark_parser.add_argument("--output")
    benchmark_parser.add_argument("--csv-output")
    benchmark_parser.add_argument("--markdown-output")
    benchmark_parser.set_defaults(func=benchmark_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
