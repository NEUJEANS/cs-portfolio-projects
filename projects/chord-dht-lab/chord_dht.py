from __future__ import annotations

import argparse
import hashlib
import json
from bisect import bisect_left
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class Node:
    name: str
    node_id: int


@dataclass(frozen=True)
class FingerEntry:
    start: int
    interval_end: int
    successor: str
    successor_id: int


@dataclass(frozen=True)
class LookupResult:
    key: str
    key_id: int
    start_node: str
    responsible_node: str
    responsible_node_id: int
    hop_count: int
    route: list[str]


class ChordRing:
    def __init__(self, m_bits: int, node_names: Iterable[str]) -> None:
        if m_bits <= 0:
            raise ValueError("m_bits must be positive")
        self.m_bits = m_bits
        self.ring_size = 2**m_bits
        self.nodes = self._build_nodes(node_names)
        if not self.nodes:
            raise ValueError("Chord ring requires at least one node")

    def _build_nodes(self, node_names: Iterable[str]) -> list[Node]:
        seen_ids: dict[int, str] = {}
        nodes: list[Node] = []
        for name in node_names:
            node_id = self.hash_identifier(name)
            if node_id in seen_ids:
                raise ValueError(
                    f"node hash collision between {seen_ids[node_id]!r} and {name!r} at id {node_id}"
                )
            seen_ids[node_id] = name
            nodes.append(Node(name=name, node_id=node_id))
        return sorted(nodes, key=lambda item: item.node_id)

    def hash_identifier(self, value: str) -> int:
        digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.ring_size

    def list_nodes(self) -> list[dict[str, int | str]]:
        return [{"name": node.name, "id": node.node_id} for node in self.nodes]

    def add_node(self, name: str) -> "ChordRing":
        if any(node.name == name for node in self.nodes):
            raise ValueError(f"node {name!r} already exists")
        return ChordRing(self.m_bits, [node.name for node in self.nodes] + [name])

    def without_nodes(self, names: Iterable[str]) -> "ChordRing":
        removed = set(names)
        remaining = [node.name for node in self.nodes if node.name not in removed]
        if not remaining:
            raise ValueError("cannot remove every node from the ring")
        if len(remaining) == len(self.nodes):
            return ChordRing(self.m_bits, [node.name for node in self.nodes])
        return ChordRing(self.m_bits, remaining)

    def get_node(self, name: str) -> Node:
        for node in self.nodes:
            if node.name == name:
                return node
        raise KeyError(f"unknown node {name!r}")

    def successor_for_id(self, identifier: int) -> Node:
        node_ids = [node.node_id for node in self.nodes]
        index = bisect_left(node_ids, identifier % self.ring_size)
        if index == len(self.nodes):
            index = 0
        return self.nodes[index]

    def predecessor_for_id(self, identifier: int) -> Node:
        node_ids = [node.node_id for node in self.nodes]
        index = bisect_left(node_ids, identifier % self.ring_size) - 1
        return self.nodes[index]

    def successor_of_node(self, node: Node) -> Node:
        index = self.nodes.index(node)
        return self.nodes[(index + 1) % len(self.nodes)]

    def predecessor_of_node(self, node: Node) -> Node:
        index = self.nodes.index(node)
        return self.nodes[(index - 1) % len(self.nodes)]

    def successor_list(self, node_name: str, count: int = 3) -> list[dict[str, int | str]]:
        if count <= 0:
            raise ValueError("successor list count must be positive")
        node = self.get_node(node_name)
        index = self.nodes.index(node)
        max_count = min(count, len(self.nodes) - 1)
        successors: list[dict[str, int | str]] = []
        for step in range(1, max_count + 1):
            successor = self.nodes[(index + step) % len(self.nodes)]
            successors.append({"name": successor.name, "id": successor.node_id})
        return successors

    def all_successor_lists(self, count: int = 3) -> dict[str, list[dict[str, int | str]]]:
        return {node.name: self.successor_list(node.name, count=count) for node in self.nodes}

    def finger_table(self, node_name: str) -> list[FingerEntry]:
        node = self.get_node(node_name)
        table: list[FingerEntry] = []
        for offset in range(self.m_bits):
            start = (node.node_id + (2**offset)) % self.ring_size
            interval_end = (node.node_id + (2 ** (offset + 1))) % self.ring_size
            successor = self.successor_for_id(start)
            table.append(
                FingerEntry(
                    start=start,
                    interval_end=interval_end,
                    successor=successor.name,
                    successor_id=successor.node_id,
                )
            )
        return table

    def all_finger_tables(self) -> dict[str, list[dict[str, int | str]]]:
        return {
            node.name: [asdict(entry) for entry in self.finger_table(node.name)]
            for node in self.nodes
        }

    def owns_identifier(self, node: Node, identifier: int) -> bool:
        predecessor = self.predecessor_of_node(node)
        return self._in_open_closed_interval(identifier, predecessor.node_id, node.node_id)

    def closest_preceding_finger(self, node: Node, identifier: int) -> Node:
        for entry in reversed(self.finger_table(node.name)):
            candidate = self.get_node(entry.successor)
            if self._in_open_open_interval(candidate.node_id, node.node_id, identifier):
                return candidate
        return self.successor_of_node(node)

    def lookup(self, start_node: str, key: str) -> LookupResult:
        current = self.get_node(start_node)
        key_id = self.hash_identifier(key)
        route = [current.name]
        max_hops = len(self.nodes) * (self.m_bits + 1)

        for _ in range(max_hops):
            if self.owns_identifier(current, key_id):
                return LookupResult(
                    key=key,
                    key_id=key_id,
                    start_node=start_node,
                    responsible_node=current.name,
                    responsible_node_id=current.node_id,
                    hop_count=len(route) - 1,
                    route=route,
                )

            next_node = self.closest_preceding_finger(current, key_id)
            if next_node.name == current.name:
                next_node = self.successor_of_node(current)
            current = next_node
            route.append(current.name)

        raise RuntimeError("lookup exceeded safe hop limit")

    def linear_lookup(self, start_node: str, key: str) -> LookupResult:
        current = self.get_node(start_node)
        key_id = self.hash_identifier(key)
        route = [current.name]

        for _ in range(len(self.nodes)):
            if self.owns_identifier(current, key_id):
                return LookupResult(
                    key=key,
                    key_id=key_id,
                    start_node=start_node,
                    responsible_node=current.name,
                    responsible_node_id=current.node_id,
                    hop_count=len(route) - 1,
                    route=route,
                )
            current = self.successor_of_node(current)
            route.append(current.name)

        raise RuntimeError("linear lookup exceeded safe hop limit")

    def benchmark_lookups(
        self, keys: Iterable[str], start_nodes: Iterable[str] | None = None
    ) -> dict[str, object]:
        key_list = list(keys)
        if not key_list:
            raise ValueError("benchmark requires at least one key")

        if start_nodes is None:
            start_names = [node.name for node in self.nodes]
        else:
            start_names = list(dict.fromkeys(start_nodes))
            if not start_names:
                raise ValueError("benchmark requires at least one start node")
            for name in start_names:
                self.get_node(name)

        cases: list[dict[str, object]] = []
        chord_hops: list[int] = []
        linear_hops: list[int] = []

        for start_node in start_names:
            for key in key_list:
                finger_result = self.lookup(start_node, key)
                linear_result = self.linear_lookup(start_node, key)
                cases.append(
                    {
                        "start_node": start_node,
                        "key": key,
                        "key_id": finger_result.key_id,
                        "responsible_node": finger_result.responsible_node,
                        "chord_hops": finger_result.hop_count,
                        "linear_hops": linear_result.hop_count,
                        "hop_savings": linear_result.hop_count - finger_result.hop_count,
                        "chord_route": finger_result.route,
                        "linear_route": linear_result.route,
                    }
                )
                chord_hops.append(finger_result.hop_count)
                linear_hops.append(linear_result.hop_count)

        improved_cases = sum(1 for case in cases if int(case["hop_savings"]) > 0)
        tied_cases = sum(1 for case in cases if int(case["hop_savings"]) == 0)
        slower_cases = len(cases) - improved_cases - tied_cases

        return {
            "m_bits": self.m_bits,
            "node_count": len(self.nodes),
            "nodes": self.list_nodes(),
            "keys": key_list,
            "start_nodes": start_names,
            "cases": cases,
            "summary": {
                "case_count": len(cases),
                "average_chord_hops": round(mean(chord_hops), 3),
                "average_linear_hops": round(mean(linear_hops), 3),
                "max_chord_hops": max(chord_hops),
                "max_linear_hops": max(linear_hops),
                "improved_cases": improved_cases,
                "tied_cases": tied_cases,
                "slower_cases": slower_cases,
                "total_hop_savings": sum(linear_hops) - sum(chord_hops),
            },
        }

    def assign_keys(self, keys: Iterable[str]) -> list[dict[str, int | str]]:
        assignments: list[dict[str, int | str]] = []
        for key in keys:
            key_id = self.hash_identifier(key)
            owner = self.successor_for_id(key_id)
            assignments.append(
                {
                    "key": key,
                    "key_id": key_id,
                    "owner": owner.name,
                    "owner_id": owner.node_id,
                }
            )
        return sorted(assignments, key=lambda item: (item["key_id"], item["key"]))

    def replica_plan(self, keys: Iterable[str], replica_count: int = 3) -> list[dict[str, object]]:
        if replica_count <= 0:
            raise ValueError("replica_count must be positive")
        max_replicas = min(replica_count, len(self.nodes))
        plan: list[dict[str, object]] = []
        for item in self.assign_keys(keys):
            owner = self.get_node(str(item["owner"]))
            owner_index = self.nodes.index(owner)
            replicas = []
            for offset in range(max_replicas):
                replica = self.nodes[(owner_index + offset) % len(self.nodes)]
                replicas.append({"name": replica.name, "id": replica.node_id})
            plan.append({**item, "replicas": replicas})
        return plan

    def resilience_report(
        self,
        keys: Iterable[str],
        failed_nodes: Iterable[str],
        replica_count: int = 3,
    ) -> dict[str, object]:
        failed = list(dict.fromkeys(failed_nodes))
        for name in failed:
            self.get_node(name)
        assignments = self.replica_plan(keys, replica_count=replica_count)
        cases: list[dict[str, object]] = []
        available_count = 0
        degraded_count = 0

        for assignment in assignments:
            replicas = assignment["replicas"]
            surviving = [replica for replica in replicas if replica["name"] not in failed]
            primary_owner = assignment["owner"]
            first_available = surviving[0]["name"] if surviving else None
            if surviving:
                available_count += 1
            if surviving and first_available != primary_owner:
                degraded_count += 1
            cases.append(
                {
                    "key": assignment["key"],
                    "key_id": assignment["key_id"],
                    "primary_owner": primary_owner,
                    "replicas": replicas,
                    "failed_nodes": failed,
                    "surviving_replicas": surviving,
                    "available": bool(surviving),
                    "served_by": first_available,
                    "degraded": bool(surviving) and first_available != primary_owner,
                }
            )

        return {
            "m_bits": self.m_bits,
            "node_count": len(self.nodes),
            "nodes": self.list_nodes(),
            "failed_nodes": failed,
            "replica_count": min(replica_count, len(self.nodes)),
            "cases": cases,
            "summary": {
                "case_count": len(cases),
                "available_cases": available_count,
                "unavailable_cases": len(cases) - available_count,
                "degraded_cases": degraded_count,
            },
        }

    def join_report(self, new_node: str, keys: Iterable[str]) -> dict[str, object]:
        updated_ring = self.add_node(new_node)
        before = {item["key"]: item for item in self.assign_keys(keys)}
        after = {item["key"]: item for item in updated_ring.assign_keys(keys)}
        moved = []
        for key, previous in before.items():
            current = after[key]
            if previous["owner"] != current["owner"]:
                moved.append(
                    {
                        "key": key,
                        "key_id": current["key_id"],
                        "from": previous["owner"],
                        "to": current["owner"],
                    }
                )
        moved.sort(key=lambda item: (item["key_id"], item["key"]))
        return {
            "m_bits": self.m_bits,
            "before_nodes": self.list_nodes(),
            "after_nodes": updated_ring.list_nodes(),
            "joined_node": new_node,
            "moved_keys": moved,
        }

    def stabilization_report(
        self,
        joined_node: str | None = None,
        failed_nodes: Iterable[str] | None = None,
        rounds: int = 3,
    ) -> dict[str, object]:
        if rounds <= 0:
            raise ValueError("rounds must be positive")

        failed = list(dict.fromkeys(failed_nodes or []))
        for name in failed:
            self.get_node(name)

        target_ring = self
        if joined_node is not None:
            if any(node.name == joined_node for node in self.nodes):
                raise ValueError(f"node {joined_node!r} already exists")
            target_ring = target_ring.add_node(joined_node)
        if failed:
            target_ring = target_ring.without_nodes(failed)

        target_names = [node.name for node in target_ring.nodes]
        if not target_names:
            raise ValueError("stabilization scenario must leave at least one live node")

        initial_state: dict[str, dict[str, object]] = {}
        for node in target_ring.nodes:
            if node.name == joined_node:
                initial_state[node.name] = {
                    "successor": node.name,
                    "predecessor": node.name,
                    "fingers": [node.name for _ in range(self.m_bits)],
                }
                continue

            source_ring = self.without_nodes(failed)
            source_node = source_ring.get_node(node.name)
            initial_state[node.name] = {
                "successor": source_ring.successor_of_node(source_node).name,
                "predecessor": source_ring.predecessor_of_node(source_node).name,
                "fingers": [entry.successor for entry in source_ring.finger_table(node.name)],
            }

        rounds_data: list[dict[str, object]] = [
            self._stabilization_round_summary(target_ring, initial_state, round_index=0, changed=[])
        ]
        current_state = initial_state

        for round_index in range(1, rounds + 1):
            next_state = {
                name: {
                    "successor": values["successor"],
                    "predecessor": values["predecessor"],
                    "fingers": list(values["fingers"]),
                }
                for name, values in current_state.items()
            }
            changed_nodes: list[str] = []
            finger_slot = (round_index - 1) % self.m_bits

            for node in target_ring.nodes:
                target_successor = target_ring.successor_of_node(node).name
                target_predecessor = target_ring.predecessor_of_node(node).name
                target_fingers = [entry.successor for entry in target_ring.finger_table(node.name)]
                state = next_state[node.name]
                before = (
                    state["successor"],
                    state["predecessor"],
                    list(state["fingers"]),
                )
                state["successor"] = target_successor
                state["predecessor"] = target_predecessor
                state["fingers"][finger_slot] = target_fingers[finger_slot]
                after = (state["successor"], state["predecessor"], list(state["fingers"]))
                if before != after:
                    changed_nodes.append(node.name)

            current_state = next_state
            rounds_data.append(
                self._stabilization_round_summary(
                    target_ring,
                    current_state,
                    round_index=round_index,
                    changed=changed_nodes,
                )
            )

        final_summary = rounds_data[-1]["summary"]
        return {
            "m_bits": self.m_bits,
            "target_node_count": len(target_ring.nodes),
            "base_nodes": self.list_nodes(),
            "target_nodes": target_ring.list_nodes(),
            "joined_node": joined_node,
            "failed_nodes": failed,
            "rounds_requested": rounds,
            "rounds": rounds_data,
            "summary": {
                "fully_stabilized": bool(final_summary["successor_matches"] == len(target_ring.nodes)
                and final_summary["predecessor_matches"] == len(target_ring.nodes)
                and final_summary["finger_matches"] == len(target_ring.nodes) * self.m_bits),
                "final_successor_matches": final_summary["successor_matches"],
                "final_predecessor_matches": final_summary["predecessor_matches"],
                "final_finger_matches": final_summary["finger_matches"],
                "total_fingers": len(target_ring.nodes) * self.m_bits,
            },
        }

    def _stabilization_round_summary(
        self,
        target_ring: "ChordRing",
        state: dict[str, dict[str, object]],
        round_index: int,
        changed: list[str],
    ) -> dict[str, object]:
        node_states: list[dict[str, object]] = []
        successor_matches = 0
        predecessor_matches = 0
        finger_matches = 0

        for node in target_ring.nodes:
            target_successor = target_ring.successor_of_node(node).name
            target_predecessor = target_ring.predecessor_of_node(node).name
            target_fingers = [entry.successor for entry in target_ring.finger_table(node.name)]
            observed = state[node.name]
            successor_ok = observed["successor"] == target_successor
            predecessor_ok = observed["predecessor"] == target_predecessor
            per_finger_matches = sum(
                1 for actual, expected in zip(observed["fingers"], target_fingers) if actual == expected
            )
            successor_matches += int(successor_ok)
            predecessor_matches += int(predecessor_ok)
            finger_matches += per_finger_matches
            node_states.append(
                {
                    "name": node.name,
                    "id": node.node_id,
                    "observed_successor": observed["successor"],
                    "target_successor": target_successor,
                    "successor_ok": successor_ok,
                    "observed_predecessor": observed["predecessor"],
                    "target_predecessor": target_predecessor,
                    "predecessor_ok": predecessor_ok,
                    "observed_fingers": list(observed["fingers"]),
                    "target_fingers": target_fingers,
                    "matching_fingers": per_finger_matches,
                    "total_fingers": self.m_bits,
                }
            )

        return {
            "round": round_index,
            "changed_nodes": changed,
            "nodes": node_states,
            "summary": {
                "successor_matches": successor_matches,
                "predecessor_matches": predecessor_matches,
                "finger_matches": finger_matches,
                "node_count": len(target_ring.nodes),
            },
        }

    def _in_open_closed_interval(self, value: int, start: int, end: int) -> bool:
        if start < end:
            return start < value <= end
        if start > end:
            return value > start or value <= end
        return True

    def _in_open_open_interval(self, value: int, start: int, end: int) -> bool:
        if start < end:
            return start < value < end
        if start > end:
            return value > start or value < end
        return value != start


def build_demo_payload() -> dict[str, object]:
    ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])
    sample_keys = ["report.pdf", "slides", "internship-notes", "compiler", "final-project"]
    route = ring.lookup("alpha", "compiler")
    return {
        "m_bits": ring.m_bits,
        "ring_size": ring.ring_size,
        "nodes": ring.list_nodes(),
        "finger_tables": ring.all_finger_tables(),
        "successor_lists": ring.all_successor_lists(count=3),
        "sample_assignments": ring.assign_keys(sample_keys),
        "lookup": asdict(route),
        "join_preview": ring.join_report("foxtrot", sample_keys),
        "resilience_preview": ring.resilience_report(
            sample_keys,
            failed_nodes=["echo"],
            replica_count=3,
        ),
        "stabilization_preview": ring.stabilization_report(joined_node="foxtrot", rounds=3),
        "hop_benchmark": ring.benchmark_lookups(sample_keys, start_nodes=["alpha", "charlie"]),
    }


def load_ring(path: Path) -> ChordRing:
    payload = json.loads(path.read_text(encoding="utf-8"))
    m_bits = payload["m_bits"]
    nodes = payload["nodes"]
    if not isinstance(nodes, list) or not all(isinstance(item, str) for item in nodes):
        raise ValueError("nodes must be a list of node names")
    return ChordRing(m_bits, nodes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chord DHT lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="print a demo Chord ring payload")
    demo_parser.add_argument("--pretty", action="store_true")

    route_parser = subparsers.add_parser("route", help="route a key lookup through a ring")
    route_parser.add_argument("ring_file", type=Path)
    route_parser.add_argument("start_node")
    route_parser.add_argument("key")
    route_parser.add_argument("--pretty", action="store_true")

    join_parser = subparsers.add_parser("join", help="preview which keys move when a node joins")
    join_parser.add_argument("ring_file", type=Path)
    join_parser.add_argument("new_node")
    join_parser.add_argument("keys", nargs="+")
    join_parser.add_argument("--pretty", action="store_true")

    benchmark_parser = subparsers.add_parser(
        "benchmark", help="compare Chord finger-table routing against linear successor forwarding"
    )
    benchmark_parser.add_argument("ring_file", type=Path)
    benchmark_parser.add_argument("keys", nargs="+")
    benchmark_parser.add_argument(
        "--start-node",
        dest="start_nodes",
        action="append",
        default=None,
        help="optional start node to benchmark; may be provided multiple times",
    )
    benchmark_parser.add_argument("--pretty", action="store_true")

    resilience_parser = subparsers.add_parser(
        "resilience",
        help="simulate successor-list replicas and key availability during node failures",
    )
    resilience_parser.add_argument("ring_file", type=Path)
    resilience_parser.add_argument("keys", nargs="+")
    resilience_parser.add_argument(
        "--failed-node",
        dest="failed_nodes",
        action="append",
        default=[],
        help="node to treat as failed; may be provided multiple times",
    )
    resilience_parser.add_argument(
        "--replica-count",
        type=int,
        default=3,
        help="number of consecutive successors to treat as replicas including the primary owner",
    )
    resilience_parser.add_argument("--pretty", action="store_true")

    stabilize_parser = subparsers.add_parser(
        "stabilize",
        help="simulate explicit stabilization rounds after a join or failure event",
    )
    stabilize_parser.add_argument("ring_file", type=Path)
    stabilize_parser.add_argument(
        "--joined-node",
        help="optional node that just joined and starts with stale self-pointing metadata",
    )
    stabilize_parser.add_argument(
        "--failed-node",
        dest="failed_nodes",
        action="append",
        default=[],
        help="node to remove from the live ring before stabilization; may be provided multiple times",
    )
    stabilize_parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="number of stabilization rounds to simulate",
    )
    stabilize_parser.add_argument("--pretty", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "demo":
        payload = {"command": "demo", **build_demo_payload()}
    elif args.command == "route":
        ring = load_ring(args.ring_file)
        payload = {"command": "route", **asdict(ring.lookup(args.start_node, args.key))}
    elif args.command == "join":
        ring = load_ring(args.ring_file)
        payload = {"command": "join", **ring.join_report(args.new_node, args.keys)}
    elif args.command == "benchmark":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "benchmark",
            **ring.benchmark_lookups(args.keys, start_nodes=args.start_nodes),
        }
    elif args.command == "resilience":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "resilience",
            **ring.resilience_report(
                args.keys,
                failed_nodes=args.failed_nodes,
                replica_count=args.replica_count,
            ),
        }
    elif args.command == "stabilize":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "stabilize",
            **ring.stabilization_report(
                joined_node=args.joined_node,
                failed_nodes=args.failed_nodes,
                rounds=args.rounds,
            ),
        }
    else:
        raise ValueError(f"unsupported command {args.command!r}")

    print(json.dumps(payload, indent=2 if getattr(args, "pretty", False) else None))


if __name__ == "__main__":
    main()
