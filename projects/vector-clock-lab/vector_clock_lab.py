from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable, Sequence


class VectorClock:
    def __init__(self, counters: dict[str, int] | None = None) -> None:
        cleaned = counters or {}
        self.counters: dict[str, int] = {}
        for replica, value in cleaned.items():
            if value < 0:
                raise ValueError("vector clock values must be non-negative")
            if value:
                self.counters[replica] = value

    def copy(self) -> "VectorClock":
        return VectorClock(dict(self.counters))

    def to_dict(self) -> dict[str, int]:
        return dict(sorted(self.counters.items()))

    def tick(self, replica: str) -> "VectorClock":
        if not replica:
            raise ValueError("replica must be non-empty")
        updated = self.to_dict()
        updated[replica] = updated.get(replica, 0) + 1
        return VectorClock(updated)

    def merge(self, *others: "VectorClock") -> "VectorClock":
        merged = self.to_dict()
        for other in others:
            for replica, value in other.counters.items():
                merged[replica] = max(merged.get(replica, 0), value)
        return VectorClock(merged)

    def compare(self, other: "VectorClock") -> str:
        replicas = set(self.counters) | set(other.counters)
        less = False
        greater = False
        for replica in replicas:
            left = self.counters.get(replica, 0)
            right = other.counters.get(replica, 0)
            if left < right:
                less = True
            elif left > right:
                greater = True
        if less and not greater:
            return "before"
        if greater and not less:
            return "after"
        if not less and not greater:
            return "equal"
        return "concurrent"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorClock):
            return NotImplemented
        return self.to_dict() == other.to_dict()


@dataclass(frozen=True)
class VersionedValue:
    value: str
    clock: VectorClock
    replica: str

    def to_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "clock": self.clock.to_dict(),
            "replica": self.replica,
        }


class ReplicaStore:
    def __init__(self, replicas: Iterable[str]) -> None:
        replica_list = list(replicas)
        if not replica_list or any(not replica for replica in replica_list):
            raise ValueError("replicas must contain only non-empty names")
        if len(set(replica_list)) != len(replica_list):
            raise ValueError("replica names must be unique")
        self.replicas = sorted(replica_list)
        self.replica_clocks = {replica: VectorClock() for replica in self.replicas}
        self.data: dict[str, list[VersionedValue]] = {}

    def write(self, replica: str, key: str, value: str) -> VersionedValue:
        self._validate_replica(replica)
        self._validate_key(key)
        next_clock = self.replica_clocks[replica].tick(replica)
        self.replica_clocks[replica] = next_clock
        version = VersionedValue(value=value, clock=next_clock, replica=replica)
        self._integrate(key, version)
        return version

    def replicate(self, target_replica: str, key: str, version: VersionedValue) -> None:
        self._validate_replica(target_replica)
        self._validate_key(key)
        self.replica_clocks[target_replica] = self.replica_clocks[target_replica].merge(version.clock)
        self._integrate(key, version)

    def merge_conflicts(self, replica: str, key: str, strategy: str = "join") -> VersionedValue:
        self._validate_replica(replica)
        conflicts = self.get_versions(key)
        if len(conflicts) < 2:
            raise ValueError("need at least two conflicting versions to merge")
        if any(
            left.clock.compare(right.clock) != "concurrent"
            for index, left in enumerate(conflicts)
            for right in conflicts[index + 1 :]
        ):
            raise ValueError("can only merge concurrent versions")
        if strategy != "join":
            raise ValueError(f"unsupported strategy: {strategy}")
        merged_clock = VectorClock().merge(*(version.clock for version in conflicts)).tick(replica)
        merged_value = " | ".join(sorted(version.value for version in conflicts))
        merged_version = VersionedValue(value=merged_value, clock=merged_clock, replica=replica)
        self.replica_clocks[replica] = merged_clock
        self.data[key] = [merged_version]
        return merged_version

    def get_versions(self, key: str) -> list[VersionedValue]:
        self._validate_key(key)
        return list(self.data.get(key, []))

    def snapshot(self) -> dict[str, object]:
        return {
            "replica_clocks": {
                replica: clock.to_dict() for replica, clock in sorted(self.replica_clocks.items())
            },
            "data": {
                key: [version.to_dict() for version in versions]
                for key, versions in sorted(self.data.items())
            },
        }

    def _integrate(self, key: str, incoming: VersionedValue) -> None:
        current = self.data.get(key, [])
        survivors: list[VersionedValue] = []
        replaced = False
        for existing in current:
            relation = incoming.clock.compare(existing.clock)
            if relation == "before":
                if existing not in survivors:
                    survivors.append(existing)
                replaced = True
            elif relation == "after":
                continue
            elif relation == "equal":
                survivors.append(incoming)
                replaced = True
            else:
                survivors.append(existing)
        if not replaced:
            survivors.append(incoming)
        self.data[key] = sorted(survivors, key=lambda version: (version.replica, version.value, json.dumps(version.clock.to_dict(), sort_keys=True)))

    def _validate_replica(self, replica: str) -> None:
        if replica not in self.replica_clocks:
            raise ValueError(f"unknown replica: {replica}")

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key:
            raise ValueError("key must be non-empty")


def parse_clock(raw: str) -> VectorClock:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("clock JSON must be an object")
    return VectorClock({str(key): int(value) for key, value in payload.items()})


def parse_version(raw: str) -> VersionedValue:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("version JSON must be an object")
    return VersionedValue(
        value=str(payload["value"]),
        clock=parse_clock(json.dumps(payload["clock"])),
        replica=str(payload["replica"]),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vector clock lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="compare two vector clocks")
    compare.add_argument("clock_a", help='JSON object, e.g. {"a": 1, "b": 2}')
    compare.add_argument("clock_b", help='JSON object, e.g. {"a": 2, "b": 2}')

    write = subparsers.add_parser("write", help="simulate sequential writes on one replica")
    write.add_argument("--replicas", nargs="+", required=True)
    write.add_argument("--replica", required=True)
    write.add_argument("--key", required=True)
    write.add_argument("--values", nargs="+", required=True)

    conflict = subparsers.add_parser("conflict", help="simulate conflicting writes from two replicas")
    conflict.add_argument("--replicas", nargs="+", required=True)
    conflict.add_argument("--key", required=True)
    conflict.add_argument("--left-replica", required=True)
    conflict.add_argument("--left-value", required=True)
    conflict.add_argument("--right-replica", required=True)
    conflict.add_argument("--right-value", required=True)
    conflict.add_argument("--merge-replica")

    replicate = subparsers.add_parser("replicate", help="apply a remote version into a target replica store")
    replicate.add_argument("--replicas", nargs="+", required=True)
    replicate.add_argument("--target-replica", required=True)
    replicate.add_argument("--key", required=True)
    replicate.add_argument("--version", required=True, help='JSON object with value, clock, replica')

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compare":
        result = {"relation": parse_clock(args.clock_a).compare(parse_clock(args.clock_b))}
    elif args.command == "write":
        store = ReplicaStore(args.replicas)
        writes = [store.write(args.replica, args.key, value).to_dict() for value in args.values]
        result = {"writes": writes, "snapshot": store.snapshot()}
    elif args.command == "replicate":
        store = ReplicaStore(args.replicas)
        version = parse_version(args.version)
        store.replicate(args.target_replica, args.key, version)
        result = store.snapshot()
    else:
        store = ReplicaStore(args.replicas)
        left = store.write(args.left_replica, args.key, args.left_value)
        right = store.write(args.right_replica, args.key, args.right_value)
        versions = [version.to_dict() for version in store.get_versions(args.key)]
        result = {
            "left": left.to_dict(),
            "right": right.to_dict(),
            "conflict": len(versions) > 1,
            "versions": versions,
        }
        if args.merge_replica:
            merged = store.merge_conflicts(args.merge_replica, args.key)
            result["merged"] = merged.to_dict()
            result["snapshot"] = store.snapshot()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
