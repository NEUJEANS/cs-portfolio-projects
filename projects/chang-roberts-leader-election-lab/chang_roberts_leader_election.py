from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from statistics import mean
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

    def _validate_active_ring(self, failed: Iterable[int] | None = None) -> tuple[list[int], set[int], dict[int, int]]:
        failed_set = set(failed or [])
        ring_ids = {node.process_id for node in self.nodes}
        if failed_set and not failed_set.issubset(ring_ids):
            raise ValueError("failed ids must belong to the ring")
        ordered_active = [node.process_id for node in self.nodes if node.process_id not in failed_set]
        if len(ordered_active) < 2:
            raise ValueError("need at least two active nodes to run the election")
        index_by_id = {process_id: index for index, process_id in enumerate(ordered_active)}
        return ordered_active, failed_set, index_by_id

    def _build_announcement_trace(self, ordered_active: list[int], index_by_id: dict[int, int], leader_id: int) -> list[dict[str, int | str]]:
        announcement_trace: list[dict[str, int | str]] = []
        current_id = leader_id
        for _ in range(len(ordered_active) - 1):
            next_id = ordered_active[(index_by_id[current_id] + 1) % len(ordered_active)]
            announcement_trace.append({"from": current_id, "to": next_id, "leader": leader_id, "phase": "announce"})
            current_id = next_id
        return announcement_trace

    def simulate(self, initiator: int, failed: Iterable[int] | None = None) -> dict[str, object]:
        if initiator not in {node.process_id for node in self.nodes}:
            raise ValueError("initiator must belong to the ring")
        ordered_active, failed_set, index_by_id = self._validate_active_ring(failed)
        if initiator in failed_set:
            raise ValueError("initiator must be active")

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
                    {
                        "from": current_id,
                        "to": next_id,
                        "candidate": incoming.candidate_id,
                        "hops": incoming.hops,
                        "action": "elect",
                        "round": message_count,
                    }
                )
                leader_id = next_id
                break
            else:
                outgoing = incoming

            trace.append(
                {
                    "from": current_id,
                    "to": next_id,
                    "candidate": outgoing.candidate_id,
                    "hops": outgoing.hops,
                    "action": action,
                    "round": message_count,
                }
            )
            current_id = next_id
            message = outgoing

        announcement_trace = self._build_announcement_trace(ordered_active, index_by_id, leader_id)
        message_count += len(announcement_trace)

        return {
            "algorithm": "chang-roberts",
            "mode": "single-initiator",
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
            "leader_index": index_by_id[leader_id],
            "worst_case_bound": len(ordered_active) * len(ordered_active),
        }

    def simulate_multi_initiator(self, initiators: Iterable[int], failed: Iterable[int] | None = None) -> dict[str, object]:
        ordered_active, failed_set, index_by_id = self._validate_active_ring(failed)
        initiator_list = list(initiators)
        if not initiator_list:
            raise ValueError("at least one initiator is required")
        if len(set(initiator_list)) != len(initiator_list):
            raise ValueError("initiators must be unique")
        ring_ids = {node.process_id for node in self.nodes}
        if any(initiator not in ring_ids for initiator in initiator_list):
            raise ValueError("every initiator must belong to the ring")
        if any(initiator in failed_set for initiator in initiator_list):
            raise ValueError("every initiator must be active")

        pending_messages: dict[int, list[ElectionMessage]] = {
            initiator: [ElectionMessage(candidate_id=initiator)] for initiator in sorted(initiator_list)
        }
        trace: list[dict[str, int | str]] = []
        round_number = 0
        election_deliveries = 0

        while True:
            round_number += 1
            arrivals: dict[int, list[tuple[int, ElectionMessage]]] = defaultdict(list)
            for current_id in sorted(pending_messages):
                next_id = ordered_active[(index_by_id[current_id] + 1) % len(ordered_active)]
                for message in pending_messages[current_id]:
                    arrivals[next_id].append((current_id, message.forward()))

            next_pending: dict[int, list[ElectionMessage]] = {}
            elected_leader: int | None = None
            elected_hops: int | None = None
            elected_from: int | None = None

            for receiver_id in ordered_active:
                incoming_deliveries = arrivals.get(receiver_id, [])
                if not incoming_deliveries:
                    continue

                delivered_candidates = []
                for sender_id, incoming in sorted(incoming_deliveries, key=lambda item: (item[1].candidate_id, item[0])):
                    election_deliveries += 1
                    if incoming.candidate_id == receiver_id:
                        trace.append(
                            {
                                "from": sender_id,
                                "to": receiver_id,
                                "candidate": incoming.candidate_id,
                                "hops": incoming.hops,
                                "action": "elect",
                                "round": round_number,
                            }
                        )
                        elected_leader = receiver_id
                        elected_hops = incoming.hops
                        elected_from = sender_id
                        break

                    replaced = incoming.candidate_id < receiver_id
                    outgoing_candidate = receiver_id if replaced else incoming.candidate_id
                    trace.append(
                        {
                            "from": sender_id,
                            "to": receiver_id,
                            "candidate": outgoing_candidate,
                            "hops": incoming.hops,
                            "action": "replace" if replaced else "forward",
                            "round": round_number,
                        }
                    )
                    delivered_candidates.append(outgoing_candidate)

                if elected_leader is not None:
                    break
                if delivered_candidates:
                    next_pending[receiver_id] = [ElectionMessage(candidate_id=max(delivered_candidates), hops=max(message.hops for _, message in incoming_deliveries))]

            if elected_leader is not None:
                leader_id = elected_leader
                break

            pending_messages = next_pending

        announcement_trace = self._build_announcement_trace(ordered_active, index_by_id, leader_id)
        rounds = max((step["round"] for step in trace), default=0)
        return {
            "algorithm": "chang-roberts",
            "mode": "multi-initiator-lockstep",
            "ring_order": [node.process_id for node in self.nodes],
            "active_ring": ordered_active,
            "failed": sorted(failed_set),
            "initiators": sorted(initiator_list),
            "leader": leader_id,
            "trace": trace,
            "announcement_trace": announcement_trace,
            "message_count": election_deliveries + len(announcement_trace),
            "election_messages": election_deliveries,
            "announcement_messages": len(announcement_trace),
            "max_id": max(ordered_active),
            "leader_index": index_by_id[leader_id],
            "worst_case_bound": len(ordered_active) * len(ordered_active),
            "rounds": rounds,
            "contention": {"simultaneous_initiators": len(initiator_list), "lockstep": True},
            "elected_from": elected_from,
            "elected_hops": elected_hops,
        }

    def benchmark_contention(self, failed: Iterable[int] | None = None) -> dict[str, object]:
        ordered_active, failed_set, _ = self._validate_active_ring(failed)
        samples: list[dict[str, object]] = []

        for initiator_count in range(1, len(ordered_active) + 1):
            combinations_for_count = list(combinations(ordered_active, initiator_count))
            results = []
            for initiators in combinations_for_count:
                if initiator_count == 1:
                    result = self.simulate(initiator=initiators[0], failed=failed_set)
                else:
                    result = self.simulate_multi_initiator(initiators=initiators, failed=failed_set)
                results.append(result)

            election_messages = [result["election_messages"] for result in results]
            total_messages = [result["message_count"] for result in results]
            rounds = [result.get("rounds", result["election_messages"]) for result in results]

            def initiator_key(result: dict[str, object]) -> tuple[int, ...]:
                if "initiators" in result:
                    return tuple(result["initiators"])
                return (result["initiator"],)

            cheapest = min(results, key=lambda result: (result["message_count"], initiator_key(result)))
            most_expensive = max(results, key=lambda result: (result["message_count"], initiator_key(result)))

            samples.append(
                {
                    "initiator_count": initiator_count,
                    "combinations_evaluated": len(combinations_for_count),
                    "average_election_messages": round(mean(election_messages), 2),
                    "average_total_messages": round(mean(total_messages), 2),
                    "average_rounds": round(mean(rounds), 2),
                    "min_total_messages": min(total_messages),
                    "max_total_messages": max(total_messages),
                    "cheapest_initiators": list(initiator_key(cheapest)),
                    "most_expensive_initiators": list(initiator_key(most_expensive)),
                }
            )

        best_average = min(samples, key=lambda sample: (sample["average_total_messages"], sample["initiator_count"]))
        worst_average = max(samples, key=lambda sample: (sample["average_total_messages"], sample["initiator_count"]))
        return {
            "algorithm": "chang-roberts",
            "mode": "contention-benchmark",
            "ring_order": [node.process_id for node in self.nodes],
            "active_ring": ordered_active,
            "failed": sorted(failed_set),
            "rows": samples,
            "summary": {
                "best_average_initiator_count": best_average["initiator_count"],
                "worst_average_initiator_count": worst_average["initiator_count"],
                "evaluated_combinations": sum(sample["combinations_evaluated"] for sample in samples),
            },
        }


def _participant_label(process_id: int) -> str:
    return f"P{process_id}"


def render_mermaid_sequence(result: dict[str, object]) -> str:
    active_ring = result["active_ring"]
    leader = result["leader"]
    lines = ["sequenceDiagram"]
    for process_id in active_ring:
        lines.append(f"    participant {_participant_label(process_id)} as {process_id}")
    if "initiators" in result:
        initiators = ", ".join(str(value) for value in result["initiators"])
        lines.append(f"    Note over {_participant_label(active_ring[0])}: initiators={initiators} (lockstep)")
    else:
        initiator = result["initiator"]
        lines.append(f"    Note over {_participant_label(initiator)}: initiator={initiator}")

    for index, step in enumerate(result["trace"], start=1):
        arrow = "->>"
        round_text = f"round {step['round']}, " if "round" in step else ""
        if step["action"] == "replace":
            detail = f"election #{index}: {round_text}replace with {step['candidate']} (hop {step['hops']})"
        elif step["action"] == "elect":
            detail = f"election #{index}: {round_text}elect leader {step['candidate']} (hop {step['hops']})"
            arrow = "-->>"
        else:
            detail = f"election #{index}: {round_text}forward {step['candidate']} (hop {step['hops']})"
        lines.append(f"    {_participant_label(step['from'])}{arrow}{_participant_label(step['to'])}: {detail}")

    if result["announcement_trace"]:
        lines.append(f"    Note over {_participant_label(leader)}: leader {leader} announces victory")
    for index, step in enumerate(result["announcement_trace"], start=1):
        lines.append(
            f"    {_participant_label(step['from'])}-->>{_participant_label(step['to'])}: announce #{index}: leader {step['leader']}"
        )

    return "\n".join(lines)


def build_output(result: dict[str, object], include_visualization: bool) -> dict[str, object]:
    if not include_visualization:
        return result
    enriched = dict(result)
    enriched["visualizations"] = {"mermaid_sequence": render_mermaid_sequence(result)}
    return enriched


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate Chang-Roberts leader election on a unidirectional ring")
    parser.add_argument("--ring", nargs="+", type=int, required=True, help="Process ids in ring order")
    initiator_group = parser.add_mutually_exclusive_group(required=True)
    initiator_group.add_argument("--initiator", type=int, help="Active process id that starts the election")
    initiator_group.add_argument(
        "--initiators",
        nargs="+",
        type=int,
        help="Active process ids that begin simultaneously in lockstep rounds",
    )
    initiator_group.add_argument(
        "--benchmark-contention",
        action="store_true",
        help="Benchmark all 1..n initiator combinations on the active ring",
    )
    parser.add_argument("--failed", nargs="*", type=int, default=[], help="Optional failed process ids to skip")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the JSON result")
    parser.add_argument(
        "--include-visualization",
        action="store_true",
        help="Include a Mermaid sequence diagram string in the JSON output",
    )
    parser.add_argument(
        "--visualization-only",
        choices=["mermaid"],
        help="Print just the requested visualization format instead of JSON",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    simulator = RingElectionSimulator(args.ring)
    if args.benchmark_contention:
        result = simulator.benchmark_contention(failed=args.failed)
    elif args.initiators:
        result = simulator.simulate_multi_initiator(initiators=args.initiators, failed=args.failed)
    else:
        result = simulator.simulate(initiator=args.initiator, failed=args.failed)
    if args.visualization_only == "mermaid":
        if result["mode"] == "contention-benchmark":
            raise SystemExit("visualization-only is unavailable for contention benchmarks")
        print(render_mermaid_sequence(result))
        return
    print(json.dumps(build_output(result, include_visualization=args.include_visualization), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
