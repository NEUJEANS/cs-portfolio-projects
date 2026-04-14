from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class Role(str, Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class NodeState:
    node_id: str
    peers: list[str]
    role: Role = Role.FOLLOWER
    current_term: int = 0
    voted_for: str | None = None
    election_deadline: int = 0
    heartbeat_interval: int = 2
    last_heartbeat_tick: int | None = None
    votes_received: set[str] = field(default_factory=set)

    def reset_election_deadline(self, tick: int, timeout: int) -> None:
        self.election_deadline = tick + timeout

    def become_follower(self, term: int, tick: int, timeout: int, leader_id: str | None = None) -> None:
        self.role = Role.FOLLOWER
        self.current_term = term
        self.voted_for = leader_id
        self.votes_received.clear()
        self.reset_election_deadline(tick, timeout)

    def start_election(self, tick: int, timeout: int) -> None:
        self.role = Role.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.reset_election_deadline(tick, timeout)

    def become_leader(self, tick: int) -> None:
        self.role = Role.LEADER
        self.last_heartbeat_tick = tick

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["role"] = self.role.value
        payload["votes_received"] = sorted(self.votes_received)
        return payload


@dataclass
class Event:
    tick: int
    node: str
    event: str
    term: int
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "tick": self.tick,
            "node": self.node,
            "event": self.event,
            "term": self.term,
            "details": self.details,
        }


class RaftElectionSimulator:
    def __init__(
        self,
        node_ids: Iterable[str],
        election_timeouts: dict[str, int],
        heartbeat_interval: int = 2,
    ) -> None:
        ids = list(node_ids)
        if len(ids) < 3:
            raise ValueError("raft elections need at least 3 nodes")
        if set(ids) != set(election_timeouts):
            raise ValueError("timeouts must be provided for every node")
        self.tick = 0
        self.heartbeat_interval = heartbeat_interval
        self.nodes = {
            node_id: NodeState(
                node_id=node_id,
                peers=[peer for peer in ids if peer != node_id],
                heartbeat_interval=heartbeat_interval,
            )
            for node_id in ids
        }
        for node_id, node in self.nodes.items():
            node.reset_election_deadline(self.tick, election_timeouts[node_id])
        self.base_timeouts = dict(election_timeouts)
        self.events: list[Event] = []
        self.partitioned_nodes: set[str] = set()

    def log(self, node: str, event: str, term: int, **details: object) -> None:
        self.events.append(Event(self.tick, node, event, term, details))

    def apply_timeout_override(self, node_id: str, timeout: int) -> None:
        self.base_timeouts[node_id] = timeout
        self.nodes[node_id].reset_election_deadline(self.tick, timeout)
        self.log(node_id, "timeout_override", self.nodes[node_id].current_term, timeout=timeout)

    def isolate(self, node_id: str) -> None:
        self.partitioned_nodes.add(node_id)
        self.log(node_id, "isolated", self.nodes[node_id].current_term)

    def heal(self, node_id: str) -> None:
        self.partitioned_nodes.discard(node_id)
        self.log(node_id, "healed", self.nodes[node_id].current_term)

    def tick_once(self) -> None:
        self.tick += 1
        for node in sorted(self.nodes.values(), key=lambda item: item.node_id):
            if node.role == Role.LEADER:
                if node.last_heartbeat_tick is None or self.tick - node.last_heartbeat_tick >= node.heartbeat_interval:
                    self.broadcast_heartbeat(node)
                    node.last_heartbeat_tick = self.tick
            elif self.tick >= node.election_deadline:
                self.start_election(node)

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.tick_once()

    def start_election(self, node: NodeState) -> None:
        node.start_election(self.tick, self.base_timeouts[node.node_id])
        self.log(node.node_id, "election_started", node.current_term, votes=sorted(node.votes_received))
        for peer_id in node.peers:
            self.request_vote(node, self.nodes[peer_id])
        if self.has_majority(node):
            node.become_leader(self.tick)
            self.log(node.node_id, "leader_elected", node.current_term, votes=sorted(node.votes_received))
            self.broadcast_heartbeat(node)

    def request_vote(self, candidate: NodeState, peer: NodeState) -> None:
        if candidate.node_id in self.partitioned_nodes or peer.node_id in self.partitioned_nodes:
            self.log(candidate.node_id, "vote_blocked", candidate.current_term, peer=peer.node_id)
            return
        if peer.current_term > candidate.current_term:
            self.log(candidate.node_id, "vote_rejected_higher_term", peer.current_term, peer=peer.node_id)
            candidate.become_follower(peer.current_term, self.tick, self.base_timeouts[candidate.node_id])
            return
        if peer.current_term < candidate.current_term:
            peer.become_follower(candidate.current_term, self.tick, self.base_timeouts[peer.node_id])
        granted = peer.voted_for in (None, candidate.node_id)
        if granted:
            peer.voted_for = candidate.node_id
            peer.reset_election_deadline(self.tick, self.base_timeouts[peer.node_id])
            candidate.votes_received.add(peer.node_id)
            self.log(candidate.node_id, "vote_granted", candidate.current_term, peer=peer.node_id)
        else:
            self.log(candidate.node_id, "vote_rejected", candidate.current_term, peer=peer.node_id, voted_for=peer.voted_for)

    def broadcast_heartbeat(self, leader: NodeState) -> None:
        self.log(leader.node_id, "heartbeat_broadcast", leader.current_term)
        for peer_id in leader.peers:
            self.receive_heartbeat(leader, self.nodes[peer_id])

    def receive_heartbeat(self, leader: NodeState, follower: NodeState) -> None:
        if leader.node_id in self.partitioned_nodes or follower.node_id in self.partitioned_nodes:
            self.log(leader.node_id, "heartbeat_blocked", leader.current_term, peer=follower.node_id)
            return
        if follower.current_term > leader.current_term:
            self.log(leader.node_id, "leader_stale", follower.current_term, peer=follower.node_id)
            leader.become_follower(follower.current_term, self.tick, self.base_timeouts[leader.node_id])
            return
        follower.become_follower(leader.current_term, self.tick, self.base_timeouts[follower.node_id], leader_id=leader.node_id)
        self.log(leader.node_id, "heartbeat_ack", leader.current_term, peer=follower.node_id)

    def has_majority(self, node: NodeState) -> bool:
        return len(node.votes_received) > len(self.nodes) // 2

    def summary(self) -> dict[str, object]:
        leaders = [node.node_id for node in self.nodes.values() if node.role == Role.LEADER]
        return {
            "tick": self.tick,
            "leaders": leaders,
            "nodes": {node_id: node.to_dict() for node_id, node in sorted(self.nodes.items())},
            "events": [event.to_dict() for event in self.events],
        }


def load_scenario(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate a Raft leader election timeline.")
    parser.add_argument("--scenario", required=True, help="Path to a JSON scenario file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def run_scenario(config: dict[str, object]) -> dict[str, object]:
    simulator = RaftElectionSimulator(
        node_ids=config["nodes"],
        election_timeouts=config["election_timeouts"],
        heartbeat_interval=config.get("heartbeat_interval", 2),
    )
    for step in config.get("steps", []):
        action = step["action"]
        if action == "run":
            simulator.run(step["ticks"])
        elif action == "isolate":
            simulator.isolate(step["node"])
        elif action == "heal":
            simulator.heal(step["node"])
        elif action == "set-timeout":
            simulator.apply_timeout_override(step["node"], step["timeout"])
        else:
            raise ValueError(f"unsupported action: {action}")
    return simulator.summary()


def main() -> None:
    args = build_parser().parse_args()
    summary = run_scenario(load_scenario(args.scenario))
    if args.pretty:
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(summary))


if __name__ == "__main__":
    main()
