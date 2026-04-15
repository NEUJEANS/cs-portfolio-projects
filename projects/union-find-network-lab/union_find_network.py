from __future__ import annotations

import argparse
import csv
import json
import random
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class OperationResult:
    operation: str
    nodes: Tuple[str, ...]
    merged: bool | None = None
    connected: bool | None = None
    created_cycle: bool | None = None
    component_size: int | None = None
    root: str | None = None


class UnionFindNetwork:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
        self.size: Dict[str, int] = {}
        self.edge_count: Dict[str, int] = {}
        self.node_count = 0
        self.successful_unions = 0

    def add(self, node: str) -> None:
        if node in self.parent:
            return
        self.parent[node] = node
        self.rank[node] = 0
        self.size[node] = 1
        self.edge_count[node] = 0
        self.node_count += 1

    def find(self, node: str) -> str:
        if node not in self.parent:
            self.add(node)
        parent = self.parent[node]
        if parent != node:
            self.parent[node] = self.find(parent)
        return self.parent[node]

    def union(self, left: str, right: str) -> OperationResult:
        self.add(left)
        self.add(right)
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            self.edge_count[root_left] += 1
            return OperationResult(
                operation="union",
                nodes=(left, right),
                merged=False,
                connected=True,
                created_cycle=True,
                component_size=self.size[root_left],
                root=root_left,
            )

        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left

        self.parent[root_right] = root_left
        self.size[root_left] += self.size[root_right]
        self.edge_count[root_left] += self.edge_count[root_right] + 1
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1
        self.successful_unions += 1

        return OperationResult(
            operation="union",
            nodes=(left, right),
            merged=True,
            connected=True,
            created_cycle=False,
            component_size=self.size[root_left],
            root=root_left,
        )

    def connected(self, left: str, right: str) -> bool:
        if left not in self.parent or right not in self.parent:
            return False
        return self.find(left) == self.find(right)

    def component_summary(self, node: str) -> Dict[str, object]:
        root = self.find(node)
        return {
            "node": node,
            "root": root,
            "size": self.size[root],
            "edges": self.edge_count[root],
            "has_cycle": self.edge_count[root] >= self.size[root],
            "members": sorted(member for member in self.parent if self.find(member) == root),
        }

    def components(self) -> List[Dict[str, object]]:
        grouped: Dict[str, List[str]] = {}
        for node in self.parent:
            root = self.find(node)
            grouped.setdefault(root, []).append(node)
        summaries = []
        for root, members in grouped.items():
            summaries.append(
                {
                    "root": root,
                    "size": self.size[root],
                    "edges": self.edge_count[root],
                    "has_cycle": self.edge_count[root] >= self.size[root],
                    "members": sorted(members),
                }
            )
        return sorted(summaries, key=lambda item: (-item["size"], item["root"]))

    def stats(self) -> Dict[str, object]:
        components = self.components()
        return {
            "nodes": self.node_count,
            "components": len(components),
            "largest_component": max((item["size"] for item in components), default=0),
            "cyclic_components": sum(1 for item in components if item["has_cycle"]),
            "successful_unions": self.successful_unions,
        }

    def run_script(self, operations: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
        if not isinstance(operations, list):
            raise ValueError("operations must be a list of {op, args} objects")

        results: List[Dict[str, object]] = []
        for step in operations:
            if not isinstance(step, dict) or "op" not in step:
                raise ValueError("each operation must be an object with an 'op' field")
            raw_args = step.get("args", [])
            if not isinstance(raw_args, list):
                raise ValueError("operation args must be a list")
            op = str(step["op"])
            args = [str(value) for value in raw_args]
            if op == "add":
                if len(args) != 1:
                    raise ValueError("add requires exactly 1 argument")
                self.add(args[0])
                results.append({"operation": op, "node": args[0]})
            elif op == "union":
                if len(args) != 2:
                    raise ValueError("union requires exactly 2 arguments")
                result = self.union(args[0], args[1])
                results.append({
                    "operation": op,
                    "nodes": list(result.nodes),
                    "merged": result.merged,
                    "created_cycle": result.created_cycle,
                    "component_size": result.component_size,
                    "root": result.root,
                })
            elif op == "connected":
                if len(args) != 2:
                    raise ValueError("connected requires exactly 2 arguments")
                results.append({"operation": op, "nodes": args, "connected": self.connected(args[0], args[1])})
            elif op == "component":
                if len(args) != 1:
                    raise ValueError("component requires exactly 1 argument")
                results.append({"operation": op, "summary": self.component_summary(args[0])})
            elif op == "stats":
                results.append({"operation": op, "stats": self.stats()})
            else:
                raise ValueError(f"unsupported operation: {op}")
        return results


def load_edges_from_csv(csv_path: Path) -> List[Tuple[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV edge file must include a header row")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        missing = {"source", "target"} - set(normalized)
        if missing:
            raise ValueError("CSV edge file must contain source,target columns")

        edges: List[Tuple[str, str]] = []
        for index, row in enumerate(reader, start=2):
            source = (row.get(normalized["source"]) or "").strip()
            target = (row.get(normalized["target"]) or "").strip()
            if not source or not target:
                raise ValueError(f"CSV edge file row {index} must define non-empty source and target values")
            edges.append((source, target))
    return edges


def run_csv_import(csv_path: Path, snapshot_every: int = 0) -> Dict[str, object]:
    edges = load_edges_from_csv(csv_path)
    network = UnionFindNetwork()
    snapshots: List[Dict[str, object]] = []
    cycle_edges = 0

    for index, (source, target) in enumerate(edges, start=1):
        result = network.union(source, target)
        if result.created_cycle:
            cycle_edges += 1
        if snapshot_every > 0 and index % snapshot_every == 0:
            snapshots.append(
                {
                    "edge_index": index,
                    "edge": [source, target],
                    "stats": network.stats(),
                }
            )

    summary: Dict[str, object] = {
        "mode": "csv-import",
        "edge_file": str(csv_path),
        "edges_processed": len(edges),
        "cycle_edges": cycle_edges,
        "stats": network.stats(),
        "components": network.components(),
    }
    if snapshot_every > 0:
        if not snapshots or snapshots[-1]["edge_index"] != len(edges):
            snapshots.append(
                {
                    "edge_index": len(edges),
                    "edge": list(edges[-1]) if edges else [],
                    "stats": network.stats(),
                }
            )
        summary["snapshots"] = snapshots
    return summary


def generate_random_edges(nodes: int, edges: int, seed: int = 7) -> List[Tuple[str, str]]:
    if nodes < 2:
        raise ValueError("benchmark nodes must be at least 2")
    if edges < 1:
        raise ValueError("benchmark edges must be at least 1")

    rng = random.Random(seed)
    labels = [f"n{i}" for i in range(nodes)]
    return [tuple(rng.sample(labels, 2)) for _ in range(edges)]


def run_benchmark(nodes: int, edges: int, seed: int = 7) -> Dict[str, object]:
    random_edges = generate_random_edges(nodes, edges, seed=seed)
    network = UnionFindNetwork()

    started = time.perf_counter()
    cycle_edges = 0
    for left, right in random_edges:
        result = network.union(left, right)
        cycle_edges += 1 if result.created_cycle else 0
    elapsed = time.perf_counter() - started

    return {
        "mode": "benchmark",
        "seed": seed,
        "nodes_requested": nodes,
        "edges_requested": edges,
        "elapsed_ms": round(elapsed * 1000, 3),
        "edges_per_second": round(edges / elapsed, 3) if elapsed else None,
        "cycle_edges": cycle_edges,
        "stats": network.stats(),
    }


def run_benchmark_series(nodes: int, edge_counts: List[int], seed: int = 7) -> Dict[str, object]:
    if not edge_counts:
        raise ValueError("benchmark series requires at least one edge count")
    if any(edge_count < 1 for edge_count in edge_counts):
        raise ValueError("benchmark series edge counts must all be at least 1")

    runs = [run_benchmark(nodes=nodes, edges=edge_count, seed=seed) for edge_count in edge_counts]
    throughput_values = [run["edges_per_second"] for run in runs if isinstance(run.get("edges_per_second"), (int, float))]

    return {
        "mode": "benchmark-series",
        "seed": seed,
        "nodes_requested": nodes,
        "edge_counts": edge_counts,
        "runs": runs,
        "summary": {
            "fastest_edges_per_second": max(throughput_values) if throughput_values else None,
            "slowest_edges_per_second": min(throughput_values) if throughput_values else None,
            "median_edges_per_second": _median(throughput_values),
        },
    }


def run_recompute_comparison(
    nodes: int,
    edges: int,
    seed: int = 7,
    checkpoint_every: int = 0,
) -> Dict[str, object]:
    random_edges = generate_random_edges(nodes, edges, seed=seed)
    interval = checkpoint_every or max(1, edges // 8)

    union_find = UnionFindNetwork()
    union_started = time.perf_counter()
    union_cycle_edges = 0
    union_checkpoints: List[Dict[str, object]] = []
    for index, (left, right) in enumerate(random_edges, start=1):
        result = union_find.union(left, right)
        union_cycle_edges += 1 if result.created_cycle else 0
        if index % interval == 0 or index == edges:
            union_elapsed_ms = (time.perf_counter() - union_started) * 1000
            union_checkpoints.append(
                {
                    "edge_index": index,
                    "elapsed_ms": round(union_elapsed_ms, 3),
                    "largest_component": union_find.stats()["largest_component"],
                }
            )
    union_elapsed = time.perf_counter() - union_started

    adjacency: Dict[str, set[str]] = {f"n{i}": set() for i in range(nodes)}
    baseline_cycle_edges = 0
    baseline_checkpoints: List[Dict[str, object]] = []
    baseline_started = time.perf_counter()
    latest_baseline_stats: Dict[str, int] = {"components": nodes, "largest_component": 1, "cyclic_components": 0}
    for index, (left, right) in enumerate(random_edges, start=1):
        if graph_path_exists(adjacency, left, right):
            baseline_cycle_edges += 1
        adjacency[left].add(right)
        adjacency[right].add(left)
        latest_baseline_stats = recompute_graph_stats(adjacency)
        if index % interval == 0 or index == edges:
            baseline_elapsed_ms = (time.perf_counter() - baseline_started) * 1000
            baseline_checkpoints.append(
                {
                    "edge_index": index,
                    "elapsed_ms": round(baseline_elapsed_ms, 3),
                    "largest_component": latest_baseline_stats["largest_component"],
                }
            )
    baseline_elapsed = time.perf_counter() - baseline_started

    union_elapsed_ms = round(union_elapsed * 1000, 3)
    baseline_elapsed_ms = round(baseline_elapsed * 1000, 3)
    speedup = round(baseline_elapsed / union_elapsed, 3) if union_elapsed else None

    return {
        "mode": "connectivity-comparison",
        "seed": seed,
        "nodes_requested": nodes,
        "edges_requested": edges,
        "checkpoint_every": interval,
        "input_edges": [[left, right] for left, right in random_edges[: min(10, len(random_edges))]],
        "union_find": {
            "elapsed_ms": union_elapsed_ms,
            "edges_per_second": round(edges / union_elapsed, 3) if union_elapsed else None,
            "cycle_edges": union_cycle_edges,
            "stats": union_find.stats(),
            "checkpoints": union_checkpoints,
        },
        "recompute_baseline": {
            "strategy": "full BFS component recomputation after every edge",
            "elapsed_ms": baseline_elapsed_ms,
            "edges_per_second": round(edges / baseline_elapsed, 3) if baseline_elapsed else None,
            "cycle_edges": baseline_cycle_edges,
            "stats": {
                "nodes": nodes,
                **latest_baseline_stats,
            },
            "checkpoints": baseline_checkpoints,
        },
        "summary": {
            "speedup_vs_recompute": speedup,
            "same_largest_component": union_find.stats()["largest_component"] == latest_baseline_stats["largest_component"],
            "same_component_count": union_find.stats()["components"] == latest_baseline_stats["components"],
        },
    }


def graph_path_exists(adjacency: Dict[str, set[str]], source: str, target: str) -> bool:
    if source == target:
        return True
    if source not in adjacency or target not in adjacency:
        return False
    queue: Deque[str] = deque([source])
    visited = {source}
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor == target:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False


def recompute_graph_stats(adjacency: Dict[str, set[str]]) -> Dict[str, int]:
    visited: set[str] = set()
    components = 0
    largest_component = 0
    cyclic_components = 0

    for node in adjacency:
        if node in visited:
            continue
        components += 1
        queue: Deque[str] = deque([node])
        visited.add(node)
        component_nodes = 0
        degree_sum = 0
        while queue:
            current = queue.popleft()
            component_nodes += 1
            degree_sum += len(adjacency[current])
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        largest_component = max(largest_component, component_nodes)
        edges_in_component = degree_sum // 2
        if edges_in_component >= component_nodes:
            cyclic_components += 1

    return {
        "components": components,
        "largest_component": largest_component,
        "cyclic_components": cyclic_components,
    }


def _median(values: List[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2, 3)


def write_json_report(payload: Dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_benchmark_series_csv(payload: Dict[str, object], output_path: Path) -> None:
    if payload.get("mode") != "benchmark-series":
        raise ValueError("CSV export currently supports benchmark-series output only")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError("benchmark-series payload must include a runs list")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "seed",
                "nodes_requested",
                "edges_requested",
                "elapsed_ms",
                "edges_per_second",
                "cycle_edges",
                "stats_nodes",
                "stats_components",
                "stats_largest_component",
                "stats_cyclic_components",
                "stats_successful_unions",
            ],
        )
        writer.writeheader()
        for run in runs:
            stats = run.get("stats", {}) if isinstance(run, dict) else {}
            writer.writerow(
                {
                    "seed": run.get("seed") if isinstance(run, dict) else None,
                    "nodes_requested": run.get("nodes_requested") if isinstance(run, dict) else None,
                    "edges_requested": run.get("edges_requested") if isinstance(run, dict) else None,
                    "elapsed_ms": run.get("elapsed_ms") if isinstance(run, dict) else None,
                    "edges_per_second": run.get("edges_per_second") if isinstance(run, dict) else None,
                    "cycle_edges": run.get("cycle_edges") if isinstance(run, dict) else None,
                    "stats_nodes": stats.get("nodes") if isinstance(stats, dict) else None,
                    "stats_components": stats.get("components") if isinstance(stats, dict) else None,
                    "stats_largest_component": stats.get("largest_component") if isinstance(stats, dict) else None,
                    "stats_cyclic_components": stats.get("cyclic_components") if isinstance(stats, dict) else None,
                    "stats_successful_unions": stats.get("successful_unions") if isinstance(stats, dict) else None,
                }
            )


def write_comparison_markdown(payload: Dict[str, object], output_path: Path) -> None:
    if payload.get("mode") != "connectivity-comparison":
        raise ValueError("Markdown export currently supports connectivity-comparison output only")

    union_find = payload.get("union_find")
    recompute = payload.get("recompute_baseline")
    summary = payload.get("summary")
    if not isinstance(union_find, dict) or not isinstance(recompute, dict) or not isinstance(summary, dict):
        raise ValueError("connectivity-comparison payload must include union_find, recompute_baseline, and summary objects")

    union_stats = union_find.get("stats") if isinstance(union_find.get("stats"), dict) else {}
    baseline_stats = recompute.get("stats") if isinstance(recompute.get("stats"), dict) else {}
    sample_edges = payload.get("input_edges") if isinstance(payload.get("input_edges"), list) else []
    sample_pairs = []
    for edge in sample_edges[:3]:
        if isinstance(edge, list) and len(edge) == 2:
            sample_pairs.append(f"`{edge[0]}->{edge[1]}`")

    speedup = summary.get("speedup_vs_recompute", "n/a")
    checkpoint_every = payload.get("checkpoint_every", "n/a")
    edge_count = payload.get("edges_requested", "n/a")
    node_count = payload.get("nodes_requested", "n/a")
    union_eps = union_find.get("edges_per_second", "n/a")
    baseline_eps = recompute.get("edges_per_second", "n/a")
    sample_text = ", ".join(sample_pairs) if sample_pairs else "n/a"
    markdown = f'''# Union-Find vs BFS recomputation summary

> Reproducible connectivity-comparison artifact for `union-find-network-lab`.

## Headline
- Processed **{edge_count}** random edges across **{node_count}** nodes with checkpoints every **{checkpoint_every}** edges.
- Union-find finished in **{union_find.get("elapsed_ms", "n/a")} ms** (**{union_eps} edges/s**) versus **{recompute.get("elapsed_ms", "n/a")} ms** (**{baseline_eps} edges/s**) for repeated BFS recomputation.
- Measured speedup: **{speedup}x**.
- Result parity: same component count = **{summary.get("same_component_count", False)}**, same largest component = **{summary.get("same_largest_component", False)}**.

## Why it matters
Union-find is a strong fit for **incremental connectivity** workloads because each new edge updates component state directly, while the baseline must walk the graph again after every insertion. This artifact shows the algorithmic advantage with the exact same random edge stream.

## Result snapshot
- Union-find components: **{union_stats.get("components", "n/a")}**
- Union-find largest component: **{union_stats.get("largest_component", "n/a")}**
- Union-find cycle edges: **{union_find.get("cycle_edges", "n/a")}**
- Baseline components: **{baseline_stats.get("components", "n/a")}**
- Baseline largest component: **{baseline_stats.get("largest_component", "n/a")}**
- Baseline cycle edges: **{recompute.get("cycle_edges", "n/a")}**
- Sample input edges: {sample_text}

## Portfolio-ready takeaway
For streaming network links, service-dependency updates, or social-graph edge ingestion, union-find preserves the same final connectivity answer while avoiding the repeated full-graph scans that make naive recomputation collapse at scale.
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")


def load_chart_source(chart_input: Path) -> Dict[str, object]:
    if not chart_input.exists():
        raise ValueError(f"chart input does not exist: {chart_input}")
    suffix = chart_input.suffix.lower()
    if suffix == ".json":
        payload = json.loads(chart_input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("chart JSON input must decode to an object")
        return payload
    if suffix == ".csv":
        with chart_input.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return {"mode": "benchmark-series-csv", "runs": rows, "source": str(chart_input)}
    raise ValueError("chart input must be a .json or .csv artifact")


def build_svg_chart(payload: Dict[str, object], title: str | None = None) -> str:
    mode = payload.get("mode")
    if mode in {"benchmark-series", "benchmark-series-csv"}:
        return _build_benchmark_series_svg(payload, title=title)
    if mode == "csv-import":
        return _build_csv_import_svg(payload, title=title)
    if mode == "connectivity-comparison":
        return _build_connectivity_comparison_svg(payload, title=title)
    raise ValueError("chart rendering currently supports benchmark-series, csv-import, and connectivity-comparison artifacts only")
def write_svg_chart(payload: Dict[str, object], output_path: Path, title: str | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_svg_chart(payload, title=title), encoding="utf-8")


def _build_benchmark_series_svg(payload: Dict[str, object], title: str | None = None) -> str:
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("benchmark-series chart input must include a non-empty runs list")

    throughput_points: List[Tuple[float, float]] = []
    largest_component_points: List[Tuple[float, float]] = []
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("benchmark-series runs must be objects")
        edges = _coerce_float(run.get("edges_requested"), "edges_requested")
        throughput = _coerce_float(run.get("edges_per_second"), "edges_per_second")
        largest_component = _coerce_nested_float(
            run,
            primary_path=("stats", "largest_component"),
            fallback_key="stats_largest_component",
            field_name="largest_component",
        )
        throughput_points.append((edges, throughput))
        largest_component_points.append((edges, largest_component))

    chart_title = title or "Union-Find benchmark throughput + graph growth"
    subtitle = "edges requested vs throughput and largest connected component"
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    footer = (
        f"median throughput: {summary.get('median_edges_per_second', 'n/a')} edges/s; includes largest-component trend"
        if summary
        else "reproducible benchmark-series artifact with dual-axis portfolio chart"
    )
    return _wrap_dual_axis_svg(
        chart_title=chart_title,
        subtitle=subtitle,
        x_axis_label="Edges requested",
        left_axis_label="Edges / second",
        right_axis_label="Largest component size",
        left_series={"name": "Throughput", "color": "#2563eb", "points": throughput_points},
        right_series={"name": "Largest component", "color": "#7c3aed", "points": largest_component_points},
        footer=footer,
    )


def _build_csv_import_svg(payload: Dict[str, object], title: str | None = None) -> str:
    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError("csv-import chart input must include non-empty snapshots")

    points: List[Tuple[float, float]] = []
    labels: List[str] = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            raise ValueError("csv-import snapshots must be objects")
        stats = snapshot.get("stats")
        if not isinstance(stats, dict):
            raise ValueError("csv-import snapshots must include stats objects")
        edge_index = _coerce_float(snapshot.get("edge_index"), "edge_index")
        largest_component = _coerce_float(stats.get("largest_component"), "largest_component")
        points.append((edge_index, largest_component))
        labels.append(str(int(edge_index)) if edge_index.is_integer() else f"{edge_index:g}")

    chart_title = title or "Union-Find component growth"
    subtitle = "processed edges vs largest component size"
    y_label = "Largest component size"
    polyline, circles, x_ticks, y_ticks = _render_xy_plot(points, labels, x_axis_label="Edges processed")
    footer = f"cycle edges detected: {payload.get('cycle_edges', 'n/a')}"
    return _wrap_svg(chart_title, subtitle, y_label, polyline, circles, x_ticks, y_ticks, footer)


def _build_connectivity_comparison_svg(payload: Dict[str, object], title: str | None = None) -> str:
    union_find = payload.get("union_find")
    recompute = payload.get("recompute_baseline")
    if not isinstance(union_find, dict) or not isinstance(recompute, dict):
        raise ValueError("connectivity-comparison chart input must include union_find and recompute_baseline objects")
    union_checkpoints = union_find.get("checkpoints")
    recompute_checkpoints = recompute.get("checkpoints")
    if not isinstance(union_checkpoints, list) or not isinstance(recompute_checkpoints, list):
        raise ValueError("connectivity-comparison chart input must include checkpoint lists")

    union_points = [
        (_coerce_float(point.get("edge_index"), "edge_index"), _coerce_float(point.get("elapsed_ms"), "elapsed_ms"))
        for point in union_checkpoints
        if isinstance(point, dict)
    ]
    recompute_points = [
        (_coerce_float(point.get("edge_index"), "edge_index"), _coerce_float(point.get("elapsed_ms"), "elapsed_ms"))
        for point in recompute_checkpoints
        if isinstance(point, dict)
    ]
    if not union_points or not recompute_points:
        raise ValueError("connectivity-comparison chart input must include non-empty checkpoint points")

    chart_title = title or "Union-Find vs BFS recomputation"
    subtitle = "cumulative elapsed time while adding the same random edges"
    footer = f"speedup vs recompute: {payload.get('summary', {}).get('speedup_vs_recompute', 'n/a')}x"
    return _wrap_multi_series_svg(
        chart_title=chart_title,
        subtitle=subtitle,
        y_axis_label="Elapsed milliseconds",
        x_axis_label="Edges processed",
        series=[
            {"name": "Union-Find", "color": "#2563eb", "points": union_points},
            {"name": "BFS recompute", "color": "#dc2626", "points": recompute_points},
        ],
        footer=footer,
    )


def _render_xy_plot(
    points: Sequence[Tuple[float, float]],
    x_labels: Sequence[str],
    *,
    x_axis_label: str,
) -> Tuple[str, str, str, str]:
    if len(points) != len(x_labels):
        raise ValueError("point and label counts must match")
    if not points:
        raise ValueError("chart rendering requires at least one point")

    width = 960
    height = 540
    left = 90
    right = 40
    top = 90
    bottom = 90
    plot_width = width - left - right
    plot_height = height - top - bottom

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    min_x = min(x_values)
    max_x = max(x_values)
    min_y = 0.0
    max_y = max(y_values)
    if max_x == min_x:
        max_x += 1.0
    if max_y == min_y:
        max_y += 1.0

    def project_x(value: float) -> float:
        return left + ((value - min_x) / (max_x - min_x)) * plot_width

    def project_y(value: float) -> float:
        return top + plot_height - ((value - min_y) / (max_y - min_y)) * plot_height

    projected = [(project_x(x), project_y(y)) for x, y in points]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
    circle_markup = "\n".join(
        (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#2563eb" />'
            f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" '
            f'font-size="12" fill="#1f2937">{_xml_escape(label)}</text>'
        )
        for (x, y), label in zip(projected, x_labels)
    )

    x_tick_markup = []
    for (x, _), label in zip(projected, x_labels):
        x_tick_markup.append(f'<line x1="{x:.1f}" y1="{top + plot_height:.1f}" x2="{x:.1f}" y2="{top + plot_height + 8:.1f}" stroke="#6b7280" stroke-width="1" />')
        x_tick_markup.append(
            f'<text x="{x:.1f}" y="{top + plot_height + 28:.1f}" text-anchor="middle" font-size="12" fill="#374151">{_xml_escape(label)}</text>'
        )
    x_tick_markup.append(
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 24:.1f}" text-anchor="middle" font-size="14" fill="#111827">{_xml_escape(x_axis_label)}</text>'
    )

    y_tick_markup = []
    for step in range(5):
        value = min_y + ((max_y - min_y) * step / 4)
        y = project_y(value)
        label = f"{value:.0f}" if max_y >= 10 else f"{value:.2f}".rstrip("0").rstrip(".")
        y_tick_markup.append(
            f'<line x1="{left:.1f}" y1="{y:.1f}" x2="{left + plot_width:.1f}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        y_tick_markup.append(
            f'<text x="{left - 12:.1f}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="#374151">{_xml_escape(label)}</text>'
        )

    return polyline, circle_markup, "\n".join(x_tick_markup), "\n".join(y_tick_markup)


def _wrap_multi_series_svg(
    *,
    chart_title: str,
    subtitle: str,
    y_axis_label: str,
    x_axis_label: str,
    series: Sequence[Dict[str, object]],
    footer: str,
) -> str:
    if not series:
        raise ValueError("multi-series chart requires at least one series")

    width = 960
    height = 540
    left = 90
    right = 40
    top = 90
    bottom = 90
    plot_width = width - left - right
    plot_height = height - top - bottom

    all_points = [point for entry in series for point in entry.get("points", []) if isinstance(point, tuple)]
    if not all_points:
        raise ValueError("multi-series chart requires at least one point")
    x_values = [point[0] for point in all_points]
    y_values = [point[1] for point in all_points]
    min_x = min(x_values)
    max_x = max(x_values)
    min_y = 0.0
    max_y = max(y_values)
    if max_x == min_x:
        max_x += 1.0
    if max_y == min_y:
        max_y += 1.0

    def project_x(value: float) -> float:
        return left + ((value - min_x) / (max_x - min_x)) * plot_width

    def project_y(value: float) -> float:
        return top + plot_height - ((value - min_y) / (max_y - min_y)) * plot_height

    x_tick_values = sorted({point[0] for point in all_points})
    x_ticks = []
    for value in x_tick_values:
        x = project_x(value)
        label = str(int(value)) if float(value).is_integer() else f"{value:g}"
        x_ticks.append(f'<line x1="{x:.1f}" y1="{top + plot_height:.1f}" x2="{x:.1f}" y2="{top + plot_height + 8:.1f}" stroke="#6b7280" stroke-width="1" />')
        x_ticks.append(f'<text x="{x:.1f}" y="{top + plot_height + 28:.1f}" text-anchor="middle" font-size="12" fill="#374151">{_xml_escape(label)}</text>')
    x_ticks.append(f'<text x="{left + plot_width / 2:.1f}" y="{height - 24:.1f}" text-anchor="middle" font-size="14" fill="#111827">{_xml_escape(x_axis_label)}</text>')

    y_ticks = []
    for step in range(5):
        value = min_y + ((max_y - min_y) * step / 4)
        y = project_y(value)
        label = f"{value:.0f}" if max_y >= 10 else f"{value:.2f}".rstrip("0").rstrip(".")
        y_ticks.append(f'<line x1="{left:.1f}" y1="{y:.1f}" x2="{left + plot_width:.1f}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />')
        y_ticks.append(f'<text x="{left - 12:.1f}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="#374151">{_xml_escape(label)}</text>')

    plot_markup = []
    legend_markup = []
    for index, entry in enumerate(series):
        name = str(entry.get("name", f"Series {index + 1}"))
        color = str(entry.get("color", "#2563eb"))
        points = entry.get("points", [])
        if not isinstance(points, list):
            raise ValueError("multi-series chart series points must be a list")
        projected = [(project_x(x), project_y(y)) for x, y in points]
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
        plot_markup.append(f'<polyline fill="none" stroke="{_xml_escape(color)}" stroke-width="3" points="{polyline}" />')
        for x, y in projected:
            plot_markup.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{_xml_escape(color)}" />')
        legend_y = 92 + index * 22
        legend_markup.append(f'<rect x="700" y="{legend_y - 10}" width="14" height="14" fill="{_xml_escape(color)}" rx="2" />')
        legend_markup.append(f'<text x="722" y="{legend_y + 2}" font-size="13" fill="#1f2937">{_xml_escape(name)}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">
  <title>{_xml_escape(chart_title)}</title>
  <desc>{_xml_escape(subtitle)}</desc>
  <rect width="960" height="540" fill="#ffffff" />
  <text x="90" y="42" font-size="26" font-weight="700" fill="#111827">{_xml_escape(chart_title)}</text>
  <text x="90" y="68" font-size="14" fill="#4b5563">{_xml_escape(subtitle)}</text>
  <line x1="90" y1="90" x2="90" y2="450" stroke="#111827" stroke-width="2" />
  <line x1="90" y1="450" x2="920" y2="450" stroke="#111827" stroke-width="2" />
  {' '.join(y_ticks)}
  <text x="24" y="270" font-size="14" fill="#111827" transform="rotate(-90 24 270)" text-anchor="middle">{_xml_escape(y_axis_label)}</text>
  {' '.join(plot_markup)}
  {' '.join(x_ticks)}
  {' '.join(legend_markup)}
  <text x="90" y="505" font-size="13" fill="#4b5563">{_xml_escape(footer)}</text>
</svg>
'''


def _wrap_dual_axis_svg(
    *,
    chart_title: str,
    subtitle: str,
    x_axis_label: str,
    left_axis_label: str,
    right_axis_label: str,
    left_series: Dict[str, object],
    right_series: Dict[str, object],
    footer: str,
) -> str:
    width = 960
    height = 540
    left = 90
    right = 90
    top = 90
    bottom = 90
    plot_width = width - left - right
    plot_height = height - top - bottom

    left_points = left_series.get("points")
    right_points = right_series.get("points")
    if not isinstance(left_points, list) or not left_points:
        raise ValueError("dual-axis chart requires a non-empty left series")
    if not isinstance(right_points, list) or not right_points:
        raise ValueError("dual-axis chart requires a non-empty right series")

    all_x = [point[0] for point in [*left_points, *right_points]]
    min_x = min(all_x)
    max_x = max(all_x)
    if max_x == min_x:
        max_x += 1.0

    left_max = max(point[1] for point in left_points)
    right_max = max(point[1] for point in right_points)
    if left_max == 0:
        left_max = 1.0
    if right_max == 0:
        right_max = 1.0

    def project_x(value: float) -> float:
        return left + ((value - min_x) / (max_x - min_x)) * plot_width

    def project_left_y(value: float) -> float:
        return top + plot_height - (value / left_max) * plot_height

    def project_right_y(value: float) -> float:
        return top + plot_height - (value / right_max) * plot_height

    x_tick_values: List[float] = []
    for value in [point[0] for point in left_points]:
        if value not in x_tick_values:
            x_tick_values.append(value)

    x_ticks = []
    for value in x_tick_values:
        x = project_x(value)
        label = str(int(value)) if float(value).is_integer() else f"{value:g}"
        x_ticks.append(f'<line x1="{x:.1f}" y1="{top + plot_height:.1f}" x2="{x:.1f}" y2="{top + plot_height + 8:.1f}" stroke="#6b7280" stroke-width="1" />')
        x_ticks.append(f'<text x="{x:.1f}" y="{top + plot_height + 28:.1f}" text-anchor="middle" font-size="12" fill="#374151">{_xml_escape(label)}</text>')
    x_ticks.append(f'<text x="{left + plot_width / 2:.1f}" y="{height - 24:.1f}" text-anchor="middle" font-size="14" fill="#111827">{_xml_escape(x_axis_label)}</text>')

    left_ticks = []
    right_ticks = []
    for step in range(5):
        left_value = left_max * step / 4
        y = project_left_y(left_value)
        left_label = f"{left_value:.0f}" if left_max >= 10 else f"{left_value:.2f}".rstrip("0").rstrip(".")
        left_ticks.append(f'<line x1="{left:.1f}" y1="{y:.1f}" x2="{left + plot_width:.1f}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />')
        left_ticks.append(f'<text x="{left - 12:.1f}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="#2563eb">{_xml_escape(left_label)}</text>')
        right_value = right_max * step / 4
        right_label = f"{right_value:.0f}" if right_max >= 10 else f"{right_value:.2f}".rstrip("0").rstrip(".")
        right_ticks.append(f'<text x="{left + plot_width + 12:.1f}" y="{y + 4:.1f}" text-anchor="start" font-size="12" fill="#7c3aed">{_xml_escape(right_label)}</text>')

    def render_series(points: List[Tuple[float, float]], color: str, projector: object) -> str:
        projected = [(project_x(x), projector(y)) for x, y in points]  # type: ignore[misc]
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
        circles = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{_xml_escape(color)}" />' for x, y in projected)
        return f'<polyline fill="none" stroke="{_xml_escape(color)}" stroke-width="3" points="{polyline}" />{circles}'

    left_color = str(left_series.get("color", "#2563eb"))
    right_color = str(right_series.get("color", "#7c3aed"))
    legend = [
        f'<rect x="640" y="82" width="14" height="14" fill="{_xml_escape(left_color)}" rx="2" />',
        f'<text x="662" y="94" font-size="13" fill="#1f2937">{_xml_escape(left_series.get("name", "Left series"))}</text>',
        f'<rect x="640" y="104" width="14" height="14" fill="{_xml_escape(right_color)}" rx="2" />',
        f'<text x="662" y="116" font-size="13" fill="#1f2937">{_xml_escape(right_series.get("name", "Right series"))}</text>',
    ]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">
  <title>{_xml_escape(chart_title)}</title>
  <desc>{_xml_escape(subtitle)}</desc>
  <rect width="960" height="540" fill="#ffffff" />
  <text x="90" y="42" font-size="26" font-weight="700" fill="#111827">{_xml_escape(chart_title)}</text>
  <text x="90" y="68" font-size="14" fill="#4b5563">{_xml_escape(subtitle)}</text>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827" stroke-width="2" />
  <line x1="{left + plot_width}" y1="{top}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827" stroke-width="2" />
  <line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827" stroke-width="2" />
  {' '.join(left_ticks)}
  {' '.join(right_ticks)}
  <text x="24" y="270" font-size="14" fill="#2563eb" transform="rotate(-90 24 270)" text-anchor="middle">{_xml_escape(left_axis_label)}</text>
  <text x="936" y="270" font-size="14" fill="#7c3aed" transform="rotate(90 936 270)" text-anchor="middle">{_xml_escape(right_axis_label)}</text>
  {render_series(left_points, left_color, project_left_y)}
  {render_series(right_points, right_color, project_right_y)}
  {' '.join(x_ticks)}
  {' '.join(legend)}
  <text x="90" y="505" font-size="13" fill="#4b5563">{_xml_escape(footer)}</text>
</svg>
'''


def _wrap_svg(
    title: str,
    subtitle: str,
    y_axis_label: str,
    polyline: str,
    circles: str,
    x_ticks: str,
    y_ticks: str,
    footer: str,
) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">
  <title>{_xml_escape(title)}</title>
  <desc>{_xml_escape(subtitle)}</desc>
  <rect width="960" height="540" fill="#ffffff" />
  <text x="90" y="42" font-size="26" font-weight="700" fill="#111827">{_xml_escape(title)}</text>
  <text x="90" y="68" font-size="14" fill="#4b5563">{_xml_escape(subtitle)}</text>
  <line x1="90" y1="90" x2="90" y2="450" stroke="#111827" stroke-width="2" />
  <line x1="90" y1="450" x2="920" y2="450" stroke="#111827" stroke-width="2" />
  {y_ticks}
  <text x="24" y="270" font-size="14" fill="#111827" transform="rotate(-90 24 270)" text-anchor="middle">{_xml_escape(y_axis_label)}</text>
  <polyline fill="none" stroke="#2563eb" stroke-width="3" points="{polyline}" />
  {circles}
  {x_ticks}
  <text x="90" y="505" font-size="13" fill="#4b5563">{_xml_escape(footer)}</text>
</svg>
'''


def _coerce_float(value: object, field_name: str) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"chart input field {field_name} must be numeric") from exc


def _coerce_nested_float(
    row: Dict[str, object],
    *,
    primary_path: Tuple[str, str],
    fallback_key: str,
    field_name: str,
) -> float:
    nested = row.get(primary_path[0])
    if isinstance(nested, dict) and primary_path[1] in nested:
        return _coerce_float(nested.get(primary_path[1]), field_name)
    return _coerce_float(row.get(fallback_key), field_name)


def _xml_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def maybe_write_report(
    payload: Dict[str, object],
    output_json: Path | None,
    output_csv: Path | None,
    output_chart: Path | None = None,
    chart_title: str | None = None,
    output_markdown: Path | None = None,
) -> None:
    if output_json:
        write_json_report(payload, output_json)
    if output_csv:
        write_benchmark_series_csv(payload, output_csv)
    if output_chart:
        write_svg_chart(payload, output_chart, title=chart_title)
    if output_markdown:
        write_comparison_markdown(payload, output_markdown)


def parse_benchmark_series(raw_value: str) -> List[int]:
    values = [part.strip() for part in raw_value.split(",") if part.strip()]
    if not values:
        raise ValueError("--benchmark-series must include at least one positive integer edge count")
    try:
        edge_counts = [int(value) for value in values]
    except ValueError as exc:
        raise ValueError("--benchmark-series must be a comma-separated list of integers") from exc
    if any(edge_count < 1 for edge_count in edge_counts):
        raise ValueError("--benchmark-series edge counts must all be positive integers")
    return edge_counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Union-Find network lab")
    parser.add_argument("--script", type=Path, help="JSON file containing scripted operations")
    parser.add_argument("--edges-csv", type=Path, help="CSV file with source,target headers for bulk edge import")
    parser.add_argument("--snapshot-every", type=int, default=0, help="Record import snapshots every N CSV edges")
    parser.add_argument("--benchmark", action="store_true", help="Run a random union benchmark")
    parser.add_argument(
        "--benchmark-series",
        type=parse_benchmark_series,
        help="Comma-separated benchmark edge counts for a reproducible multi-run series, e.g. 1000,5000,10000",
    )
    parser.add_argument("--compare-recompute", action="store_true", help="Compare union-find against full BFS recomputation on the same random edge stream")
    parser.add_argument("--comparison-checkpoint-every", type=int, default=0, help="Record comparison checkpoints every N edges (default: edges/8)")
    parser.add_argument("--chart-input", type=Path, help="Existing benchmark-series JSON/CSV, csv-import JSON, or connectivity comparison JSON artifact to render as SVG")
    parser.add_argument("--benchmark-nodes", type=int, default=1000, help="Number of nodes for benchmark mode")
    parser.add_argument("--benchmark-edges", type=int, default=5000, help="Number of random edges for benchmark mode")
    parser.add_argument("--benchmark-seed", type=int, default=7, help="Seed for reproducible benchmark mode")
    parser.add_argument("--output-json", type=Path, help="Write JSON output to a file in addition to stdout")
    parser.add_argument("--output-csv", type=Path, help="Write benchmark-series output as CSV")
    parser.add_argument("--output-chart", type=Path, help="Write an SVG chart for benchmark-series, csv-import, or comparison output")
    parser.add_argument("--output-markdown", type=Path, help="Write a Markdown summary for connectivity comparison output")
    parser.add_argument("--chart-title", help="Optional custom SVG chart title")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("command", nargs="*", help="Optional single command, e.g. union a b")
    return parser


def _run_single_command(network: UnionFindNetwork, command: List[str]) -> Dict[str, object]:
    if not command:
        return {"stats": network.stats(), "components": network.components()}
    op, *args = command
    return network.run_script([{"op": op, "args": args}])[-1]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.snapshot_every < 0:
            raise ValueError("--snapshot-every must be zero or a positive integer")
        if args.comparison_checkpoint_every < 0:
            raise ValueError("--comparison-checkpoint-every must be zero or a positive integer")
        enabled_modes = sum(
            bool(flag)
            for flag in (
                args.script,
                args.edges_csv,
                args.benchmark,
                args.benchmark_series,
                args.compare_recompute,
                args.chart_input,
            )
        )
        if enabled_modes > 1:
            raise ValueError(
                "choose only one of --script, --edges-csv, --benchmark, --benchmark-series, --compare-recompute, or --chart-input"
            )
        if args.output_csv and not args.benchmark_series:
            raise ValueError("--output-csv requires --benchmark-series")
        if args.output_chart and not (args.edges_csv or args.benchmark_series or args.compare_recompute or args.chart_input):
            raise ValueError("--output-chart requires --edges-csv, --benchmark-series, --compare-recompute, or --chart-input")
        if args.output_markdown and not (args.compare_recompute or args.chart_input):
            raise ValueError("--output-markdown requires --compare-recompute or --chart-input")
        if args.chart_title and not args.output_chart:
            raise ValueError("--chart-title requires --output-chart")

        network = UnionFindNetwork()

        if args.script:
            operations = json.loads(args.script.read_text())
            result: Dict[str, object] = {
                "results": network.run_script(operations),
                "stats": network.stats(),
                "components": network.components(),
            }
        elif args.edges_csv:
            result = run_csv_import(args.edges_csv, snapshot_every=args.snapshot_every)
        elif args.benchmark:
            result = run_benchmark(args.benchmark_nodes, args.benchmark_edges, seed=args.benchmark_seed)
        elif args.benchmark_series:
            result = run_benchmark_series(args.benchmark_nodes, args.benchmark_series, seed=args.benchmark_seed)
        elif args.compare_recompute:
            result = run_recompute_comparison(
                args.benchmark_nodes,
                args.benchmark_edges,
                seed=args.benchmark_seed,
                checkpoint_every=args.comparison_checkpoint_every,
            )
        elif args.chart_input:
            result = load_chart_source(args.chart_input)
        else:
            result = _run_single_command(network, args.command)

        maybe_write_report(result, args.output_json, args.output_csv, args.output_chart, args.chart_title, args.output_markdown)
    except ValueError as exc:
        parser.error(str(exc))

    if (args.output_chart or args.output_markdown) and args.chart_input and not args.json:
        response = {"mode": result.get("mode")}
        if args.output_chart:
            response["chart_output"] = str(args.output_chart)
        if args.output_markdown:
            response["markdown_output"] = str(args.output_markdown)
        print(json.dumps(response, indent=2, sort_keys=True))
    elif args.json or args.script or args.edges_csv or args.benchmark or args.benchmark_series or args.compare_recompute or args.chart_input:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
