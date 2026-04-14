from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence


RING_SIZE = 2**128


def stable_hash(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


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

    def get_node(self, key: str) -> str:
        if not self._ring:
            raise ValueError("ring has no nodes")
        position = stable_hash(key)
        index = bisect.bisect_left(self._positions, position)
        if index == len(self._positions):
            index = 0
        return self._ring[index].physical_node

    def assign_keys(self, keys: Iterable[str]) -> dict[str, str]:
        return {key: self.get_node(key) for key in keys}

    def distribution(self, keys: Iterable[str]) -> dict[str, int]:
        counts = Counter(self.assign_keys(keys).values())
        return {node: counts.get(node, 0) for node in self.nodes}

    def load_report(self, keys: Iterable[str]) -> dict[str, object]:
        key_list = list(keys)
        distribution = self.distribution(key_list)
        total = len(key_list)
        loads = list(distribution.values())
        average = total / len(self.nodes) if self.nodes else 0.0
        return {
            "total_keys": total,
            "nodes": len(self.nodes),
            "virtual_nodes_per_physical": self.virtual_nodes,
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


def simulate_remap(nodes: Sequence[str], keys: Sequence[str], virtual_nodes: int, add: str | None = None, remove: str | None = None) -> dict[str, object]:
    if add and remove:
        raise ValueError("choose either add or remove, not both")
    before = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
    before_assignments = before.assign_keys(keys)

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
    after_assignments = after.assign_keys(keys)

    moved = sorted(key for key in keys if before_assignments[key] != after_assignments[key])
    return {
        "before_nodes": list(nodes),
        "after_nodes": after_nodes,
        "key_count": len(keys),
        "moved_keys": len(moved),
        "movement_ratio": (len(moved) / len(keys)) if keys else 0.0,
        "sample_moved_keys": moved[:10],
        "before_distribution": before.distribution(keys),
        "after_distribution": after.distribution(keys),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consistent hashing ring lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign = subparsers.add_parser("assign", help="assign keys to nodes")
    assign.add_argument("--nodes", nargs="+", required=True)
    assign.add_argument("--keys", nargs="+", required=True)
    assign.add_argument("--virtual-nodes", type=int, default=128)

    report = subparsers.add_parser("report", help="show load distribution for generated keys")
    report.add_argument("--nodes", nargs="+", required=True)
    report.add_argument("--key-count", type=int, required=True)
    report.add_argument("--key-prefix", default="key")
    report.add_argument("--virtual-nodes", type=int, default=128)

    remap = subparsers.add_parser("remap", help="simulate node add/remove remapping")
    remap.add_argument("--nodes", nargs="+", required=True)
    remap.add_argument("--key-count", type=int, required=True)
    remap.add_argument("--key-prefix", default="key")
    remap.add_argument("--virtual-nodes", type=int, default=128)
    remap.add_argument("--add-node")
    remap.add_argument("--remove-node")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "assign":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.assign_keys(args.keys)
    elif args.command == "report":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.load_report(generate_keys(args.key_count, args.key_prefix))
    else:
        payload = simulate_remap(
            args.nodes,
            generate_keys(args.key_count, args.key_prefix),
            virtual_nodes=args.virtual_nodes,
            add=args.add_node,
            remove=args.remove_node,
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
