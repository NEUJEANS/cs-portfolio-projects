from __future__ import annotations

import argparse
import hashlib
import json
import random
from bisect import bisect_left
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Literal


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


FingerRepairMode = Literal["single", "all", "random"]
SUPPORTED_FINGER_REPAIR_MODES: tuple[FingerRepairMode, ...] = ("single", "all", "random")


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
        finger_repair_mode: FingerRepairMode = "single",
        finger_repair_seed: int | None = None,
    ) -> dict[str, object]:
        if rounds <= 0:
            raise ValueError("rounds must be positive")
        if finger_repair_mode not in SUPPORTED_FINGER_REPAIR_MODES:
            raise ValueError(f"unsupported finger_repair_mode {finger_repair_mode!r}")
        if finger_repair_mode == "random" and finger_repair_seed is None:
            raise ValueError("random finger repair mode requires a seed")

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
            self._stabilization_round_summary(
                target_ring,
                initial_state,
                round_index=0,
                changed=[],
                repaired_finger_slots=[],
            )
        ]
        current_state = initial_state
        random_finger_order = list(range(self.m_bits))
        if finger_repair_mode == "random":
            random.Random(finger_repair_seed).shuffle(random_finger_order)

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
            repaired_finger_slots = self._finger_slots_for_round(
                round_index,
                finger_repair_mode=finger_repair_mode,
                random_finger_order=random_finger_order,
            )

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
                for finger_slot in repaired_finger_slots:
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
                    repaired_finger_slots=repaired_finger_slots,
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
            "finger_repair_mode": finger_repair_mode,
            "finger_repair_seed": finger_repair_seed,
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

    def _finger_slots_for_round(
        self,
        round_index: int,
        *,
        finger_repair_mode: FingerRepairMode,
        random_finger_order: list[int],
    ) -> list[int]:
        if finger_repair_mode == "all":
            return list(range(self.m_bits))
        if finger_repair_mode == "random":
            return [random_finger_order[(round_index - 1) % self.m_bits]]
        return [(round_index - 1) % self.m_bits]

    def _stabilization_round_summary(
        self,
        target_ring: "ChordRing",
        state: dict[str, dict[str, object]],
        round_index: int,
        changed: list[str],
        repaired_finger_slots: list[int],
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
            "repaired_finger_slots": repaired_finger_slots,
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

    def churn_report(
        self,
        events: Iterable[dict[str, object]],
        *,
        rounds: int = 3,
        finger_repair_mode: FingerRepairMode = "single",
        finger_repair_seed: int | None = None,
    ) -> dict[str, object]:
        event_list = list(events)
        if not event_list:
            raise ValueError("churn report requires at least one event")

        current_ring = self
        steps: list[dict[str, object]] = []
        fully_stabilized_steps = 0
        stabilized_rounds: list[int] = []

        for index, raw_event in enumerate(event_list, start=1):
            action = raw_event.get("action")
            if action not in {"join", "fail", "recover"}:
                raise ValueError(f"unsupported churn action {action!r}")
            node_name = raw_event.get("node")
            if not isinstance(node_name, str) or not node_name:
                raise ValueError("each churn event requires a non-empty string node")
            event_rounds = int(raw_event.get("rounds", rounds))
            if event_rounds <= 0:
                raise ValueError("event rounds must be positive")

            before_nodes = current_ring.list_nodes()
            if action == "join":
                report = current_ring.stabilization_report(
                    joined_node=node_name,
                    rounds=event_rounds,
                    finger_repair_mode=finger_repair_mode,
                    finger_repair_seed=finger_repair_seed,
                )
                current_ring = current_ring.add_node(node_name)
            elif action == "fail":
                report = current_ring.stabilization_report(
                    failed_nodes=[node_name],
                    rounds=event_rounds,
                    finger_repair_mode=finger_repair_mode,
                    finger_repair_seed=finger_repair_seed,
                )
                current_ring = current_ring.without_nodes([node_name])
            else:
                if any(node.name == node_name for node in current_ring.nodes):
                    raise ValueError(f"recover event requires node {node_name!r} to be absent from the current ring")
                if not any(node.name == node_name for node in self.nodes):
                    raise ValueError(
                        f"recover event requires node {node_name!r} to exist in the original ring"
                    )
                report = current_ring.stabilization_report(
                    joined_node=node_name,
                    rounds=event_rounds,
                    finger_repair_mode=finger_repair_mode,
                    finger_repair_seed=finger_repair_seed,
                )
                current_ring = current_ring.add_node(node_name)

            stabilized_round = next(
                (
                    round_data["round"]
                    for round_data in report["rounds"]
                    if round_data["summary"]["successor_matches"] == report["target_node_count"]
                    and round_data["summary"]["predecessor_matches"] == report["target_node_count"]
                    and round_data["summary"]["finger_matches"] == report["summary"]["total_fingers"]
                ),
                None,
            )
            if report["summary"]["fully_stabilized"]:
                fully_stabilized_steps += 1
            if stabilized_round is not None:
                stabilized_rounds.append(int(stabilized_round))

            steps.append(
                {
                    "step": index,
                    "action": action,
                    "node": node_name,
                    "rounds_requested": event_rounds,
                    "before_nodes": before_nodes,
                    "after_nodes": current_ring.list_nodes(),
                    "target_node_count": report["target_node_count"],
                    "fully_stabilized": report["summary"]["fully_stabilized"],
                    "stabilized_round": stabilized_round,
                    "final_successor_matches": report["summary"]["final_successor_matches"],
                    "final_predecessor_matches": report["summary"]["final_predecessor_matches"],
                    "final_finger_matches": report["summary"]["final_finger_matches"],
                    "total_fingers": report["summary"]["total_fingers"],
                    "report": report,
                }
            )

        return {
            "m_bits": self.m_bits,
            "starting_nodes": self.list_nodes(),
            "ending_nodes": current_ring.list_nodes(),
            "event_count": len(steps),
            "rounds_default": rounds,
            "finger_repair_mode": finger_repair_mode,
            "finger_repair_seed": finger_repair_seed,
            "steps": steps,
            "summary": {
                "fully_stabilized_steps": fully_stabilized_steps,
                "partially_stabilized_steps": len(steps) - fully_stabilized_steps,
                "max_stabilized_round": max(stabilized_rounds) if stabilized_rounds else None,
                "average_stabilized_round": round(mean(stabilized_rounds), 3) if stabilized_rounds else None,
                "final_node_count": len(current_ring.nodes),
            },
        }

    def compare_stabilization_modes(
        self,
        *,
        joined_node: str | None = None,
        failed_nodes: Iterable[str] | None = None,
        rounds: int = 3,
        modes: Iterable[FingerRepairMode] | None = None,
        random_seed: int = 17,
    ) -> dict[str, object]:
        selected_modes = list(dict.fromkeys(modes or SUPPORTED_FINGER_REPAIR_MODES))
        if not selected_modes:
            raise ValueError("at least one stabilization mode is required")
        for mode in selected_modes:
            if mode not in SUPPORTED_FINGER_REPAIR_MODES:
                raise ValueError(f"unsupported finger_repair_mode {mode!r}")

        reports: dict[str, dict[str, object]] = {}
        score_rows: list[dict[str, object]] = []
        fastest_modes: list[str] = []
        fastest_rounds: int | None = None
        highest_progress_mode = selected_modes[0]
        highest_progress_ratio = -1.0

        for mode in selected_modes:
            report = self.stabilization_report(
                joined_node=joined_node,
                failed_nodes=failed_nodes,
                rounds=rounds,
                finger_repair_mode=mode,
                finger_repair_seed=random_seed if mode == "random" else None,
            )
            reports[mode] = report
            stabilized_round = next(
                (
                    round_data["round"]
                    for round_data in report["rounds"]
                    if round_data["summary"]["successor_matches"] == report["target_node_count"]
                    and round_data["summary"]["predecessor_matches"] == report["target_node_count"]
                    and round_data["summary"]["finger_matches"] == report["summary"]["total_fingers"]
                ),
                None,
            )
            progress_ratio = report["summary"]["final_finger_matches"] / max(report["summary"]["total_fingers"], 1)
            if progress_ratio > highest_progress_ratio:
                highest_progress_ratio = progress_ratio
                highest_progress_mode = mode
            if stabilized_round is not None and (fastest_rounds is None or stabilized_round < fastest_rounds):
                fastest_rounds = stabilized_round
                fastest_modes = [mode]
            elif stabilized_round is not None and stabilized_round == fastest_rounds:
                fastest_modes.append(mode)

            score_rows.append(
                {
                    "mode": mode,
                    "random_seed": random_seed if mode == "random" else None,
                    "fully_stabilized": report["summary"]["fully_stabilized"],
                    "stabilized_round": stabilized_round,
                    "final_successor_matches": report["summary"]["final_successor_matches"],
                    "final_predecessor_matches": report["summary"]["final_predecessor_matches"],
                    "final_finger_matches": report["summary"]["final_finger_matches"],
                    "total_fingers": report["summary"]["total_fingers"],
                    "final_finger_progress_ratio": round(progress_ratio, 3),
                }
            )

        score_rows.sort(
            key=lambda row: (
                row["stabilized_round"] is None,
                row["stabilized_round"] if row["stabilized_round"] is not None else rounds + 1,
                -float(row["final_finger_progress_ratio"]),
                str(row["mode"]),
            )
        )
        return {
            "m_bits": self.m_bits,
            "joined_node": joined_node,
            "failed_nodes": list(dict.fromkeys(failed_nodes or [])),
            "rounds_requested": rounds,
            "modes": selected_modes,
            "random_seed": random_seed,
            "comparison": score_rows,
            "reports": reports,
            "summary": {
                "fastest_modes": fastest_modes,
                "fastest_stabilized_round": fastest_rounds,
                "highest_progress_mode": highest_progress_mode,
                "highest_progress_ratio": round(highest_progress_ratio, 3),
            },
        }

    def export_graphviz(
        self,
        mode: str,
        start_node: str | None = None,
        key: str | None = None,
        joined_node: str | None = None,
        failed_nodes: Iterable[str] | None = None,
        rounds: int = 3,
        finger_repair_mode: FingerRepairMode = "single",
        finger_repair_seed: int | None = None,
    ) -> str:
        if mode == "ring":
            return self._ring_graphviz()
        if mode == "route":
            if start_node is None or key is None:
                raise ValueError("route graph export requires start_node and key")
            return self._route_graphviz(start_node, key)
        if mode == "stabilize":
            return self._stabilization_graphviz(
                joined_node=joined_node,
                failed_nodes=failed_nodes,
                rounds=rounds,
                finger_repair_mode=finger_repair_mode,
                finger_repair_seed=finger_repair_seed,
            )
        raise ValueError(f"unsupported graph export mode {mode!r}")

    def _ring_graphviz(self) -> str:
        lines = [
            "digraph chord_ring {",
            "  rankdir=LR;",
            '  graph [label="Chord ring topology", labelloc=t, fontsize=20];',
            '  node [shape=record, style="rounded,filled", fillcolor="#eef6ff", color="#3b82f6"];',
            '  edge [color="#475569", penwidth=1.4];',
        ]
        for node in self.nodes:
            lines.append(
                f'  "{node.name}" [label="{{{node.name}|id={node.node_id}}}"];'
            )
        for node in self.nodes:
            successor = self.successor_of_node(node)
            lines.append(f'  "{node.name}" -> "{successor.name}" [label="successor"];')
        lines.append("}")
        return "\\n".join(lines)

    def _route_graphviz(self, start_node: str, key: str) -> str:
        result = self.lookup(start_node, key)
        owner = self.get_node(result.responsible_node)
        key_id = result.key_id
        lines = [
            "digraph chord_route {",
            "  rankdir=LR;",
            f'  graph [label="Chord lookup route for {self._dot_label(key)} (id={key_id})", labelloc=t, fontsize=20];',
            '  node [shape=record, style="rounded,filled", fillcolor="#eef6ff", color="#3b82f6"];',
            '  edge [color="#94a3b8", penwidth=1.2];',
        ]
        route_pairs = {(result.route[index], result.route[index + 1]) for index in range(len(result.route) - 1)}
        route_nodes = set(result.route)
        for node in self.nodes:
            extras = []
            if node.name == result.start_node:
                extras.append("start")
            if node.name == owner.name:
                extras.append("owner")
            if node.name in route_nodes:
                extras.append("route")
            suffix = f'\\n({", ".join(extras)})' if extras else ""
            fill = '#dbeafe' if node.name in route_nodes else '#eef6ff'
            if node.name == owner.name:
                fill = '#dcfce7'
            lines.append(
                f'  "{node.name}" [label="{{{node.name}|id={node.node_id}{suffix}}}", fillcolor="{fill}"];'
            )
        lines.append(f'  "key:{key}" [shape=note, fillcolor="#fff7ed", color="#f97316", label="{self._dot_label(key)}\\nid={key_id}"];')
        lines.append(f'  "key:{key}" -> "{owner.name}" [color="#f97316", penwidth=2.2, label="maps to"];')
        for node in self.nodes:
            successor = self.successor_of_node(node)
            if (node.name, successor.name) in route_pairs:
                lines.append(
                    f'  "{node.name}" -> "{successor.name}" [color="#94a3b8", style=dashed, label="ring"];'
                )
            else:
                lines.append(f'  "{node.name}" -> "{successor.name}" [color="#cbd5e1", style=dashed];')
        for index in range(len(result.route) - 1):
            source = result.route[index]
            target = result.route[index + 1]
            lines.append(
                f'  "{source}" -> "{target}" [color="#dc2626", penwidth=2.6, label="hop {index + 1}"];'
            )
        lines.append("}")
        return "\\n".join(lines)

    def _stabilization_graphviz(
        self,
        joined_node: str | None = None,
        failed_nodes: Iterable[str] | None = None,
        rounds: int = 3,
        finger_repair_mode: FingerRepairMode = "single",
        finger_repair_seed: int | None = None,
    ) -> str:
        report = self.stabilization_report(
            joined_node=joined_node,
            failed_nodes=failed_nodes,
            rounds=rounds,
            finger_repair_mode=finger_repair_mode,
            finger_repair_seed=finger_repair_seed,
        )
        failed = set(report["failed_nodes"])
        mode_suffix = finger_repair_mode
        if finger_repair_mode == "random":
            mode_suffix = f"{finger_repair_mode} (seed={finger_repair_seed})"
        lines = [
            "digraph chord_stabilization {",
            "  rankdir=LR;",
            f'  graph [label="Chord stabilization progression | finger repair: {self._dot_label(mode_suffix)}", labelloc=t, fontsize=20];',
            '  node [shape=record, style="rounded,filled", fillcolor="#f8fafc", color="#334155"];',
            '  edge [color="#64748b", penwidth=1.1];',
        ]
        for round_data in report["rounds"]:
            round_index = round_data["round"]
            summary = round_data["summary"]
            repaired = round_data["repaired_finger_slots"]
            repaired_label = "all" if len(repaired) == self.m_bits else ", ".join(str(slot) for slot in repaired) or "none"
            lines.append(f'  subgraph cluster_round_{round_index} {{')
            lines.append(f'    label="round {round_index} | repair={self._dot_label(repaired_label)}";')
            lines.append('    color="#cbd5e1";')
            for node_state in round_data["nodes"]:
                name = node_state["name"]
                fill = '#fef3c7' if name == joined_node else '#f8fafc'
                if name in failed:
                    fill = '#fee2e2'
                if node_state["successor_ok"] and node_state["predecessor_ok"] and node_state["matching_fingers"] == node_state["total_fingers"]:
                    fill = '#dcfce7'
                label = (
                    f"{{{name}|succ={node_state['observed_successor']}|pred={node_state['observed_predecessor']}|"
                    f"fingers={node_state['matching_fingers']}/{node_state['total_fingers']}}}"
                )
                lines.append(
                    f'    "r{round_index}:{name}" [label="{label}", fillcolor="{fill}"];'
                )
            lines.append(
                f'    "r{round_index}:summary" [shape=note, fillcolor="#e0f2fe", color="#0284c7", '
                f'label="matched succ/pred: {summary["successor_matches"]}/{summary["node_count"]} / {summary["predecessor_matches"]}/{summary["node_count"]}\\nfingers: {summary["finger_matches"]}/{summary["node_count"] * self.m_bits}"];'
            )
            lines.append("  }")
        for round_data in report["rounds"][:-1]:
            next_round = round_data["round"] + 1
            for node_state in round_data["nodes"]:
                name = node_state["name"]
                lines.append(f'  "r{round_data["round"]}:{name}" -> "r{next_round}:{name}";')
            changed = report["rounds"][next_round]["changed_nodes"]
            label = ", ".join(changed) if changed else "no metadata changes"
            lines.append(
                f'  "r{round_data["round"]}:summary" -> "r{next_round}:summary" [label="changed: {self._dot_label(label)}"];'
            )
        lines.append("}")
        return "\n".join(lines)

    def _dot_label(self, value: str) -> str:
        return value.replace("\\", r"\\").replace('"', r'\"').replace("\n", r"\n")


def select_benchmark_start_nodes(
    ring: ChordRing,
    requested_count: int | None,
    *,
    sample_mode: str = "first",
    seed: int | None = None,
) -> list[str]:
    if requested_count is None:
        return [node.name for node in ring.nodes]
    if requested_count <= 0:
        raise ValueError("start_nodes must be positive when provided")

    count = min(requested_count, len(ring.nodes))
    node_names = [node.name for node in ring.nodes]
    if sample_mode == "first":
        return node_names[:count]
    if sample_mode == "random":
        if seed is None:
            raise ValueError("random start-node sampling requires a seed")
        return random.Random(seed).sample(node_names, count)
    raise ValueError(f"unsupported sample_mode {sample_mode!r}")


def render_benchmark_report_markdown(benchmark: dict[str, object]) -> str:
    summary = benchmark["summary"]
    lines = [
        "# Chord lookup benchmark",
        "",
        f"- Identifier bits: `{benchmark['m_bits']}`",
        f"- Node count: `{benchmark['node_count']}`",
        f"- Start nodes benchmarked: {', '.join(f'`{name}`' for name in benchmark['start_nodes'])}",
        f"- Key count: `{len(benchmark['keys'])}`",
        f"- Case count: `{summary['case_count']}`",
        f"- Average Chord hops: `{summary['average_chord_hops']}`",
        f"- Average linear hops: `{summary['average_linear_hops']}`",
        f"- Total hop savings: `{summary['total_hop_savings']}`",
        f"- Improved cases: `{summary['improved_cases']}`",
        f"- Tied cases: `{summary['tied_cases']}`",
        f"- Slower cases: `{summary['slower_cases']}`",
        "",
        "| Start node | Key | Responsible node | Chord hops | Linear hops | Hop savings | Chord route | Linear route |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for case in benchmark["cases"]:
        lines.append(
            f"| `{case['start_node']}` | `{case['key']}` | `{case['responsible_node']}` | {case['chord_hops']} | {case['linear_hops']} | {case['hop_savings']} | {' → '.join(case['chord_route'])} | {' → '.join(case['linear_route'])} |"
        )
    return "\n".join(lines)


def render_benchmark_report_csv(benchmark: dict[str, object]) -> str:
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "start_node",
        "key",
        "key_id",
        "responsible_node",
        "chord_hops",
        "linear_hops",
        "hop_savings",
        "chord_route",
        "linear_route",
    ])
    for case in benchmark["cases"]:
        writer.writerow([
            case["start_node"],
            case["key"],
            case["key_id"],
            case["responsible_node"],
            case["chord_hops"],
            case["linear_hops"],
            case["hop_savings"],
            "->".join(case["chord_route"]),
            "->".join(case["linear_route"]),
        ])
    return output.getvalue().strip()


def render_stabilization_comparison_markdown(comparison: dict[str, object]) -> str:
    rows = comparison["comparison"]
    summary = comparison["summary"]
    reports = comparison["reports"]
    lines = [
        "# Chord stabilization comparison",
        "",
        f"- Scenario joined node: `{comparison['joined_node']}`" if comparison.get('joined_node') else f"- Scenario failed nodes: {', '.join(f'`{name}`' for name in comparison['failed_nodes']) or 'none'}",
        f"- Rounds simulated: `{comparison['rounds_requested']}`",
        f"- Random seed: `{comparison['random_seed']}`",
        f"- Fastest mode(s): {', '.join(f'`{mode}`' for mode in summary['fastest_modes'])}",
        f"- Fastest stabilized round: `{summary['fastest_stabilized_round']}`",
        f"- Highest final finger progress mode: `{summary['highest_progress_mode']}` ({summary['highest_progress_ratio']:.2%})",
        "",
        "| Mode | Stabilized round | Final finger progress | Successor matches | Predecessor matches | Final finger matches |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        report = reports[row['mode']]
        final = report['summary']
        stabilized_round = row['stabilized_round'] if row['stabilized_round'] is not None else "not within budget"
        lines.append(
            f"| `{row['mode']}` | {stabilized_round} | {row['final_finger_progress_ratio']:.2%} | "
            f"{final['final_successor_matches']}/{report['target_node_count']} | "
            f"{final['final_predecessor_matches']}/{report['target_node_count']} | "
            f"{final['final_finger_matches']}/{final['total_fingers']} |"
        )
    return "\n".join(lines)


def render_stabilization_comparison_csv(comparison: dict[str, object]) -> str:
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "mode",
        "stabilized_round",
        "final_finger_progress_ratio",
        "final_successor_matches",
        "node_count",
        "final_predecessor_matches",
        "final_finger_matches",
        "total_fingers",
    ])
    reports = comparison['reports']
    for row in comparison['comparison']:
        final = reports[row['mode']]['summary']
        writer.writerow([
            row['mode'],
            row['stabilized_round'],
            f"{row['final_finger_progress_ratio']:.6f}",
            final['final_successor_matches'],
            reports[row['mode']]['target_node_count'],
            final['final_predecessor_matches'],
            final['final_finger_matches'],
            final['total_fingers'],
        ])
    return output.getvalue().strip()


def render_churn_report_markdown(report: dict[str, object]) -> str:
    summary = report['summary']
    starting_nodes = ', '.join(f"`{node['name']}`" for node in report['starting_nodes'])
    ending_nodes = ', '.join(f"`{node['name']}`" for node in report['ending_nodes'])
    lines = [
        "# Chord churn summary",
        "",
        f"- Events processed: `{report['event_count']}`",
        f"- Default rounds per event: `{report['rounds_default']}`",
        f"- Finger repair mode: `{report['finger_repair_mode']}`",
        f"- Finger repair seed: `{report['finger_repair_seed']}`" if report.get('finger_repair_seed') is not None else "- Finger repair seed: `none`",
        f"- Starting nodes: {starting_nodes}",
        f"- Ending nodes: {ending_nodes}",
        f"- Fully stabilized steps: `{summary['fully_stabilized_steps']}`",
        f"- Partially stabilized steps: `{summary['partially_stabilized_steps']}`",
        f"- Max stabilized round: `{summary['max_stabilized_round']}`",
        f"- Average stabilized round: `{summary['average_stabilized_round']}`",
        f"- Final node count: `{summary['final_node_count']}`",
        "",
        "| Step | Action | Node | Rounds | Stabilized round | Final finger progress | Final successor matches | Final predecessor matches |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for step in report['steps']:
        stabilized_round = step['stabilized_round'] if step['stabilized_round'] is not None else "not within budget"
        progress_ratio = step['final_finger_matches'] / max(step['total_fingers'], 1)
        lines.append(
            f"| {step['step']} | `{step['action']}` | `{step['node']}` | {step['rounds_requested']} | {stabilized_round} | {progress_ratio:.2%} | {step['final_successor_matches']}/{step['target_node_count']} | {step['final_predecessor_matches']}/{step['target_node_count']} |"
        )
    return "\n".join(lines)


def render_churn_report_csv(report: dict[str, object]) -> str:
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "step",
        "action",
        "node",
        "rounds_requested",
        "finger_repair_mode",
        "stabilized_round",
        "fully_stabilized",
        "final_finger_progress_ratio",
        "final_successor_matches",
        "target_node_count",
        "final_predecessor_matches",
        "final_finger_matches",
        "total_fingers",
        "ending_node_count",
    ])
    for step in report['steps']:
        writer.writerow([
            step['step'],
            step['action'],
            step['node'],
            step['rounds_requested'],
            report['finger_repair_mode'],
            step['stabilized_round'],
            str(step['fully_stabilized']).lower(),
            f"{step['final_finger_matches'] / max(step['total_fingers'], 1):.6f}",
            step['final_successor_matches'],
            step['target_node_count'],
            step['final_predecessor_matches'],
            step['final_finger_matches'],
            step['total_fingers'],
            len(step['after_nodes']),
        ])
    return output.getvalue().strip()


def build_demo_payload() -> dict[str, object]:
    ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])
    sample_keys = ["report.pdf", "slides", "internship-notes", "compiler", "final-project"]
    route = ring.lookup("alpha", "compiler")
    stabilization_comparison = ring.compare_stabilization_modes(
        joined_node="foxtrot",
        rounds=3,
        random_seed=17,
    )
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
        "stabilization_comparison_preview": {
            "modes": stabilization_comparison["modes"],
            "random_seed": stabilization_comparison["random_seed"],
            "comparison": stabilization_comparison["comparison"],
            "summary": stabilization_comparison["summary"],
        },
        "graphviz_preview": {
            "ring_dot": ring.export_graphviz("ring"),
            "route_dot": ring.export_graphviz("route", start_node="alpha", key="compiler"),
        },
        "hop_benchmark": ring.benchmark_lookups(sample_keys, start_nodes=["alpha", "charlie"]),
    }


def build_synthetic_benchmark_payload(
    m_bits: int,
    node_count: int,
    key_count: int,
    seed: int,
    start_nodes: int | None = None,
    start_node_sample_mode: str = "first",
    start_node_seed: int | None = None,
) -> dict[str, object]:
    if m_bits <= 0:
        raise ValueError("m_bits must be positive")
    if node_count <= 0:
        raise ValueError("node_count must be positive")
    if key_count <= 0:
        raise ValueError("key_count must be positive")
    ring_size = 2**m_bits
    if node_count > ring_size:
        raise ValueError("node_count cannot exceed the identifier ring size")

    rng = random.Random(seed)
    node_names: list[str] = []
    used_ids: set[int] = set()
    attempt = 0
    while len(node_names) < node_count:
        candidate = f"node-{attempt:03d}-{rng.randrange(1_000_000):06d}"
        candidate_id = int(hashlib.sha1(candidate.encode("utf-8")).hexdigest(), 16) % ring_size
        if candidate_id not in used_ids:
            node_names.append(candidate)
            used_ids.add(candidate_id)
        attempt += 1
        if attempt > node_count * 20 and len(node_names) < node_count:
            raise ValueError("unable to generate enough unique node identifiers for the ring")

    ring = ChordRing(m_bits, node_names)
    keys = [f"key-{index:03d}-{rng.randrange(1_000_000):06d}" for index in range(key_count)]
    benchmark_starts = select_benchmark_start_nodes(
        ring,
        start_nodes,
        sample_mode=start_node_sample_mode,
        seed=start_node_seed if start_node_seed is not None else seed,
    )

    benchmark = ring.benchmark_lookups(keys, start_nodes=benchmark_starts)
    return {
        "generator": {
            "seed": seed,
            "m_bits": m_bits,
            "node_count": node_count,
            "key_count": key_count,
            "benchmark_start_node_count": len(benchmark_starts),
            "start_node_sample_mode": start_node_sample_mode,
            "start_node_seed": (start_node_seed if start_node_seed is not None else seed),
        },
        "ring": {
            "m_bits": ring.m_bits,
            "ring_size": ring.ring_size,
            "nodes": ring.list_nodes(),
        },
        "keys": keys,
        "benchmark": benchmark,
    }


def load_churn_events(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("churn events file must contain a JSON list")
    normalized: list[dict[str, object]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"churn event #{index} must be a JSON object")
        normalized.append(dict(item))
    return normalized


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

    benchmark_export_parser = subparsers.add_parser(
        "benchmark-export",
        help="render a lookup benchmark as Markdown or CSV for portfolio notes",
    )
    benchmark_export_parser.add_argument("ring_file", type=Path)
    benchmark_export_parser.add_argument("keys", nargs="+", help="keys to benchmark")
    benchmark_export_parser.add_argument(
        "--start-node",
        dest="start_nodes",
        action="append",
        default=None,
        help="optional start node; may be provided multiple times",
    )
    benchmark_export_parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="report format for the rendered lookup benchmark",
    )

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
    stabilize_parser.add_argument(
        "--finger-repair-mode",
        choices=["single", "all", "random"],
        default="single",
        help="how each stabilization round repairs finger entries: one slot in order, all slots, or one seeded-random slot",
    )
    stabilize_parser.add_argument(
        "--finger-repair-seed",
        type=int,
        default=None,
        help="seed for --finger-repair-mode random; required when random mode is used",
    )
    stabilize_parser.add_argument("--pretty", action="store_true")

    compare_stabilize_parser = subparsers.add_parser(
        "compare-stabilize",
        help="compare stabilization outcomes across multiple finger repair modes on the same scenario",
    )
    compare_stabilize_parser.add_argument("ring_file", type=Path)
    compare_stabilize_parser.add_argument(
        "--joined-node",
        help="optional node that just joined and starts with stale self-pointing metadata",
    )
    compare_stabilize_parser.add_argument(
        "--failed-node",
        dest="failed_nodes",
        action="append",
        default=[],
        help="node to remove from the live ring before stabilization; may be provided multiple times",
    )
    compare_stabilize_parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="number of stabilization rounds to simulate for each mode",
    )
    compare_stabilize_parser.add_argument(
        "--mode",
        dest="modes",
        action="append",
        default=None,
        choices=list(SUPPORTED_FINGER_REPAIR_MODES),
        help="stabilization mode to include; may be provided multiple times and defaults to all modes",
    )
    compare_stabilize_parser.add_argument(
        "--random-seed",
        type=int,
        default=17,
        help="seed to use for the random finger repair mode during comparison",
    )
    compare_stabilize_parser.add_argument("--pretty", action="store_true")

    compare_export_parser = subparsers.add_parser(
        "compare-stabilize-export",
        help="render stabilization comparison summaries as Markdown or CSV for portfolio write-ups",
    )
    compare_export_parser.add_argument("ring_file", type=Path)
    compare_export_parser.add_argument(
        "--joined-node",
        help="optional node that just joined and starts with stale self-pointing metadata",
    )
    compare_export_parser.add_argument(
        "--failed-node",
        dest="failed_nodes",
        action="append",
        default=[],
        help="node to remove from the live ring before stabilization; may be provided multiple times",
    )
    compare_export_parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="number of stabilization rounds to simulate for each mode",
    )
    compare_export_parser.add_argument(
        "--mode",
        dest="modes",
        action="append",
        default=None,
        choices=list(SUPPORTED_FINGER_REPAIR_MODES),
        help="stabilization mode to include; may be provided multiple times and defaults to all modes",
    )
    compare_export_parser.add_argument(
        "--random-seed",
        type=int,
        default=17,
        help="seed to use for the random finger repair mode during comparison",
    )
    compare_export_parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="report format for the rendered comparison summary",
    )

    churn_parser = subparsers.add_parser(
        "churn",
        help="simulate a sequence of join, fail, or recover events and summarize stabilization after each step",
    )
    churn_parser.add_argument("ring_file", type=Path)
    churn_parser.add_argument(
        "events_file",
        type=Path,
        help="JSON file containing churn events (join, fail, or recover)",
    )
    churn_parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="default number of stabilization rounds to simulate after each event",
    )
    churn_parser.add_argument(
        "--finger-repair-mode",
        choices=["single", "all", "random"],
        default="single",
        help="finger repair policy to use for each churn step",
    )
    churn_parser.add_argument(
        "--finger-repair-seed",
        type=int,
        default=None,
        help="seed for random finger repair mode; required when random mode is used",
    )
    churn_parser.add_argument("--pretty", action="store_true")

    churn_export_parser = subparsers.add_parser(
        "churn-export",
        help="render a churn summary as Markdown or CSV for portfolio notes",
    )
    churn_export_parser.add_argument("ring_file", type=Path)
    churn_export_parser.add_argument("events_file", type=Path)
    churn_export_parser.add_argument("--rounds", type=int, default=3)
    churn_export_parser.add_argument(
        "--finger-repair-mode",
        choices=["single", "all", "random"],
        default="single",
        help="finger repair policy to use for each churn step",
    )
    churn_export_parser.add_argument(
        "--finger-repair-seed",
        type=int,
        default=None,
        help="seed for random finger repair mode; required when random mode is used",
    )
    churn_export_parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="report format for the rendered churn summary",
    )

    synth_parser = subparsers.add_parser(
        "synth-benchmark",
        help="generate a deterministic synthetic ring/workload and benchmark lookup hops",
    )
    synth_parser.add_argument("--m-bits", type=int, default=10, help="identifier width for the generated ring")
    synth_parser.add_argument("--nodes", type=int, default=16, help="number of synthetic nodes to generate")
    synth_parser.add_argument("--keys", type=int, default=32, help="number of synthetic keys to benchmark")
    synth_parser.add_argument("--seed", type=int, default=7, help="random seed for reproducible generation")
    synth_parser.add_argument(
        "--start-nodes",
        type=int,
        default=None,
        help="optional number of generated nodes to benchmark from; defaults to all nodes",
    )
    synth_parser.add_argument(
        "--start-node-sample-mode",
        choices=["first", "random"],
        default="first",
        help="how to choose a subset of benchmark start nodes when --start-nodes is provided",
    )
    synth_parser.add_argument(
        "--start-node-seed",
        type=int,
        default=None,
        help="seed for random start-node sampling; defaults to --seed",
    )
    synth_parser.add_argument("--pretty", action="store_true")

    graphviz_parser = subparsers.add_parser(
        "graphviz",
        help="export Graphviz DOT for the ring, a lookup route, or stabilization rounds",
    )
    graphviz_parser.add_argument("ring_file", type=Path)
    graphviz_parser.add_argument(
        "--mode",
        choices=["ring", "route", "stabilize"],
        default="ring",
        help="what to export as DOT",
    )
    graphviz_parser.add_argument("--start-node", help="start node for route mode")
    graphviz_parser.add_argument("--key", help="lookup key for route mode")
    graphviz_parser.add_argument("--joined-node", help="joined node for stabilization mode")
    graphviz_parser.add_argument(
        "--failed-node",
        dest="failed_nodes",
        action="append",
        default=[],
        help="failed node for stabilization mode; may be provided multiple times",
    )
    graphviz_parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="number of stabilization rounds to export when mode=stabilize",
    )
    graphviz_parser.add_argument(
        "--finger-repair-mode",
        choices=["single", "all", "random"],
        default="single",
        help="finger repair policy for stabilization graph exports when mode=stabilize",
    )
    graphviz_parser.add_argument(
        "--finger-repair-seed",
        type=int,
        default=None,
        help="seed for random finger repair mode when mode=stabilize",
    )

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
    elif args.command == "benchmark-export":
        ring = load_ring(args.ring_file)
        benchmark = ring.benchmark_lookups(args.keys, start_nodes=args.start_nodes)
        if args.format == "markdown":
            print(render_benchmark_report_markdown(benchmark))
            return
        if args.format == "csv":
            print(render_benchmark_report_csv(benchmark))
            return
        raise ValueError(f"unsupported export format {args.format!r}")
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
                finger_repair_mode=args.finger_repair_mode,
                finger_repair_seed=args.finger_repair_seed,
            ),
        }
    elif args.command == "compare-stabilize":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "compare-stabilize",
            **ring.compare_stabilization_modes(
                joined_node=args.joined_node,
                failed_nodes=args.failed_nodes,
                rounds=args.rounds,
                modes=args.modes,
                random_seed=args.random_seed,
            ),
        }
    elif args.command == "synth-benchmark":
        payload = {
            "command": "synth-benchmark",
            **build_synthetic_benchmark_payload(
                m_bits=args.m_bits,
                node_count=args.nodes,
                key_count=args.keys,
                seed=args.seed,
                start_nodes=args.start_nodes,
                start_node_sample_mode=args.start_node_sample_mode,
                start_node_seed=args.start_node_seed,
            ),
        }
    elif args.command == "churn":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "churn",
            "events_file": str(args.events_file),
            **ring.churn_report(
                load_churn_events(args.events_file),
                rounds=args.rounds,
                finger_repair_mode=args.finger_repair_mode,
                finger_repair_seed=args.finger_repair_seed,
            ),
        }
    elif args.command == "compare-stabilize-export":
        ring = load_ring(args.ring_file)
        comparison = ring.compare_stabilization_modes(
            joined_node=args.joined_node,
            failed_nodes=args.failed_nodes,
            rounds=args.rounds,
            modes=args.modes,
            random_seed=args.random_seed,
        )
        if args.format == "markdown":
            print(render_stabilization_comparison_markdown(comparison))
            return
        if args.format == "csv":
            print(render_stabilization_comparison_csv(comparison))
            return
        raise ValueError(f"unsupported export format {args.format!r}")
    elif args.command == "churn-export":
        ring = load_ring(args.ring_file)
        report = ring.churn_report(
            load_churn_events(args.events_file),
            rounds=args.rounds,
            finger_repair_mode=args.finger_repair_mode,
            finger_repair_seed=args.finger_repair_seed,
        )
        if args.format == "markdown":
            print(render_churn_report_markdown(report))
            return
        if args.format == "csv":
            print(render_churn_report_csv(report))
            return
        raise ValueError(f"unsupported export format {args.format!r}")
    elif args.command == "graphviz":
        ring = load_ring(args.ring_file)
        payload = {
            "command": "graphviz",
            "mode": args.mode,
            "dot": ring.export_graphviz(
                args.mode,
                start_node=args.start_node,
                key=args.key,
                joined_node=args.joined_node,
                failed_nodes=args.failed_nodes,
                rounds=args.rounds,
                finger_repair_mode=args.finger_repair_mode,
                finger_repair_seed=args.finger_repair_seed,
            ),
        }
    else:
        raise ValueError(f"unsupported command {args.command!r}")

    print(json.dumps(payload, indent=2 if getattr(args, "pretty", False) else None))


if __name__ == "__main__":
    main()
