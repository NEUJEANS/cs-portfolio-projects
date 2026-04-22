from __future__ import annotations

import argparse
import csv
import html
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


@dataclass(frozen=True)
class BenchmarkPreset:
    name: str
    query_ratio: float
    set_ratio: float
    max_range_width: int | None
    description: str


DEFAULT_BENCHMARK_PRESET = "balanced"
BENCHMARK_PRESETS: dict[str, BenchmarkPreset] = {
    "balanced": BenchmarkPreset(
        name="balanced",
        query_ratio=0.45,
        set_ratio=0.15,
        max_range_width=32,
        description="Balanced mix across reads, range updates, and point overwrites.",
    ),
    "query-heavy": BenchmarkPreset(
        name="query-heavy",
        query_ratio=0.75,
        set_ratio=0.1,
        max_range_width=48,
        description="Range-sum reads dominate the workload story.",
    ),
    "update-heavy": BenchmarkPreset(
        name="update-heavy",
        query_ratio=0.2,
        set_ratio=0.1,
        max_range_width=24,
        description="Range adds dominate the workload story.",
    ),
    "point-set-heavy": BenchmarkPreset(
        name="point-set-heavy",
        query_ratio=0.25,
        set_ratio=0.55,
        max_range_width=12,
        description="Single-index overwrites dominate the workload story.",
    ),
}
DEFAULT_COMPARE_PRESETS = tuple(BENCHMARK_PRESETS)
OPERATION_LABELS = {
    "range_sum": "Range sum",
    "range_add": "Range add",
    "point_set": "Point set",
}


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


def resolve_benchmark_profile(
    *,
    preset: str,
    query_ratio: float | None,
    set_ratio: float | None,
    max_range_width: int | None,
) -> BenchmarkPreset:
    profile = BENCHMARK_PRESETS.get(preset)
    if profile is None:
        available = ", ".join(sorted(BENCHMARK_PRESETS))
        raise ValueError(f"unknown benchmark preset: {preset}. choose from: {available}")
    return BenchmarkPreset(
        name=profile.name,
        query_ratio=profile.query_ratio if query_ratio is None else query_ratio,
        set_ratio=profile.set_ratio if set_ratio is None else set_ratio,
        max_range_width=profile.max_range_width if max_range_width is None else max_range_width,
        description=profile.description,
    )


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
    preset: str = DEFAULT_BENCHMARK_PRESET,
    query_ratio: float | None = None,
    set_ratio: float | None = None,
    max_range_width: int | None = None,
    value_min: int,
    value_max: int,
    delta_min: int,
    delta_max: int,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be positive")

    profile = resolve_benchmark_profile(
        preset=preset,
        query_ratio=query_ratio,
        set_ratio=set_ratio,
        max_range_width=max_range_width,
    )

    initial_values = generate_benchmark_values(size, seed=seed, value_min=value_min, value_max=value_max)
    workload = generate_benchmark_operations(
        size=size,
        operations=operations,
        seed=seed + 1,
        query_ratio=profile.query_ratio,
        set_ratio=profile.set_ratio,
        max_range_width=profile.max_range_width,
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
        "preset": profile.name,
        "preset_description": profile.description,
        "query_ratio": profile.query_ratio,
        "set_ratio": profile.set_ratio,
        "range_add_ratio": round(1 - profile.query_ratio - profile.set_ratio, 4),
        "max_range_width": profile.max_range_width,
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
        "preset",
        "query_ratio",
        "range_add_ratio",
        "set_ratio",
        "max_range_width",
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for result in payload["strategies"]:
            writer.writerow(
                {
                    "preset": payload["preset"],
                    "query_ratio": payload["query_ratio"],
                    "range_add_ratio": payload["range_add_ratio"],
                    "set_ratio": payload["set_ratio"],
                    "max_range_width": payload["max_range_width"],
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


def _format_metric(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def _format_ratio_pct(value: float) -> str:
    return f"{int(round(value * 100))}%"


def _preset_related_artifacts(preset: str) -> dict[str, str]:
    if preset == DEFAULT_BENCHMARK_PRESET:
        return {
            "json": "../sample-benchmark.json",
            "csv": "../sample-benchmark.csv",
            "markdown": "../sample-benchmark-report.md",
            "svg": "../sample-benchmark-chart.svg",
        }
    base = f"{preset}-benchmark"
    return {
        "json": f"{base}.json",
        "csv": f"{base}.csv",
        "markdown": f"{base}-report.md",
        "svg": f"{base}-chart.svg",
    }


def _saved_benchmark_json_path(preset: str) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    relative_path = _preset_related_artifacts(preset)["json"]
    return (repo_root / "docs/artifacts/fenwick-tree-range-query-lab/presets" / relative_path).resolve()


def _build_preset_comparison_payload(benchmark_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    if not benchmark_payloads:
        raise ValueError("at least one benchmark payload is required")

    first = benchmark_payloads[0]
    shared_fields = ["size", "operations", "repeats", "seed", "value_min", "value_max", "delta_min", "delta_max"]
    for payload in benchmark_payloads[1:]:
        for field in shared_fields:
            if payload[field] != first[field]:
                raise ValueError(f"benchmark payloads must share {field} to compare presets safely")

    rows: list[dict[str, Any]] = []
    operation_winner_counts = {
        "range-fenwick": {kind: 0 for kind in OPERATION_LABELS},
        "segment-tree": {kind: 0 for kind in OPERATION_LABELS},
    }

    for payload in benchmark_payloads:
        strategies = {result["strategy"]: result for result in payload["strategies"]}
        fenwick = strategies["range-fenwick"]
        segment_tree = strategies["segment-tree"]
        dominant_operation = max(
            payload["operation_mix"],
            key=lambda kind: (payload["operation_mix"][kind], kind),
        )
        per_operation_winners: dict[str, str] = {}
        for kind in OPERATION_LABELS:
            winner = min(
                payload["strategies"],
                key=lambda result: result["timings"][kind]["average_microseconds"],
            )["strategy"]
            per_operation_winners[kind] = winner
            operation_winner_counts[winner][kind] += 1
        fenwick_advantage_pct = None
        if segment_tree["operations_per_second"]:
            fenwick_advantage_pct = round(
                ((fenwick["operations_per_second"] / segment_tree["operations_per_second"]) - 1) * 100,
                1,
            )
        rows.append(
            {
                "preset": payload["preset"],
                "preset_description": payload["preset_description"],
                "query_ratio": payload["query_ratio"],
                "range_add_ratio": payload["range_add_ratio"],
                "set_ratio": payload["set_ratio"],
                "max_range_width": payload["max_range_width"],
                "operation_mix": payload["operation_mix"],
                "dominant_operation": dominant_operation,
                "correctness_verified": payload["correctness_verified"],
                "faster_strategy": payload["faster_strategy"],
                "speedup": payload["speedup"],
                "range_fenwick_ops_per_second": fenwick["operations_per_second"],
                "segment_tree_ops_per_second": segment_tree["operations_per_second"],
                "fenwick_advantage_pct": fenwick_advantage_pct,
                "range_fenwick_average_seconds": fenwick["average_seconds"],
                "segment_tree_average_seconds": segment_tree["average_seconds"],
                "per_operation_winners": per_operation_winners,
                "artifacts": _preset_related_artifacts(payload["preset"]),
            }
        )

    strongest_edge = max(rows, key=lambda row: (row["speedup"], row["preset"]))
    tightest_race = min(rows, key=lambda row: (row["speedup"], row["preset"]))
    fastest_fenwick = max(rows, key=lambda row: (row["range_fenwick_ops_per_second"], row["preset"]))
    fastest_segment_tree = max(rows, key=lambda row: (row["segment_tree_ops_per_second"], row["preset"]))

    return {
        "mode": "compare-presets",
        "size": first["size"],
        "operations": first["operations"],
        "repeats": first["repeats"],
        "seed": first["seed"],
        "value_min": first["value_min"],
        "value_max": first["value_max"],
        "delta_min": first["delta_min"],
        "delta_max": first["delta_max"],
        "preset_count": len(rows),
        "presets": rows,
        "all_correctness_verified": all(row["correctness_verified"] for row in rows),
        "average_speedup": round(sum(row["speedup"] for row in rows) / len(rows), 3),
        "consistent_winner": len({row["faster_strategy"] for row in rows}) == 1,
        "operation_winner_counts": operation_winner_counts,
        "strongest_edge": {
            "preset": strongest_edge["preset"],
            "speedup": strongest_edge["speedup"],
            "dominant_operation": strongest_edge["dominant_operation"],
        },
        "tightest_race": {
            "preset": tightest_race["preset"],
            "speedup": tightest_race["speedup"],
            "dominant_operation": tightest_race["dominant_operation"],
        },
        "fastest_fenwick": {
            "preset": fastest_fenwick["preset"],
            "operations_per_second": fastest_fenwick["range_fenwick_ops_per_second"],
        },
        "fastest_segment_tree": {
            "preset": fastest_segment_tree["preset"],
            "operations_per_second": fastest_segment_tree["segment_tree_ops_per_second"],
        },
    }


def compare_benchmark_presets(
    *,
    presets: list[str] | None = None,
    size: int,
    operations: int,
    seed: int,
    repeats: int,
    value_min: int,
    value_max: int,
    delta_min: int,
    delta_max: int,
) -> dict[str, Any]:
    selected_presets = list(dict.fromkeys(presets or DEFAULT_COMPARE_PRESETS))
    if not selected_presets:
        raise ValueError("at least one preset is required")
    benchmark_payloads = [
        run_benchmark(
            size=size,
            operations=operations,
            seed=seed,
            repeats=repeats,
            preset=preset,
            value_min=value_min,
            value_max=value_max,
            delta_min=delta_min,
            delta_max=delta_max,
        )
        for preset in selected_presets
    ]
    return _build_preset_comparison_payload(benchmark_payloads)


def compare_saved_benchmark_presets(presets: list[str] | None = None) -> dict[str, Any]:
    selected_presets = list(dict.fromkeys(presets or DEFAULT_COMPARE_PRESETS))
    if not selected_presets:
        raise ValueError("at least one preset is required")
    benchmark_payloads = [json.loads(_saved_benchmark_json_path(preset).read_text()) for preset in selected_presets]
    return _build_preset_comparison_payload(benchmark_payloads)


def render_benchmark_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fenwick vs Segment Tree Benchmark",
        "",
        f"- size: {payload['size']}",
        f"- operations per run: {payload['operations']}",
        f"- repeats: {payload['repeats']}",
        f"- seed: {payload['seed']}",
        f"- workload preset: {payload['preset']}",
        f"- preset summary: {payload['preset_description']}",
        f"- query ratio: {payload['query_ratio']}",
        f"- range-add ratio: {payload['range_add_ratio']}",
        f"- point-set ratio: {payload['set_ratio']}",
        f"- max range width: {payload['max_range_width']}",
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


def render_benchmark_svg(payload: dict[str, Any]) -> str:
    width = 1040
    height = 760
    card_width = 290
    card_height = 92
    ops_bar_width = 360
    latency_bar_width = 230
    strategy_colors = {
        "range-fenwick": "#2563eb",
        "segment-tree": "#f97316",
    }
    strategies = payload["strategies"]
    max_ops = max(result["operations_per_second"] for result in strategies)
    latency_rows = [
        ("range_sum", "Range sum μs"),
        ("range_add", "Range add μs"),
        ("point_set", "Point set μs"),
    ]
    max_latency = max(
        result["timings"][kind]["average_microseconds"]
        for result in strategies
        for kind, _ in latency_rows
    )

    def strategy_color(name: str) -> str:
        return strategy_colors.get(name, "#475569")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">Fenwick vs Segment Tree benchmark chart</title>",
        (
            "<desc id=\"desc\">"
            "Benchmark summary comparing RangeFenwick and a lazy segment tree, including throughput and average operation latencies."
            "</desc>"
        ),
        "<style>",
        "text { font-family: Inter, Arial, sans-serif; fill: #0f172a; }",
        ".muted { fill: #475569; }",
        ".subtle { fill: #64748b; }",
        ".title { font-size: 26px; font-weight: 700; }",
        ".section { font-size: 16px; font-weight: 700; }",
        ".label { font-size: 13px; font-weight: 600; }",
        ".body { font-size: 13px; }",
        ".small { font-size: 12px; }",
        ".value { font-size: 28px; font-weight: 700; }",
        ".card { fill: #f8fafc; stroke: #cbd5e1; stroke-width: 1; }",
        ".panel { fill: #ffffff; stroke: #dbe3ee; stroke-width: 1; }",
        ".grid { stroke: #e2e8f0; stroke-width: 1; }",
        "</style>",
        '<rect width="100%" height="100%" fill="#f8fafc" />',
        '<text class="title" x="40" y="48">Fenwick vs Segment Tree benchmark</text>',
        (
            f'<text class="body muted" x="40" y="74">'
            f'Preset {payload["preset"]} • Size {payload["size"]} • {payload["operations"]} operations/run • '
            f'{payload["repeats"]} repeats • seed {payload["seed"]}'
            "</text>"
        ),
    ]

    summary_cards = [
        ("Faster strategy", payload["faster_strategy"], f'{_format_metric(payload["speedup"])}x speedup vs slower baseline'),
        (
            "Workload preset",
            payload["preset"],
            "Q "
            f'{int(round(payload["query_ratio"] * 100))}% • '
            "A "
            f'{int(round(payload["range_add_ratio"] * 100))}% • '
            "S "
            f'{int(round(payload["set_ratio"] * 100))}% • '
            f'width≤{payload["max_range_width"]}',
        ),
        ("Correctness", "verified" if payload["correctness_verified"] else "failed", "Query checksum and final total matched across both structures"),
        (
            "Operation mix",
            f'{payload["operation_mix"]["range_sum"]}/{payload["operation_mix"]["range_add"]}/{payload["operation_mix"]["point_set"]}',
            "range_sum / range_add / point_set operations in the shared workload",
        ),
    ]
    for index, (label, value, detail) in enumerate(summary_cards):
        x = 40 + index * (card_width + 20)
        lines.extend(
            [
                f'<rect class="card" x="{x}" y="98" width="{card_width}" height="{card_height}" rx="14" />',
                f'<text class="small subtle" x="{x + 18}" y="124">{html.escape(label)}</text>',
                f'<text class="value" x="{x + 18}" y="160">{html.escape(str(value))}</text>',
                f'<text class="small muted" x="{x + 18}" y="180">{html.escape(detail)}</text>',
            ]
        )

    legend_x = 930
    legend_y = 112
    lines.extend(
        [
            '<text class="label" x="930" y="116">Legend</text>',
        ]
    )
    for idx, result in enumerate(strategies):
        y = legend_y + 22 + idx * 22
        color = strategy_color(result["strategy"])
        lines.extend(
            [
                f'<rect x="{legend_x}" y="{y}" width="12" height="12" rx="3" fill="{color}" />',
                f'<text class="small muted" x="{legend_x + 18}" y="{y + 10}">{html.escape(result["strategy"])}</text>',
            ]
        )

    lines.extend(
        [
            '<rect class="panel" x="40" y="222" width="460" height="236" rx="16" />',
            '<text class="section" x="64" y="254">Throughput comparison</text>',
            '<text class="small muted" x="64" y="274">Longer bars mean more operations completed per second on the same workload.</text>',
        ]
    )
    ops_label_x = 64
    ops_bar_x = 64
    ops_value_x = ops_bar_x + ops_bar_width + 12
    for index, result in enumerate(strategies):
        y = 318 + index * 68
        color = strategy_color(result["strategy"])
        bar_width = 0 if max_ops == 0 else round((result["operations_per_second"] / max_ops) * ops_bar_width, 1)
        lines.extend(
            [
                f'<text class="label" x="{ops_label_x}" y="{y - 10}">{html.escape(result["strategy"])}</text>',
                f'<rect x="{ops_bar_x}" y="{y}" width="{ops_bar_width}" height="20" rx="10" fill="#e2e8f0" />',
                f'<rect x="{ops_bar_x}" y="{y}" width="{bar_width}" height="20" rx="10" fill="{color}" />',
                f'<text class="body muted" x="{ops_value_x}" y="{y + 15}">{_format_metric(result["operations_per_second"], 2)} ops/sec</text>',
                f'<text class="small subtle" x="{ops_bar_x}" y="{y + 38}">avg {_format_metric(result["average_seconds"], 6)}s, best {_format_metric(result["best_seconds"], 6)}s</text>',
            ]
        )

    latency_panel_x = 530
    lines.extend(
        [
            f'<rect class="panel" x="{latency_panel_x}" y="222" width="470" height="380" rx="16" />',
            f'<text class="section" x="{latency_panel_x + 24}" y="254">Per-operation latency</text>',
            f'<text class="small muted" x="{latency_panel_x + 24}" y="274">Shorter bars are better because they show less average time spent per operation kind.</text>',
        ]
    )
    for row_index, (kind, label) in enumerate(latency_rows):
        row_top = 316 + row_index * 102
        lines.extend(
            [
                f'<text class="label" x="{latency_panel_x + 24}" y="{row_top}">{html.escape(label)}</text>',
                f'<line class="grid" x1="{latency_panel_x + 24}" y1="{row_top + 8}" x2="{latency_panel_x + 430}" y2="{row_top + 8}" />',
            ]
        )
        for index, result in enumerate(strategies):
            y = row_top + 20 + index * 30
            value = result["timings"][kind]["average_microseconds"]
            bar_width = 0 if max_latency == 0 else round((value / max_latency) * latency_bar_width, 1)
            color = strategy_color(result["strategy"])
            lines.extend(
                [
                    f'<text class="small muted" x="{latency_panel_x + 24}" y="{y + 12}">{html.escape(result["strategy"])}</text>',
                    f'<rect x="{latency_panel_x + 118}" y="{y}" width="{latency_bar_width}" height="16" rx="8" fill="#e2e8f0" />',
                    f'<rect x="{latency_panel_x + 118}" y="{y}" width="{bar_width}" height="16" rx="8" fill="{color}" />',
                    f'<text class="small muted" x="{latency_panel_x + 360}" y="{y + 12}">{_format_metric(value)} μs</text>',
                ]
            )

    lines.extend(
        [
            '<rect class="panel" x="40" y="480" width="460" height="122" rx="16" />',
            '<text class="section" x="64" y="512">Why this chart matters</text>',
            '<text class="body muted" x="64" y="538">• The same deterministic preset workload is replayed through both data structures, so the timing comparison stays apples-to-apples.</text>',
            '<text class="body muted" x="64" y="562">• Correctness gates the benchmark, the chart is only meaningful when both structures agree on checksum and final total.</text>',
            '<text class="body muted" x="64" y="586">• RangeFenwick stays compact and wins this sample, while the segment tree remains a strong baseline for richer range-update/query stories.</text>',
        ]
    )

    footer_y = 642
    lines.extend(
        [
            f'<text class="small subtle" x="40" y="{footer_y}">Generated by fenwick_tree_range_query_lab.py benchmark --svg-output ...</text>',
            f'<text class="small subtle" text-anchor="end" x="1000" y="{footer_y}">viewBox 0 0 {width} {height}</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def render_preset_comparison_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fenwick workload preset comparison",
        "",
        f"- compared presets: {', '.join(row['preset'] for row in payload['presets'])}",
        f"- size: {payload['size']}",
        f"- operations per run: {payload['operations']}",
        f"- repeats: {payload['repeats']}",
        f"- seed: {payload['seed']}",
        f"- all correctness checks passed: {payload['all_correctness_verified']}",
        f"- average Fenwick speedup: {payload['average_speedup']}x",
        "",
        "## Preset snapshot",
        "",
        "| Preset | Mix (Q/A/S) | Dominant op | Faster strategy | Speedup | Fenwick ops/sec | Segment ops/sec | Artifact bundle |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["presets"]:
        lines.append(
            "| "
            f"{row['preset']} | "
            f"{_format_ratio_pct(row['query_ratio'])}/{_format_ratio_pct(row['range_add_ratio'])}/{_format_ratio_pct(row['set_ratio'])} | "
            f"{OPERATION_LABELS[row['dominant_operation']]} | "
            f"{row['faster_strategy']} | "
            f"{row['speedup']}x | "
            f"{row['range_fenwick_ops_per_second']} | "
            f"{row['segment_tree_ops_per_second']} | "
            f"[Markdown]({row['artifacts']['markdown']}) / [SVG]({row['artifacts']['svg']}) |"
        )
    lines.extend(
        [
            "",
            "## Operation-level winners",
            "",
            "| Operation | Fenwick wins | Segment tree wins |",
            "| --- | ---: | ---: |",
        ]
    )
    for kind, label in OPERATION_LABELS.items():
        lines.append(
            f"| {label} | {payload['operation_winner_counts']['range-fenwick'][kind]} | {payload['operation_winner_counts']['segment-tree'][kind]} |"
        )
    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            (
                f"- Strongest Fenwick edge: `{payload['strongest_edge']['preset']}` at `"
                f"{payload['strongest_edge']['speedup']}x`, where `{OPERATION_LABELS[payload['strongest_edge']['dominant_operation']]}` dominates the workload."
            ),
            (
                f"- Tightest race: `{payload['tightest_race']['preset']}` at `{payload['tightest_race']['speedup']}x`, which is the closest this benchmark pack gets to a near draw."
            ),
            (
                f"- Fastest absolute throughput for RangeFenwick: `{payload['fastest_fenwick']['preset']}` at `"
                f"{payload['fastest_fenwick']['operations_per_second']} ops/sec`."
            ),
            (
                f"- Fastest absolute throughput for the segment tree baseline: `{payload['fastest_segment_tree']['preset']}` at `"
                f"{payload['fastest_segment_tree']['operations_per_second']} ops/sec`."
            ),
            "- Use the linked per-preset Markdown and SVG artifacts when you want the deeper single-workload breakdown beside this summary dashboard.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_preset_comparison_html(payload: dict[str, Any]) -> str:
    rows_html = []
    for row in payload["presets"]:
        artifact_links = " ".join(
            (
                f'<a href="{html.escape(path)}">{label}</a>'
                for label, path in (
                    ("JSON", row["artifacts"]["json"]),
                    ("CSV", row["artifacts"]["csv"]),
                    ("Markdown", row["artifacts"]["markdown"]),
                    ("SVG", row["artifacts"]["svg"]),
                )
            )
        )
        rows_html.append(
            "<tr>"
            f"<td><strong>{html.escape(row['preset'])}</strong><div class=\"muted\">{html.escape(row['preset_description'])}</div></td>"
            f"<td>{_format_ratio_pct(row['query_ratio'])} / {_format_ratio_pct(row['range_add_ratio'])} / {_format_ratio_pct(row['set_ratio'])}</td>"
            f"<td>{html.escape(OPERATION_LABELS[row['dominant_operation']])}</td>"
            f"<td>{html.escape(row['faster_strategy'])}</td>"
            f"<td>{html.escape(_format_metric(row['speedup']))}x</td>"
            f"<td>{html.escape(_format_metric(row['range_fenwick_ops_per_second'], 2))}</td>"
            f"<td>{html.escape(_format_metric(row['segment_tree_ops_per_second'], 2))}</td>"
            f"<td>{artifact_links}</td>"
            "</tr>"
        )

    operation_rows = []
    for kind, label in OPERATION_LABELS.items():
        operation_rows.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{payload['operation_winner_counts']['range-fenwick'][kind]}</td>"
            f"<td>{payload['operation_winner_counts']['segment-tree'][kind]}</td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Fenwick workload preset comparison</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: Inter, Arial, sans-serif;
        background: #f8fafc;
        color: #0f172a;
      }}
      body {{ margin: 0; background: #f8fafc; }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 40px 28px 56px; }}
      h1, h2 {{ margin: 0 0 16px; }}
      p {{ line-height: 1.55; }}
      .muted {{ color: #475569; font-size: 0.95rem; }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin: 24px 0 32px; }}
      .card {{ background: white; border: 1px solid #dbe3ee; border-radius: 18px; padding: 18px 20px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06); }}
      .eyebrow {{ text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.74rem; color: #64748b; margin-bottom: 10px; }}
      .value {{ font-size: 1.9rem; font-weight: 700; }}
      table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #dbe3ee; border-radius: 18px; overflow: hidden; }}
      th, td {{ padding: 12px 14px; border-bottom: 1px solid #e2e8f0; vertical-align: top; text-align: left; }}
      th {{ background: #eff6ff; font-size: 0.9rem; }}
      tr:last-child td {{ border-bottom: none; }}
      .section {{ margin-top: 30px; }}
      .callouts {{ background: white; border: 1px solid #dbe3ee; border-radius: 18px; padding: 20px 22px; }}
      ul {{ margin: 0; padding-left: 20px; line-height: 1.6; }}
      a {{ color: #2563eb; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </style>
  </head>
  <body>
    <main>
      <p class=\"eyebrow\">Fenwick Tree Range Query Lab</p>
      <h1>Workload preset comparison dashboard</h1>
      <p class=\"muted\">Shared settings: size {payload['size']}, {payload['operations']} operations per run, {payload['repeats']} repeats, seed {payload['seed']}. This dashboard contrasts all committed workload presets so reviewers can see where RangeFenwick keeps a strong lead and where the lazy segment tree baseline closes the gap.</p>

      <section class=\"grid\">
        <article class=\"card\">
          <div class=\"eyebrow\">Compared presets</div>
          <div class=\"value\">{payload['preset_count']}</div>
          <div class=\"muted\">{html.escape(', '.join(row['preset'] for row in payload['presets']))}</div>
        </article>
        <article class=\"card\">
          <div class=\"eyebrow\">Strongest Fenwick edge</div>
          <div class=\"value\">{html.escape(payload['strongest_edge']['preset'])}</div>
          <div class=\"muted\">{html.escape(_format_metric(payload['strongest_edge']['speedup']))}x speedup, dominant {html.escape(OPERATION_LABELS[payload['strongest_edge']['dominant_operation']])}</div>
        </article>
        <article class=\"card\">
          <div class=\"eyebrow\">Tightest race</div>
          <div class=\"value\">{html.escape(payload['tightest_race']['preset'])}</div>
          <div class=\"muted\">{html.escape(_format_metric(payload['tightest_race']['speedup']))}x speedup</div>
        </article>
        <article class=\"card\">
          <div class=\"eyebrow\">Average speedup</div>
          <div class=\"value\">{html.escape(_format_metric(payload['average_speedup']))}x</div>
          <div class=\"muted\">All correctness checks passed: {payload['all_correctness_verified']}</div>
        </article>
      </section>

      <section class=\"section\">
        <h2>Preset-by-preset snapshot</h2>
        <table>
          <thead>
            <tr>
              <th>Preset</th>
              <th>Mix (Q/A/S)</th>
              <th>Dominant operation</th>
              <th>Faster strategy</th>
              <th>Speedup</th>
              <th>Fenwick ops/sec</th>
              <th>Segment ops/sec</th>
              <th>Related artifacts</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows_html)}
          </tbody>
        </table>
      </section>

      <section class=\"section\">
        <h2>Operation-level winners</h2>
        <table>
          <thead>
            <tr>
              <th>Operation</th>
              <th>Fenwick wins</th>
              <th>Segment tree wins</th>
            </tr>
          </thead>
          <tbody>
            {''.join(operation_rows)}
          </tbody>
        </table>
      </section>

      <section class=\"section callouts\">
        <h2>Recruiter-facing takeaways</h2>
        <ul>
          <li>RangeFenwick posts its strongest relative advantage on <strong>{html.escape(payload['strongest_edge']['preset'])}</strong>, where the dominant operation mix is <strong>{html.escape(OPERATION_LABELS[payload['strongest_edge']['dominant_operation']])}</strong>.</li>
          <li>The closest contest is <strong>{html.escape(payload['tightest_race']['preset'])}</strong>, which keeps the story honest by showing where a lazy segment tree nearly catches up.</li>
          <li>The fastest absolute Fenwick throughput appears on <strong>{html.escape(payload['fastest_fenwick']['preset'])}</strong> at <strong>{html.escape(_format_metric(payload['fastest_fenwick']['operations_per_second'], 2))} ops/sec</strong>.</li>
          <li>Use this dashboard as the landing page, then open each linked preset artifact when you want the deeper JSON, Markdown, CSV, or SVG evidence.</li>
        </ul>
      </section>
    </main>
  </body>
</html>
"""


def render_preset_comparison_svg(payload: dict[str, Any]) -> str:
    width = 1180
    row_height = 68
    panel_height = 88 + len(payload["presets"]) * row_height
    footer_y = 222 + panel_height + 24
    height = footer_y + 114
    speedup_panel_width = 500
    throughput_panel_width = 560
    strategy_colors = {
        "range-fenwick": "#2563eb",
        "segment-tree": "#f97316",
    }
    max_speedup = max(row["speedup"] for row in payload["presets"])
    max_ops = max(
        max(row["range_fenwick_ops_per_second"], row["segment_tree_ops_per_second"])
        for row in payload["presets"]
    )

    def strategy_color(name: str) -> str:
        return strategy_colors.get(name, "#475569")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Fenwick preset comparison dashboard</title>',
        '<desc id="desc">A multi-preset benchmark dashboard comparing RangeFenwick and a lazy segment tree across balanced, query-heavy, update-heavy, and point-set-heavy workloads.</desc>',
        '<style>',
        'text { font-family: Inter, Arial, sans-serif; fill: #0f172a; }',
        '.muted { fill: #475569; }',
        '.subtle { fill: #64748b; }',
        '.title { font-size: 28px; font-weight: 700; }',
        '.section { font-size: 16px; font-weight: 700; }',
        '.label { font-size: 13px; font-weight: 600; }',
        '.body { font-size: 13px; }',
        '.small { font-size: 12px; }',
        '.value { font-size: 26px; font-weight: 700; }',
        '.card { fill: #ffffff; stroke: #dbe3ee; stroke-width: 1; }',
        '.panel { fill: #ffffff; stroke: #dbe3ee; stroke-width: 1; }',
        '</style>',
        '<rect width="100%" height="100%" fill="#f8fafc" />',
        '<text class="title" x="40" y="50">Fenwick workload preset comparison</text>',
        f'<text class="body muted" x="40" y="76">Size {payload["size"]} • {payload["operations"]} operations/run • {payload["repeats"]} repeats • seed {payload["seed"]} • average speedup {_format_metric(payload["average_speedup"])}x</text>',
    ]

    card_width = 260
    summary_cards = [
        ("Compared presets", str(payload["preset_count"]), ", ".join(row["preset"] for row in payload["presets"])),
        (
            "Strongest edge",
            payload["strongest_edge"]["preset"],
            f'{_format_metric(payload["strongest_edge"]["speedup"])}x with {OPERATION_LABELS[payload["strongest_edge"]["dominant_operation"]].lower()} dominance',
        ),
        (
            "Tightest race",
            payload["tightest_race"]["preset"],
            f'{_format_metric(payload["tightest_race"]["speedup"])}x speedup',
        ),
        (
            "Fastest Fenwick preset",
            payload["fastest_fenwick"]["preset"],
            f'{_format_metric(payload["fastest_fenwick"]["operations_per_second"], 2)} ops/sec',
        ),
    ]
    for index, (label, value, detail) in enumerate(summary_cards):
        x = 40 + index * (card_width + 16)
        lines.extend(
            [
                f'<rect class="card" x="{x}" y="102" width="{card_width}" height="92" rx="16" />',
                f'<text class="small subtle" x="{x + 18}" y="128">{html.escape(label)}</text>',
                f'<text class="value" x="{x + 18}" y="162">{html.escape(str(value))}</text>',
                f'<text class="small muted" x="{x + 18}" y="182">{html.escape(detail)}</text>',
            ]
        )

    lines.extend(
        [
            f'<rect class="panel" x="40" y="222" width="{speedup_panel_width}" height="{panel_height}" rx="18" />',
            '<text class="section" x="64" y="252">Speedup by preset</text>',
            '<text class="small muted" x="64" y="272">Longer bars show where RangeFenwick gains more relative distance over the segment tree baseline.</text>',
            f'<rect class="panel" x="580" y="222" width="{throughput_panel_width}" height="{panel_height}" rx="18" />',
            '<text class="section" x="604" y="252">Throughput by preset</text>',
            '<text class="small muted" x="604" y="272">Each row keeps the same workload settings but swaps the preset mix.</text>',
        ]
    )

    for index, row in enumerate(payload["presets"]):
        row_top = 316 + index * row_height
        speedup_bar_width = 320
        throughput_bar_width = 170
        speedup_width = 0 if max_speedup == 0 else round((row["speedup"] / max_speedup) * speedup_bar_width, 1)
        fenwick_width = 0 if max_ops == 0 else round((row["range_fenwick_ops_per_second"] / max_ops) * throughput_bar_width, 1)
        segment_width = 0 if max_ops == 0 else round((row["segment_tree_ops_per_second"] / max_ops) * throughput_bar_width, 1)
        lines.extend(
            [
                f'<text class="label" x="64" y="{row_top - 8}">{html.escape(row["preset"])}</text>',
                f'<text class="small subtle" x="64" y="{row_top + 10}">Q/A/S {_format_ratio_pct(row["query_ratio"])} / {_format_ratio_pct(row["range_add_ratio"])} / {_format_ratio_pct(row["set_ratio"])} • dominant {html.escape(OPERATION_LABELS[row["dominant_operation"]].lower())}</text>',
                f'<rect x="64" y="{row_top + 20}" width="{speedup_bar_width}" height="18" rx="9" fill="#e2e8f0" />',
                f'<rect x="64" y="{row_top + 20}" width="{speedup_width}" height="18" rx="9" fill="#2563eb" />',
                f'<text class="small muted" x="396" y="{row_top + 34}">{_format_metric(row["speedup"])}x</text>',
                f'<text class="label" x="604" y="{row_top - 8}">{html.escape(row["preset"])}</text>',
                f'<rect x="604" y="{row_top + 10}" width="{throughput_bar_width}" height="14" rx="7" fill="#dbeafe" />',
                f'<rect x="604" y="{row_top + 10}" width="{fenwick_width}" height="14" rx="7" fill="{strategy_color("range-fenwick")}" />',
                f'<text class="small muted" x="782" y="{row_top + 21}">Fenwick {_format_metric(row["range_fenwick_ops_per_second"], 2)}</text>',
                f'<rect x="604" y="{row_top + 34}" width="{throughput_bar_width}" height="14" rx="7" fill="#ffedd5" />',
                f'<rect x="604" y="{row_top + 34}" width="{segment_width}" height="14" rx="7" fill="{strategy_color("segment-tree")}" />',
                f'<text class="small muted" x="782" y="{row_top + 45}">Segment {_format_metric(row["segment_tree_ops_per_second"], 2)}</text>',
            ]
        )

    lines.extend(
        [
            f'<rect class="panel" x="40" y="{footer_y}" width="1100" height="86" rx="18" />',
            f'<text class="section" x="64" y="{footer_y + 30}">Why this dashboard matters</text>',
            f'<text class="body muted" x="64" y="{footer_y + 54}">• Strongest edge: {html.escape(payload["strongest_edge"]["preset"])} at {_format_metric(payload["strongest_edge"]["speedup"])}x. Tightest race: {html.escape(payload["tightest_race"]["preset"])} at {_format_metric(payload["tightest_race"]["speedup"])}x.</text>',
            f'<text class="body muted" x="64" y="{footer_y + 76}">• Use this as the one-screen summary, then open the linked Markdown or SVG preset artifacts for the deeper single-workload breakdown.</text>',
            '</svg>',
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
        preset=args.preset,
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
    if args.svg_output:
        output = Path(args.svg_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_benchmark_svg(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


def compare_presets_command(args: argparse.Namespace) -> int:
    payload = (
        compare_saved_benchmark_presets(args.presets)
        if args.use_saved_json
        else compare_benchmark_presets(
            presets=args.presets,
            size=args.size,
            operations=args.operations,
            seed=args.seed,
            repeats=args.repeats,
            value_min=args.value_min,
            value_max=args.value_max,
            delta_min=args.delta_min,
            delta_max=args.delta_max,
        )
    )
    if args.output:
        save_benchmark_json(Path(args.output), payload)
    if args.markdown_output:
        output = Path(args.markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_preset_comparison_markdown(payload), encoding="utf-8")
    if args.html_output:
        output = Path(args.html_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_preset_comparison_html(payload), encoding="utf-8")
    if args.svg_output:
        output = Path(args.svg_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_preset_comparison_svg(payload), encoding="utf-8")
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
    benchmark_parser.add_argument(
        "--preset",
        choices=sorted(BENCHMARK_PRESETS),
        default=DEFAULT_BENCHMARK_PRESET,
        help="named workload mix to use before any explicit ratio overrides",
    )
    benchmark_parser.add_argument("--query-ratio", type=float, help="override the preset range-sum ratio")
    benchmark_parser.add_argument("--set-ratio", type=float, help="override the preset point-set ratio")
    benchmark_parser.add_argument("--max-range-width", type=int, help="override the preset maximum sampled range width")
    benchmark_parser.add_argument("--value-min", type=int, default=0)
    benchmark_parser.add_argument("--value-max", type=int, default=200)
    benchmark_parser.add_argument("--delta-min", type=int, default=-20)
    benchmark_parser.add_argument("--delta-max", type=int, default=20)
    benchmark_parser.add_argument("--output")
    benchmark_parser.add_argument("--csv-output")
    benchmark_parser.add_argument("--markdown-output")
    benchmark_parser.add_argument("--svg-output")
    benchmark_parser.set_defaults(func=benchmark_command)

    compare_parser = subparsers.add_parser(
        "compare-presets",
        help="compare multiple workload presets in one dashboard-oriented benchmark pack",
    )
    compare_parser.add_argument(
        "--presets",
        nargs="+",
        choices=sorted(BENCHMARK_PRESETS),
        default=list(DEFAULT_COMPARE_PRESETS),
        help="one or more named workload presets to contrast in a single report",
    )
    compare_parser.add_argument(
        "--use-saved-json",
        action="store_true",
        help="load the committed per-preset benchmark JSON artifacts instead of re-running the benchmark",
    )
    compare_parser.add_argument("--size", type=int, default=256, help="benchmark array size when re-running presets")
    compare_parser.add_argument("--operations", type=int, default=1000, help="operations per benchmark run when re-running presets")
    compare_parser.add_argument("--seed", type=int, default=7, help="seed used for generated values and operations when re-running presets")
    compare_parser.add_argument("--repeats", type=int, default=3, help="repeat count per preset when re-running presets")
    compare_parser.add_argument("--value-min", type=int, default=0, help="minimum generated starting value when re-running presets")
    compare_parser.add_argument("--value-max", type=int, default=200, help="maximum generated starting value when re-running presets")
    compare_parser.add_argument("--delta-min", type=int, default=-20, help="minimum generated range-add delta when re-running presets")
    compare_parser.add_argument("--delta-max", type=int, default=20, help="maximum generated range-add delta when re-running presets")
    compare_parser.add_argument("--output")
    compare_parser.add_argument("--markdown-output")
    compare_parser.add_argument("--html-output")
    compare_parser.add_argument("--svg-output")
    compare_parser.set_defaults(func=compare_presets_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
