from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SyncOperation:
    source: str
    target: str
    direction: str = "both"


class ORSet:
    def __init__(
        self,
        adds: dict[str, set[str]] | None = None,
        tombstones: set[str] | None = None,
        counters: dict[str, int] | None = None,
    ) -> None:
        self.adds: dict[str, set[str]] = {
            element: set(tags)
            for element, tags in (adds or {}).items()
            if element and tags
        }
        self.tombstones: set[str] = set(tombstones or set())
        self.counters: dict[str, int] = {replica: int(value) for replica, value in (counters or {}).items()}
        self._normalize_counters_from_tags()

    def copy(self) -> "ORSet":
        return ORSet(
            adds={element: set(tags) for element, tags in self.adds.items()},
            tombstones=set(self.tombstones),
            counters=dict(self.counters),
        )

    def add(self, replica: str, element: str) -> str:
        self._validate_replica(replica)
        self._validate_element(element)
        counter = self.counters.get(replica, 0) + 1
        self.counters[replica] = counter
        tag = f"{replica}:{counter}"
        self.adds.setdefault(element, set()).add(tag)
        return tag

    def remove(self, element: str) -> list[str]:
        self._validate_element(element)
        observed = sorted(self.active_tags(element))
        self.tombstones.update(observed)
        return observed

    def active_tags(self, element: str) -> set[str]:
        self._validate_element(element)
        return set(self.adds.get(element, set()) - self.tombstones)

    def contains(self, element: str) -> bool:
        return bool(self.active_tags(element))

    def elements(self) -> list[str]:
        return sorted(element for element in self.adds if self.contains(element))

    def merge(self, other: "ORSet") -> "ORSet":
        merged_adds: dict[str, set[str]] = {
            element: set(tags) for element, tags in self.adds.items()
        }
        for element, tags in other.adds.items():
            merged_adds.setdefault(element, set()).update(tags)
        merged_counters = dict(self.counters)
        for replica, counter in other.counters.items():
            merged_counters[replica] = max(merged_counters.get(replica, 0), counter)
        merged = ORSet(
            adds=merged_adds,
            tombstones=self.tombstones | other.tombstones,
            counters=merged_counters,
        )
        merged._normalize_counters_from_tags()
        return merged

    def to_dict(self) -> dict[str, object]:
        return {
            "elements": self.elements(),
            "active_tags": {
                element: sorted(self.active_tags(element))
                for element in sorted(self.adds)
                if self.active_tags(element)
            },
            "observed_tags": {
                element: sorted(self.adds[element]) for element in sorted(self.adds)
            },
            "tombstones": sorted(self.tombstones),
            "counters": dict(sorted(self.counters.items())),
        }

    def _normalize_counters_from_tags(self) -> None:
        for replica, counter in list(self.counters.items()):
            if counter < 0:
                raise ValueError("replica counters must be non-negative")
            if counter == 0:
                self.counters.pop(replica)
        for tags in list(self.adds.values()) + [self.tombstones]:
            for tag in tags:
                replica, counter = parse_tag(tag)
                self.counters[replica] = max(self.counters.get(replica, 0), counter)

    @staticmethod
    def _validate_replica(replica: str) -> None:
        if not replica:
            raise ValueError("replica must be non-empty")

    @staticmethod
    def _validate_element(element: str) -> None:
        if not element:
            raise ValueError("element must be non-empty")


class ReplicaCluster:
    def __init__(self, replicas: Iterable[str]) -> None:
        replica_list = list(replicas)
        if not replica_list or any(not replica for replica in replica_list):
            raise ValueError("replicas must contain only non-empty names")
        if len(set(replica_list)) != len(replica_list):
            raise ValueError("replica names must be unique")
        self.replicas = tuple(sorted(replica_list))
        self.states = {replica: ORSet() for replica in self.replicas}
        self.timeline: list[dict[str, object]] = []

    def add(self, replica: str, element: str) -> str:
        state = self._state(replica)
        tag = state.add(replica, element)
        self.timeline.append(
            {
                "op": "add",
                "replica": replica,
                "element": element,
                "tag": tag,
                "state": state.to_dict(),
            }
        )
        return tag

    def remove(self, replica: str, element: str) -> list[str]:
        state = self._state(replica)
        removed_tags = state.remove(element)
        self.timeline.append(
            {
                "op": "remove",
                "replica": replica,
                "element": element,
                "removed_tags": removed_tags,
                "state": state.to_dict(),
            }
        )
        return removed_tags

    def sync(self, source: str, target: str, *, direction: str = "both") -> dict[str, object]:
        self._validate_sync_direction(direction)
        self._state(source)
        self._state(target)
        if direction == "both":
            source_before = self.states[source].copy()
            target_before = self.states[target].copy()
            self.states[source] = source_before.merge(target_before)
            self.states[target] = target_before.merge(source_before)
        elif direction == "forward":
            self.states[target] = self.states[target].merge(self.states[source])
        else:
            self.states[source] = self.states[source].merge(self.states[target])

        event = {
            "op": "sync",
            "source": source,
            "target": target,
            "direction": direction,
            "source_state": self.states[source].to_dict(),
            "target_state": self.states[target].to_dict(),
        }
        self.timeline.append(event)
        return event

    def convergence_report(self) -> dict[str, object]:
        membership = {
            replica: self.states[replica].elements()
            for replica in self.replicas
        }
        tag_views = {
            replica: self.states[replica].to_dict()["active_tags"]
            for replica in self.replicas
        }
        state_views = {
            replica: self.states[replica].to_dict()
            for replica in self.replicas
        }
        baseline_state = next(iter(state_views.values()), {})
        converged = all(view == baseline_state for view in state_views.values())
        return {
            "converged": converged,
            "membership": membership,
            "active_tags": tag_views,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "replicas": {
                replica: self.states[replica].to_dict() for replica in self.replicas
            },
            "timeline": list(self.timeline),
            "convergence": self.convergence_report(),
        }

    def run_script(self, operations: Sequence[dict[str, object]]) -> dict[str, object]:
        for index, operation in enumerate(operations, start=1):
            op_name = str(operation.get("op", "")).strip()
            if op_name == "add":
                self.add(str(operation["replica"]), str(operation["element"]))
            elif op_name == "remove":
                self.remove(str(operation["replica"]), str(operation["element"]))
            elif op_name == "sync":
                self.sync(
                    str(operation["source"]),
                    str(operation["target"]),
                    direction=str(operation.get("direction", "both")),
                )
            else:
                raise ValueError(f"unsupported op at index {index}: {op_name or '<missing>'}")
        return self.snapshot()

    def _state(self, replica: str) -> ORSet:
        try:
            return self.states[replica]
        except KeyError as exc:
            raise ValueError(f"unknown replica: {replica}") from exc

    @staticmethod
    def _validate_sync_direction(direction: str) -> None:
        if direction not in {"both", "forward", "reverse"}:
            raise ValueError("sync direction must be one of: both, forward, reverse")


def parse_tag(tag: str) -> tuple[str, int]:
    replica, separator, counter_text = tag.partition(":")
    if not separator or not replica or not counter_text.isdigit():
        raise ValueError(f"invalid OR-Set tag: {tag}")
    return replica, int(counter_text)


def load_script(path: str | Path) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict):
        operations = payload.get("operations")
    else:
        operations = payload
    if not isinstance(operations, list):
        raise ValueError("script JSON must be a list of operations or an object with an operations list")
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError("each operation must be an object")
    return operations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Observed-remove set CRDT lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_script = subparsers.add_parser("run-script", help="run a JSON operation script across replicas")
    run_script.add_argument("--replicas", nargs="+", required=True)
    run_script.add_argument("--script", required=True)

    add = subparsers.add_parser("add", help="apply one add on a fresh cluster")
    add.add_argument("--replicas", nargs="+", required=True)
    add.add_argument("--replica", required=True)
    add.add_argument("--element", required=True)

    remove = subparsers.add_parser("remove", help="sync optional seed state, then remove an observed element")
    remove.add_argument("--replicas", nargs="+", required=True)
    remove.add_argument("--seed-script")
    remove.add_argument("--replica", required=True)
    remove.add_argument("--element", required=True)

    sync = subparsers.add_parser("sync", help="sync two replicas on a fresh or seeded cluster")
    sync.add_argument("--replicas", nargs="+", required=True)
    sync.add_argument("--seed-script")
    sync.add_argument("--source", required=True)
    sync.add_argument("--target", required=True)
    sync.add_argument("--direction", choices=["both", "forward", "reverse"], default="both")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cluster = ReplicaCluster(args.replicas)

    if args.command == "run-script":
        result = cluster.run_script(load_script(args.script))
    elif args.command == "add":
        cluster.add(args.replica, args.element)
        result = cluster.snapshot()
    elif args.command == "remove":
        if args.seed_script:
            cluster.run_script(load_script(args.seed_script))
        cluster.remove(args.replica, args.element)
        result = cluster.snapshot()
    else:
        if args.seed_script:
            cluster.run_script(load_script(args.seed_script))
        cluster.sync(args.source, args.target, direction=args.direction)
        result = cluster.snapshot()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
