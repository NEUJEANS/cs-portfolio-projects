from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Node:
    process_id: int


@dataclass(frozen=True)
class ElectionMessage:
    candidate_id: int
    hops: int = 0

    def forward(self) -> "ElectionMessage":
        return ElectionMessage(candidate_id=self.candidate_id, hops=self.hops + 1)


class RingElectionSimulator:
    def __init__(self, process_ids: Iterable[int]) -> None:
        raw_ids = list(process_ids)
        if len(raw_ids) < 2:
            raise ValueError("at least two process ids are required")
        if len(set(raw_ids)) != len(raw_ids):
            raise ValueError("process ids must be unique")
        if any(process_id < 0 for process_id in raw_ids):
            raise ValueError("process ids must be non-negative")
        self.nodes = [Node(process_id=value) for value in raw_ids]

    def simulate(self, initiator: int, failed: Iterable[int] | None = None) -> dict[str, object]:
        failed_set = set(failed or [])
        if failed_set and not failed_set.issubset({node.process_id for node in self.nodes}):
            raise ValueError("failed ids must belong to the ring")
        active_nodes = [node for node in self.nodes if node.process_id not in failed_set]
        if len(active_nodes) < 2:
            raise ValueError("need at least two active nodes to run the election")
        if initiator in failed_set:
            raise ValueError("initiator must be active")
        if initiator not in {node.process_id for node in self.nodes}:
            raise ValueError("initiator must belong to the ring")

        ordered_active = [node.process_id for node in self.nodes if node.process_id not in failed_set]
        index_by_id = {process_id: index for index, process_id in enumerate(ordered_active)}
        current_id = initiator
        message = ElectionMessage(candidate_id=initiator)
        trace: list[dict[str, int | str]] = []
        message_count = 0

        while True:
            next_id = ordered_active[(index_by_id[current_id] + 1) % len(ordered_active)]
            incoming = message.forward()
            message_count += 1
            action = "forward"

            if incoming.candidate_id < next_id:
                outgoing = ElectionMessage(candidate_id=next_id, hops=incoming.hops)
                action = "replace"
            elif incoming.candidate_id == next_id:
                trace.append(
                    {"from": current_id, "to": next_id, "candidate": incoming.candidate_id, "hops": incoming.hops, "action": "elect"}
                )
                leader_id = next_id
                break
            else:
                outgoing = incoming

            trace.append(
                {"from": current_id, "to": next_id, "candidate": outgoing.candidate_id, "hops": outgoing.hops, "action": action}
            )
            current_id = next_id
            message = outgoing

        leader_index = index_by_id[leader_id]
        announcement_trace: list[dict[str, int | str]] = []
        current_id = leader_id
        for _ in range(len(ordered_active) - 1):
            next_id = ordered_active[(index_by_id[current_id] + 1) % len(ordered_active)]
            message_count += 1
            announcement_trace.append({"from": current_id, "to": next_id, "leader": leader_id, "phase": "announce"})
            current_id = next_id

        return {
            "algorithm": "chang-roberts",
            "ring_order": [node.process_id for node in self.nodes],
            "active_ring": ordered_active,
            "failed": sorted(failed_set),
            "initiator": initiator,
            "leader": leader_id,
            "trace": trace,
            "announcement_trace": announcement_trace,
            "message_count": message_count,
            "election_messages": len(trace),
            "announcement_messages": len(announcement_trace),
            "max_id": max(ordered_active),
            "leader_index": leader_index,
            "worst_case_bound": len(ordered_active) * len(ordered_active),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate Chang-Roberts leader election on a unidirectional ring")
    parser.add_argument("--ring", nargs="+", type=int, required=True, help="Process ids in ring order")
    parser.add_argument("--initiator", type=int, required=True, help="Active process id that starts the election")
    parser.add_argument("--failed", nargs="*", type=int, default=[], help="Optional failed process ids to skip")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the JSON result")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    simulator = RingElectionSimulator(args.ring)
    result = simulator.simulate(initiator=args.initiator, failed=args.failed)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
