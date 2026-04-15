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
        self.data[key] = sorted(
            survivors,
            key=lambda version: (
                version.replica,
                version.value,
                json.dumps(version.clock.to_dict(), sort_keys=True),
            ),
        )

    def _validate_replica(self, replica: str) -> None:
        if replica not in self.replica_clocks:
            raise ValueError(f"unknown replica: {replica}")

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key:
            raise ValueError("key must be non-empty")


@dataclass(frozen=True)
class PartitionWrite:
    replica: str
    value: str


@dataclass(frozen=True)
class PartitionScenario:
    key: str
    left_partition: tuple[str, ...]
    right_partition: tuple[str, ...]
    left_writes: tuple[PartitionWrite, ...]
    right_writes: tuple[PartitionWrite, ...]
    heal_replica: str | None = None


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


def parse_partition_write(raw: str) -> PartitionWrite:
    replica, separator, value = raw.partition(":")
    if not separator or not replica or not value:
        raise ValueError("partition writes must use replica:value format")
    return PartitionWrite(replica=replica, value=value)


def validate_partition_membership(
    replicas: Iterable[str],
    left_partition: Iterable[str],
    right_partition: Iterable[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    replica_set = set(replicas)
    left = tuple(left_partition)
    right = tuple(right_partition)
    if not left or not right:
        raise ValueError("both partitions must contain at least one replica")
    left_set = set(left)
    right_set = set(right)
    if left_set & right_set:
        raise ValueError("partitions must be disjoint")
    if left_set | right_set != replica_set:
        raise ValueError("partitions must cover every replica exactly once")
    return left, right


def simulate_partition(store: ReplicaStore, scenario: PartitionScenario) -> dict[str, object]:
    left_partition, right_partition = validate_partition_membership(
        store.replicas,
        scenario.left_partition,
        scenario.right_partition,
    )
    if scenario.heal_replica is not None:
        store._validate_replica(scenario.heal_replica)

    timeline: list[dict[str, object]] = []
    partition_lookup = {
        replica: "left" for replica in left_partition
    } | {replica: "right" for replica in right_partition}
    partition_stores = {
        "left": ReplicaStore(left_partition),
        "right": ReplicaStore(right_partition),
    }

    def apply_partition_write(write: PartitionWrite) -> VersionedValue:
        partition_name = partition_lookup.get(write.replica)
        if partition_name is None:
            raise ValueError(f"unknown replica: {write.replica}")
        partition_store = partition_stores[partition_name]
        version = partition_store.write(write.replica, scenario.key, write.value)
        timeline.append(
            {
                "event": "write",
                "partition": partition_name,
                "replica": write.replica,
                "version": version.to_dict(),
            }
        )
        return version

    for write in scenario.left_writes:
        apply_partition_write(write)
    for write in scenario.right_writes:
        apply_partition_write(write)

    versions_before_heal = sorted(
        [
            version.to_dict()
            for version in partition_stores["left"].get_versions(scenario.key)
            + partition_stores["right"].get_versions(scenario.key)
        ],
        key=lambda version: (version["replica"], version["value"], json.dumps(version["clock"], sort_keys=True)),
    )
    result: dict[str, object] = {
        "key": scenario.key,
        "partitions": {"left": list(left_partition), "right": list(right_partition)},
        "partition_snapshots": {
            name: partition_store.snapshot() for name, partition_store in partition_stores.items()
        },
        "timeline": timeline,
        "conflict_detected": len(versions_before_heal) > 1,
        "versions_before_heal": versions_before_heal,
    }

    if scenario.heal_replica is not None and versions_before_heal:
        healed_versions = [parse_version(json.dumps(version)) for version in versions_before_heal]
        for partition_store in partition_stores.values():
            for replica, clock in partition_store.replica_clocks.items():
                store.replica_clocks[replica] = store.replica_clocks[replica].merge(clock)
        for target_replica in store.replicas:
            for version in healed_versions:
                store.replicate(target_replica, scenario.key, version)
        result["snapshot_after_heal"] = store.snapshot()
        if len(store.get_versions(scenario.key)) > 1:
            merged = store.merge_conflicts(scenario.heal_replica, scenario.key)
            result["merged"] = merged.to_dict()
            result["snapshot_after_merge"] = store.snapshot()

    return result


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

    partition = subparsers.add_parser("partition", help="simulate a network partition, heal, and optional conflict merge")
    partition.add_argument("--replicas", nargs="+", required=True)
    partition.add_argument("--key", required=True)
    partition.add_argument("--left-partition", nargs="+", required=True)
    partition.add_argument("--right-partition", nargs="+", required=True)
    partition.add_argument("--left-write", action="append", default=[], help="replica:value write visible only on the left partition")
    partition.add_argument("--right-write", action="append", default=[], help="replica:value write visible only on the right partition")
    partition.add_argument("--heal-replica", help="replica that performs the deterministic merge after partitions heal")

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
    elif args.command == "partition":
        store = ReplicaStore(args.replicas)
        scenario = PartitionScenario(
            key=args.key,
            left_partition=tuple(args.left_partition),
            right_partition=tuple(args.right_partition),
            left_writes=tuple(parse_partition_write(raw) for raw in args.left_write),
            right_writes=tuple(parse_partition_write(raw) for raw in args.right_write),
            heal_replica=args.heal_replica,
        )
        result = simulate_partition(store, scenario)
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
