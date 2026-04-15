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
class LogEntry:
    term: int
    command: str

    def to_dict(self) -> dict[str, object]:
        return {"term": self.term, "command": self.command}


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
    log: list[LogEntry] = field(default_factory=list)
    commit_index: int = 0

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

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["role"] = self.role.value
        payload["votes_received"] = sorted(self.votes_received)
        payload["log"] = [entry.to_dict() for entry in self.log]
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


@dataclass
class AppendAttemptResult:
    success: bool
    prev_index: int
    prev_term: int
    next_index: int
    replicated_entries: int = 0
    truncated_entries: int = 0


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
        self.replication_state: dict[str, dict[str, dict[str, int]]] = {}

    def log(self, node: str, event: str, term: int, **details: object) -> None:
        self.events.append(Event(self.tick, node, event, term, details))

    def initialize_leader_replication_state(self, leader: NodeState) -> None:
        self.replication_state[leader.node_id] = {
            peer_id: {"next_index": len(leader.log) + 1, "match_index": 0}
            for peer_id in leader.peers
        }

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

    def force_log(self, node_id: str, entries: list[dict[str, object]], commit_index: int | None = None) -> None:
        node = self.nodes[node_id]
        node.log = [LogEntry(term=int(entry["term"]), command=str(entry["command"])) for entry in entries]
        node.commit_index = min(commit_index if commit_index is not None else node.commit_index, len(node.log))
        self.log(
            node_id,
            "log_forced",
            node.current_term,
            log_length=len(node.log),
            commit_index=node.commit_index,
        )

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
            self.initialize_leader_replication_state(node)
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
            self.replicate_to_follower(leader, self.nodes[peer_id])
            if leader.role != Role.LEADER:
                return
        self.refresh_commit_indexes(leader)

    def replicate_to_follower(self, leader: NodeState, follower: NodeState) -> None:
        if leader.node_id in self.partitioned_nodes or follower.node_id in self.partitioned_nodes:
            self.log(leader.node_id, "heartbeat_blocked", leader.current_term, peer=follower.node_id)
            return
        if follower.current_term > leader.current_term:
            self.log(leader.node_id, "leader_stale", follower.current_term, peer=follower.node_id)
            leader.become_follower(follower.current_term, self.tick, self.base_timeouts[leader.node_id])
            self.replication_state.pop(leader.node_id, None)
            return

        follower.become_follower(leader.current_term, self.tick, self.base_timeouts[follower.node_id], leader_id=leader.node_id)
        follower_state = self.replication_state.setdefault(
            leader.node_id,
            {peer_id: {"next_index": len(leader.log) + 1, "match_index": 0} for peer_id in leader.peers},
        )[follower.node_id]

        attempts = 0
        while True:
            attempts += 1
            result = self.try_append_entries(leader, follower, follower_state["next_index"])
            if result.success:
                follower_state["match_index"] = len(follower.log)
                follower_state["next_index"] = len(follower.log) + 1
                self.log(
                    leader.node_id,
                    "heartbeat_ack",
                    leader.current_term,
                    peer=follower.node_id,
                    replicated_entries=result.replicated_entries,
                    truncated_entries=result.truncated_entries,
                    follower_log_length=len(follower.log),
                    attempts=attempts,
                    next_index=follower_state["next_index"],
                )
                return

            previous_next_index = follower_state["next_index"]
            follower_state["next_index"] = max(1, follower_state["next_index"] - 1)
            self.log(
                leader.node_id,
                "append_rejected",
                leader.current_term,
                peer=follower.node_id,
                prev_log_index=result.prev_index,
                prev_log_term=result.prev_term,
                follower_log_length=len(follower.log),
                next_index=previous_next_index,
                retry_next_index=follower_state["next_index"],
            )
            if follower_state["next_index"] == previous_next_index:
                return

    def try_append_entries(self, leader: NodeState, follower: NodeState, next_index: int) -> AppendAttemptResult:
        prev_index = next_index - 1
        prev_term = leader.log[prev_index - 1].term if prev_index > 0 else 0
        if prev_index > len(follower.log):
            return AppendAttemptResult(False, prev_index, prev_term, next_index)
        if prev_index > 0 and follower.log[prev_index - 1].term != prev_term:
            return AppendAttemptResult(False, prev_index, prev_term, next_index)

        leader_suffix = leader.log[next_index - 1 :]
        truncated_entries = 0
        index = next_index - 1
        while index < len(leader.log) and index < len(follower.log):
            if follower.log[index].term != leader.log[index].term or follower.log[index].command != leader.log[index].command:
                truncated_entries = len(follower.log) - index
                follower.log = follower.log[:index]
                break
            index += 1

        replicated_entries = 0
        append_start = len(follower.log)
        for entry in leader.log[append_start:]:
            follower.log.append(LogEntry(entry.term, entry.command))
            replicated_entries += 1

        return AppendAttemptResult(True, prev_index, prev_term, next_index, replicated_entries, truncated_entries)

    def refresh_commit_indexes(self, leader: NodeState) -> None:
        follower_state = self.replication_state.get(leader.node_id, {})
        replicated_indexes = [len(leader.log)] + [state["match_index"] for state in follower_state.values()]
        majority_position = len(replicated_indexes) // 2
        majority_length = sorted(replicated_indexes)[majority_position]
        new_commit_index = min(majority_length, len(leader.log))
        if new_commit_index > leader.commit_index:
            leader.commit_index = new_commit_index
            self.log(leader.node_id, "commit_advanced", leader.current_term, commit_index=new_commit_index)
        for node in self.nodes.values():
            if node is leader:
                continue
            replicated_commit = min(len(node.log), leader.commit_index)
            if replicated_commit > node.commit_index:
                node.commit_index = replicated_commit
                self.log(leader.node_id, "commit_replicated", leader.current_term, peer=node.node_id, commit_index=node.commit_index)
            else:
                node.commit_index = min(node.commit_index, len(node.log))

    def append_client_command(self, command: str) -> None:
        leader = self.current_leader()
        if leader is None:
            raise ValueError("cannot append command without a leader")
        leader.log.append(LogEntry(term=leader.current_term, command=command))
        self.log(
            leader.node_id,
            "client_command_appended",
            leader.current_term,
            command=command,
            log_index=len(leader.log),
        )
        self.broadcast_heartbeat(leader)
        leader.last_heartbeat_tick = self.tick

    def current_leader(self) -> NodeState | None:
        leaders = [node for node in self.nodes.values() if node.role == Role.LEADER]
        if len(leaders) != 1:
            return None
        return leaders[0]

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


def require_step_fields(step: dict[str, object], *fields: str) -> None:
    missing = [field for field in fields if field not in step]
    if missing:
        raise ValueError(f"step action {step.get('action', '<missing>')} missing fields: {', '.join(missing)}")


def run_scenario(config: dict[str, object]) -> dict[str, object]:
    simulator = RaftElectionSimulator(
        node_ids=config["nodes"],
        election_timeouts=config["election_timeouts"],
        heartbeat_interval=config.get("heartbeat_interval", 2),
    )
    for step in config.get("steps", []):
        action = step["action"]
        if action == "run":
            require_step_fields(step, "ticks")
            simulator.run(step["ticks"])
        elif action == "isolate":
            require_step_fields(step, "node")
            simulator.isolate(step["node"])
        elif action == "heal":
            require_step_fields(step, "node")
            simulator.heal(step["node"])
        elif action == "set-timeout":
            require_step_fields(step, "node", "timeout")
            simulator.apply_timeout_override(step["node"], step["timeout"])
        elif action == "client-write":
            require_step_fields(step, "command")
            simulator.append_client_command(step["command"])
        elif action == "force-log":
            require_step_fields(step, "node", "entries")
            simulator.force_log(step["node"], step["entries"], step.get("commit_index"))
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
