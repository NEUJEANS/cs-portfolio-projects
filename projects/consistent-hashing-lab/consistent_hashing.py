from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence


def stable_hash(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


@dataclass(frozen=True)
class RingPoint:
    position: int
    physical_node: str
    virtual_node: str


class ConsistentHashRing:
    def __init__(self, nodes: Sequence[str] | None = None, virtual_nodes: int = 128) -> None:
        if virtual_nodes <= 0:
            raise ValueError("virtual_nodes must be positive")
        self.virtual_nodes = virtual_nodes
        self.nodes: list[str] = []
        self._ring: list[RingPoint] = []
        self._positions: list[int] = []
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node: str) -> None:
        if not node:
            raise ValueError("node name must be non-empty")
        if node in self.nodes:
            raise ValueError(f"duplicate node: {node}")
        self.nodes.append(node)
        for index in range(self.virtual_nodes):
            virtual_name = f"{node}#{index}"
            point = RingPoint(
                position=stable_hash(virtual_name),
                physical_node=node,
                virtual_node=virtual_name,
            )
            self._ring.append(point)
        self._ring.sort(key=lambda item: item.position)
        self._positions = [point.position for point in self._ring]

    def remove_node(self, node: str) -> None:
        if node not in self.nodes:
            raise ValueError(f"unknown node: {node}")
        self.nodes.remove(node)
        self._ring = [point for point in self._ring if point.physical_node != node]
        self._positions = [point.position for point in self._ring]

    def effective_replication_factor(self, replication_factor: int) -> int:
        if replication_factor <= 0:
            raise ValueError("replication_factor must be positive")
        return min(replication_factor, len(self.nodes))

    def get_nodes(self, key: str, replication_factor: int = 1) -> list[str]:
        if not self._ring:
            raise ValueError("ring has no nodes")

        distinct_target = self.effective_replication_factor(replication_factor)
        position = stable_hash(key)
        index = bisect.bisect_left(self._positions, position)
        if index == len(self._positions):
            index = 0

        selected: list[str] = []
        seen: set[str] = set()
        for offset in range(len(self._ring)):
            point = self._ring[(index + offset) % len(self._ring)]
            if point.physical_node in seen:
                continue
            selected.append(point.physical_node)
            seen.add(point.physical_node)
            if len(selected) == distinct_target:
                return selected

        return selected

    def get_node(self, key: str) -> str:
        return self.get_nodes(key, replication_factor=1)[0]

    def assign_keys(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, str] | dict[str, list[str]]:
        if replication_factor == 1:
            return {key: self.get_node(key) for key in keys}
        return {key: self.get_nodes(key, replication_factor=replication_factor) for key in keys}

    def distribution(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for nodes in self.assign_keys(keys, replication_factor=replication_factor).values():
            if isinstance(nodes, str):
                counts[nodes] += 1
            else:
                counts.update(nodes)
        return {node: counts.get(node, 0) for node in self.nodes}

    def load_report(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, object]:
        key_list = list(keys)
        effective_replication_factor = self.effective_replication_factor(replication_factor) if self.nodes else 0
        distribution = self.distribution(key_list, replication_factor=replication_factor)
        total_keys = len(key_list)
        loads = list(distribution.values())
        placement_count = total_keys * effective_replication_factor if self.nodes else 0
        average = placement_count / len(self.nodes) if self.nodes else 0.0
        return {
            "total_keys": total_keys,
            "nodes": len(self.nodes),
            "virtual_nodes_per_physical": self.virtual_nodes,
            "replication_factor": replication_factor,
            "effective_replication_factor": effective_replication_factor,
            "total_replica_placements": placement_count,
            "distribution": distribution,
            "max_load": max(loads) if loads else 0,
            "min_load": min(loads) if loads else 0,
            "average_load": average,
            "imbalance_ratio": (max(loads) / average) if loads and average else 0.0,
        }


def generate_keys(count: int, prefix: str = "key") -> list[str]:
    if count < 0:
        raise ValueError("count must be non-negative")
    return [f"{prefix}-{index}" for index in range(count)]


def simulate_remap(
    nodes: Sequence[str],
    keys: Sequence[str],
    virtual_nodes: int,
    add: str | None = None,
    remove: str | None = None,
    replication_factor: int = 1,
) -> dict[str, object]:
    if add and remove:
        raise ValueError("choose either add or remove, not both")
    before = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
    before_assignments = before.assign_keys(keys, replication_factor=replication_factor)

    if add:
        after_nodes = list(nodes)
        after_nodes.append(add)
    elif remove:
        after_nodes = [node for node in nodes if node != remove]
        if len(after_nodes) == len(nodes):
            raise ValueError(f"cannot remove unknown node: {remove}")
    else:
        raise ValueError("either add or remove must be provided")

    after = ConsistentHashRing(after_nodes, virtual_nodes=virtual_nodes)
    after_assignments = after.assign_keys(keys, replication_factor=replication_factor)

    moved = sorted(key for key in keys if before_assignments[key] != after_assignments[key])
    replica_placement_changes = 0
    for key in keys:
        before_nodes = before_assignments[key]
        after_nodes_for_key = after_assignments[key]
        if isinstance(before_nodes, str):
            if before_nodes != after_nodes_for_key:
                replica_placement_changes += 1
        else:
            replica_placement_changes += len(set(before_nodes).symmetric_difference(set(after_nodes_for_key)))

    return {
        "before_nodes": list(nodes),
        "after_nodes": after_nodes,
        "key_count": len(keys),
        "replication_factor": replication_factor,
        "effective_before_replication_factor": before.effective_replication_factor(replication_factor),
        "effective_after_replication_factor": after.effective_replication_factor(replication_factor),
        "moved_keys": len(moved),
        "movement_ratio": (len(moved) / len(keys)) if keys else 0.0,
        "replica_placement_changes": replica_placement_changes,
        "sample_moved_keys": moved[:10],
        "before_distribution": before.distribution(keys, replication_factor=replication_factor),
        "after_distribution": after.distribution(keys, replication_factor=replication_factor),
    }


def benchmark_virtual_nodes(
    nodes: Sequence[str],
    key_count: int,
    virtual_node_counts: Sequence[int],
    key_prefix: str = "key",
    replication_factor: int = 1,
    add: str | None = None,
    remove: str | None = None,
) -> dict[str, object]:
    if not virtual_node_counts:
        raise ValueError("virtual_node_counts must not be empty")

    keys = generate_keys(key_count, prefix=key_prefix)
    benchmark_points: list[dict[str, object]] = []
    seen_counts: set[int] = set()
    for virtual_nodes in virtual_node_counts:
        if virtual_nodes in seen_counts:
            continue
        seen_counts.add(virtual_nodes)
        ring = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
        load_report = ring.load_report(keys, replication_factor=replication_factor)
        point: dict[str, object] = {
            "virtual_nodes": virtual_nodes,
            "max_load": load_report["max_load"],
            "min_load": load_report["min_load"],
            "average_load": load_report["average_load"],
            "imbalance_ratio": load_report["imbalance_ratio"],
        }
        if add or remove:
            remap_summary = simulate_remap(
                nodes,
                keys,
                virtual_nodes=virtual_nodes,
                add=add,
                remove=remove,
                replication_factor=replication_factor,
            )
            point["moved_keys"] = remap_summary["moved_keys"]
            point["movement_ratio"] = remap_summary["movement_ratio"]
            point["replica_placement_changes"] = remap_summary["replica_placement_changes"]
        benchmark_points.append(point)

    best_imbalance = min(benchmark_points, key=lambda item: (item["imbalance_ratio"], item["virtual_nodes"]))
    payload: dict[str, object] = {
        "nodes": list(nodes),
        "node_count": len(nodes),
        "key_count": key_count,
        "replication_factor": replication_factor,
        "key_prefix": key_prefix,
        "virtual_node_counts": [point["virtual_nodes"] for point in benchmark_points],
        "series": benchmark_points,
        "best_imbalance_virtual_nodes": best_imbalance["virtual_nodes"],
        "best_imbalance_ratio": best_imbalance["imbalance_ratio"],
    }
    if add:
        payload["topology_change"] = {"action": "add", "node": add}
    elif remove:
        payload["topology_change"] = {"action": "remove", "node": remove}
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consistent hashing ring lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign = subparsers.add_parser("assign", help="assign keys to nodes")
    assign.add_argument("--nodes", nargs="+", required=True)
    assign.add_argument("--keys", nargs="+", required=True)
    assign.add_argument("--virtual-nodes", type=positive_int, default=128)
    assign.add_argument("--replication-factor", type=positive_int, default=1)

    report = subparsers.add_parser("report", help="show load distribution for generated keys")
    report.add_argument("--nodes", nargs="+", required=True)
    report.add_argument("--key-count", type=int, required=True)
    report.add_argument("--key-prefix", default="key")
    report.add_argument("--virtual-nodes", type=positive_int, default=128)
    report.add_argument("--replication-factor", type=positive_int, default=1)

    remap = subparsers.add_parser("remap", help="simulate node add/remove remapping")
    remap.add_argument("--nodes", nargs="+", required=True)
    remap.add_argument("--key-count", type=int, required=True)
    remap.add_argument("--key-prefix", default="key")
    remap.add_argument("--virtual-nodes", type=positive_int, default=128)
    remap.add_argument("--replication-factor", type=positive_int, default=1)
    remap_change = remap.add_mutually_exclusive_group(required=True)
    remap_change.add_argument("--add-node")
    remap_change.add_argument("--remove-node")

    benchmark = subparsers.add_parser(
        "benchmark",
        help="compare multiple virtual-node counts for load balance and optional remapping",
    )
    benchmark.add_argument("--nodes", nargs="+", required=True)
    benchmark.add_argument("--key-count", type=int, required=True)
    benchmark.add_argument("--key-prefix", default="key")
    benchmark.add_argument("--virtual-node-counts", nargs="+", type=positive_int, required=True)
    benchmark.add_argument("--replication-factor", type=positive_int, default=1)
    benchmark_change = benchmark.add_mutually_exclusive_group()
    benchmark_change.add_argument("--add-node")
    benchmark_change.add_argument("--remove-node")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "assign":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.assign_keys(args.keys, replication_factor=args.replication_factor)
    elif args.command == "report":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.load_report(
            generate_keys(args.key_count, args.key_prefix),
            replication_factor=args.replication_factor,
        )
    elif args.command == "remap":
        payload = simulate_remap(
            args.nodes,
            generate_keys(args.key_count, args.key_prefix),
            virtual_nodes=args.virtual_nodes,
            add=args.add_node,
            remove=args.remove_node,
            replication_factor=args.replication_factor,
        )
    else:
        payload = benchmark_virtual_nodes(
            args.nodes,
            key_count=args.key_count,
            virtual_node_counts=args.virtual_node_counts,
            key_prefix=args.key_prefix,
            replication_factor=args.replication_factor,
            add=args.add_node,
            remove=args.remove_node,
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
