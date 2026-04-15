from __future__ import annotations

import argparse
import csv
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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


def run_benchmark(nodes: int, edges: int, seed: int = 7) -> Dict[str, object]:
    if nodes < 2:
        raise ValueError("benchmark nodes must be at least 2")
    if edges < 1:
        raise ValueError("benchmark edges must be at least 1")

    rng = random.Random(seed)
    labels = [f"n{i}" for i in range(nodes)]
    network = UnionFindNetwork()

    started = time.perf_counter()
    cycle_edges = 0
    for _ in range(edges):
        left, right = rng.sample(labels, 2)
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


def maybe_write_report(payload: Dict[str, object], output_json: Path | None, output_csv: Path | None) -> None:
    if output_json:
        write_json_report(payload, output_json)
    if output_csv:
        write_benchmark_series_csv(payload, output_csv)


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
    parser.add_argument("--benchmark-nodes", type=int, default=1000, help="Number of nodes for benchmark mode")
    parser.add_argument("--benchmark-edges", type=int, default=5000, help="Number of random edges for benchmark mode")
    parser.add_argument("--benchmark-seed", type=int, default=7, help="Seed for reproducible benchmark mode")
    parser.add_argument("--output-json", type=Path, help="Write JSON output to a file in addition to stdout")
    parser.add_argument("--output-csv", type=Path, help="Write benchmark-series output as CSV")
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
        enabled_modes = sum(bool(flag) for flag in (args.script, args.edges_csv, args.benchmark, args.benchmark_series))
        if enabled_modes > 1:
            raise ValueError("choose only one of --script, --edges-csv, --benchmark, or --benchmark-series")
        if args.output_csv and not args.benchmark_series:
            raise ValueError("--output-csv requires --benchmark-series")

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
        else:
            result = _run_single_command(network, args.command)

        maybe_write_report(result, args.output_json, args.output_csv)
    except ValueError as exc:
        parser.error(str(exc))

    if args.json or args.script or args.edges_csv or args.benchmark or args.benchmark_series:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
