from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class SnapshotError(ValueError):
    """Raised when a saved hash-table snapshot is invalid."""


class InputDataError(ValueError):
    """Raised when build input or benchmark arguments are invalid."""


@dataclass(slots=True)
class Entry:
    key: str
    value: str
    hash_value: int
    probe_distance: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "hash_value": self.hash_value,
            "probe_distance": self.probe_distance,
        }


@dataclass(slots=True)
class OperationResult:
    action: str
    probes: int
    swaps: int = 0
    probe_distance: int = 0


@dataclass(slots=True)
class BenchmarkRow:
    trial: int
    load_factor: float
    entry_count: int
    average_insert_probes: float
    average_successful_lookup_probes: float
    max_probe_distance: int
    swap_count: int

    def to_dict(self, capacity: int) -> dict[str, Any]:
        return {
            "capacity": capacity,
            "trial": self.trial,
            "load_factor": round(self.load_factor, 4),
            "entry_count": self.entry_count,
            "average_insert_probes": round(self.average_insert_probes, 4),
            "average_successful_lookup_probes": round(self.average_successful_lookup_probes, 4),
            "max_probe_distance": self.max_probe_distance,
            "swap_count": self.swap_count,
        }


def stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


class RobinHoodHashTable:
    def __init__(self, capacity: int = 11, *, max_load_factor: float = 0.75, auto_resize: bool = True) -> None:
        if capacity < 3:
            raise ValueError("capacity must be at least 3")
        if not 0 < max_load_factor <= 0.95:
            raise ValueError("max_load_factor must be between 0 and 0.95")
        self.capacity = capacity
        self.max_load_factor = max_load_factor
        self.auto_resize = auto_resize
        self.size = 0
        self.slots: list[Entry | None] = [None] * capacity

    def __len__(self) -> int:
        return self.size

    def _ensure_capacity_for_insert(self) -> None:
        if not self.auto_resize:
            return
        if (self.size + 1) / self.capacity <= self.max_load_factor:
            return
        self._resize(self.capacity * 2 + 1)

    def _resize(self, new_capacity: int) -> None:
        entries = [entry for entry in self.slots if entry is not None]
        self.capacity = max(3, new_capacity)
        self.size = 0
        self.slots = [None] * self.capacity
        for entry in entries:
            self._insert_entry(Entry(entry.key, entry.value, entry.hash_value, 0))

    def put(self, key: str, value: str) -> OperationResult:
        self._ensure_capacity_for_insert()
        return self._insert_entry(Entry(key, value, stable_hash(key), 0))

    def _insert_entry(self, incoming: Entry) -> OperationResult:
        index = incoming.hash_value % self.capacity
        probes = 0
        swaps = 0
        while probes < self.capacity:
            probes += 1
            resident = self.slots[index]
            if resident is None:
                self.slots[index] = incoming
                self.size += 1
                return OperationResult(
                    action="inserted",
                    probes=probes,
                    swaps=swaps,
                    probe_distance=incoming.probe_distance,
                )

            if resident.key == incoming.key:
                resident.value = incoming.value
                return OperationResult(
                    action="updated",
                    probes=probes,
                    swaps=swaps,
                    probe_distance=resident.probe_distance,
                )

            if resident.probe_distance < incoming.probe_distance:
                self.slots[index], incoming = incoming, resident
                swaps += 1

            index = (index + 1) % self.capacity
            incoming.probe_distance += 1

        raise RuntimeError("hash table is full; choose a larger capacity")

    def get(self, key: str) -> str | None:
        value, _ = self.get_with_metrics(key)
        return value

    def get_with_metrics(self, key: str) -> tuple[str | None, int]:
        hash_value = stable_hash(key)
        index = hash_value % self.capacity
        probe_distance = 0
        probes = 0
        while probe_distance < self.capacity:
            probes += 1
            resident = self.slots[index]
            if resident is None:
                return None, probes
            if resident.probe_distance < probe_distance:
                return None, probes
            if resident.key == key:
                return resident.value, probes
            index = (index + 1) % self.capacity
            probe_distance += 1
        return None, probes

    def delete(self, key: str) -> bool:
        hash_value = stable_hash(key)
        index = hash_value % self.capacity
        probe_distance = 0
        while probe_distance < self.capacity:
            resident = self.slots[index]
            if resident is None:
                return False
            if resident.probe_distance < probe_distance:
                return False
            if resident.key == key:
                self._delete_at_index(index)
                self.size -= 1
                return True
            index = (index + 1) % self.capacity
            probe_distance += 1
        return False

    def _delete_at_index(self, index: int) -> None:
        hole = index
        next_index = (index + 1) % self.capacity
        while True:
            resident = self.slots[next_index]
            if resident is None or resident.probe_distance == 0:
                self.slots[hole] = None
                return
            self.slots[hole] = Entry(
                key=resident.key,
                value=resident.value,
                hash_value=resident.hash_value,
                probe_distance=resident.probe_distance - 1,
            )
            hole = next_index
            next_index = (next_index + 1) % self.capacity

    def items(self) -> list[tuple[str, str]]:
        return sorted((entry.key, entry.value) for entry in self.slots if entry is not None)

    def cluster_lengths(self) -> list[int]:
        occupied = [slot is not None for slot in self.slots]
        if not any(occupied):
            return []
        if all(occupied):
            return [self.capacity]
        start = occupied.index(False)
        lengths: list[int] = []
        current = 0
        for offset in range(1, self.capacity + 1):
            filled = occupied[(start + offset) % self.capacity]
            if filled:
                current += 1
            elif current:
                lengths.append(current)
                current = 0
        if current:
            lengths.append(current)
        return lengths

    def stats(self) -> dict[str, Any]:
        probe_distances = [entry.probe_distance for entry in self.slots if entry is not None]
        clusters = self.cluster_lengths()
        return {
            "capacity": self.capacity,
            "size": self.size,
            "load_factor": round(self.size / self.capacity, 4),
            "max_load_factor": self.max_load_factor,
            "auto_resize": self.auto_resize,
            "max_probe_distance": max(probe_distances, default=0),
            "average_probe_distance": round(statistics.fmean(probe_distances), 4) if probe_distances else 0.0,
            "cluster_count": len(clusters),
            "cluster_lengths": clusters,
            "entries": [
                {
                    "slot": index,
                    "key": entry.key,
                    "value": entry.value,
                    "home_slot": entry.hash_value % self.capacity,
                    "probe_distance": entry.probe_distance,
                }
                for index, entry in enumerate(self.slots)
                if entry is not None
            ],
        }

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": self.size,
            "max_load_factor": self.max_load_factor,
            "auto_resize": self.auto_resize,
            "slots": [entry.to_dict() if entry is not None else None for entry in self.slots],
        }

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> "RobinHoodHashTable":
        try:
            capacity = int(payload["capacity"])
            size = int(payload["size"])
            max_load_factor = float(payload["max_load_factor"])
            auto_resize = bool(payload["auto_resize"])
            slots_payload = payload["slots"]
        except (KeyError, TypeError, ValueError) as exc:
            raise SnapshotError("snapshot is missing required fields") from exc

        if not isinstance(slots_payload, list) or len(slots_payload) != capacity:
            raise SnapshotError("snapshot slot count must match capacity")

        table = cls(capacity=capacity, max_load_factor=max_load_factor, auto_resize=auto_resize)
        keys_seen: set[str] = set()
        actual_size = 0
        for index, raw_entry in enumerate(slots_payload):
            if raw_entry is None:
                continue
            if not isinstance(raw_entry, dict):
                raise SnapshotError(f"slot {index} must be an object or null")
            try:
                key = raw_entry["key"]
                value = raw_entry["value"]
                hash_value = int(raw_entry["hash_value"])
                probe_distance = int(raw_entry["probe_distance"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SnapshotError(f"slot {index} has invalid entry fields") from exc

            if not isinstance(key, str) or not isinstance(value, str):
                raise SnapshotError(f"slot {index} key/value must be strings")

            if key in keys_seen:
                raise SnapshotError(f"duplicate key in snapshot: {key}")
            expected_hash = stable_hash(key)
            if expected_hash != hash_value:
                raise SnapshotError(f"slot {index} hash does not match key: {key}")
            expected_probe_distance = (index - (hash_value % capacity)) % capacity
            if expected_probe_distance != probe_distance:
                raise SnapshotError(
                    f"slot {index} probe distance mismatch for {key}: expected {expected_probe_distance}, got {probe_distance}"
                )

            table.slots[index] = Entry(key=key, value=value, hash_value=hash_value, probe_distance=probe_distance)
            keys_seen.add(key)
            actual_size += 1

        if actual_size != size:
            raise SnapshotError(f"snapshot size mismatch: expected {size}, found {actual_size}")
        table.size = actual_size

        for index, entry in enumerate(table.slots):
            if entry is None:
                continue
            for previous_probe in range(entry.probe_distance):
                previous_slot = table.slots[(index - previous_probe - 1) % capacity]
                if previous_slot is None:
                    raise SnapshotError(
                        f"slot {index} has a gap inside its probe sequence, breaking Robin Hood invariants"
                    )

        return table


def load_snapshot(path: Path) -> RobinHoodHashTable:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"snapshot is not valid JSON: {path}") from exc
    return RobinHoodHashTable.from_snapshot(payload)


def save_snapshot(table: RobinHoodHashTable, path: Path, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(table.to_snapshot(), indent=2 if pretty else None, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def parse_pairs_input(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            key, value = line.split(",", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            raise InputDataError(f"line {line_number} must contain ',' or '=': {raw_line}")
        key = key.strip()
        value = value.strip()
        if not key:
            raise InputDataError(f"line {line_number} has an empty key")
        pairs.append((key, value))
    return pairs


def export_entries(table: RobinHoodHashTable, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        for key, value in table.items():
            writer.writerow([key, value])


def parse_load_factors(raw: str) -> list[float]:
    values: list[float] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        value = float(chunk)
        if not 0 < value < 0.95:
            raise InputDataError("load factors must be between 0 and 0.95")
        values.append(value)
    if not values:
        raise InputDataError("at least one load factor is required")
    return values


def run_benchmark(*, capacity: int, load_factors: Iterable[float], trials: int, seed: int) -> list[BenchmarkRow]:
    if capacity < 3:
        raise InputDataError("benchmark capacity must be at least 3")
    if trials < 1:
        raise InputDataError("trials must be at least 1")

    rows: list[BenchmarkRow] = []
    for load_factor in load_factors:
        target_count = max(1, int(round(capacity * load_factor)))
        if target_count >= capacity:
            raise InputDataError("benchmark target entry count must stay below capacity")
        for trial in range(1, trials + 1):
            rng = random.Random(f"robin-hood:{capacity}:{load_factor}:{trial}:{seed}")
            keys = [f"key-{trial}-{index}-{rng.randrange(10**9)}" for index in range(target_count)]
            values = [f"value-{rng.randrange(10**9)}" for _ in range(target_count)]
            table = RobinHoodHashTable(capacity=capacity, max_load_factor=0.95, auto_resize=False)
            insert_probe_counts: list[int] = []
            swap_total = 0
            for key, value in zip(keys, values, strict=True):
                result = table.put(key, value)
                insert_probe_counts.append(result.probes)
                swap_total += result.swaps
            lookup_probe_counts = [table.get_with_metrics(key)[1] for key in keys]
            rows.append(
                BenchmarkRow(
                    trial=trial,
                    load_factor=load_factor,
                    entry_count=target_count,
                    average_insert_probes=statistics.fmean(insert_probe_counts),
                    average_successful_lookup_probes=statistics.fmean(lookup_probe_counts),
                    max_probe_distance=table.stats()["max_probe_distance"],
                    swap_count=swap_total,
                )
            )
    return rows


def save_benchmark(rows: list[BenchmarkRow], output_path: Path, *, capacity: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [row.to_dict(capacity) for row in rows]
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "capacity",
                "trial",
                "load_factor",
                "entry_count",
                "average_insert_probes",
                "average_successful_lookup_probes",
                "max_probe_distance",
                "swap_count",
            ],
        )
        writer.writeheader()
        for row in payload:
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Robin Hood hashing lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build a snapshot from key/value input")
    build_parser.add_argument("--input", required=True, type=Path, help="newline-delimited key,value or key=value pairs")
    build_parser.add_argument("--output", required=True, type=Path, help="path to write JSON snapshot")
    build_parser.add_argument("--capacity", type=int, default=11)
    build_parser.add_argument("--max-load-factor", type=float, default=0.75)
    build_parser.add_argument("--pretty", action="store_true")

    stats_parser = subparsers.add_parser("stats", help="Print snapshot statistics as JSON")
    stats_parser.add_argument("--snapshot", required=True, type=Path)
    stats_parser.add_argument("--pretty", action="store_true")

    lookup_parser = subparsers.add_parser("lookup", help="Lookup a key in a snapshot")
    lookup_parser.add_argument("--snapshot", required=True, type=Path)
    lookup_parser.add_argument("key")

    remove_parser = subparsers.add_parser("remove", help="Remove a key and save the updated snapshot")
    remove_parser.add_argument("--snapshot", required=True, type=Path)
    remove_parser.add_argument("--output", required=True, type=Path)
    remove_parser.add_argument("--pretty", action="store_true")
    remove_parser.add_argument("key")

    export_parser = subparsers.add_parser("export", help="Export sorted entries to CSV")
    export_parser.add_argument("--snapshot", required=True, type=Path)
    export_parser.add_argument("--output", required=True, type=Path)

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark probe behavior across load factors")
    benchmark_parser.add_argument("--capacity", type=int, default=127)
    benchmark_parser.add_argument("--load-factors", default="0.25,0.5,0.7,0.85")
    benchmark_parser.add_argument("--trials", type=int, default=5)
    benchmark_parser.add_argument("--seed", type=int, default=17)
    benchmark_parser.add_argument("--output", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            pairs = parse_pairs_input(args.input)
            table = RobinHoodHashTable(
                capacity=args.capacity,
                max_load_factor=args.max_load_factor,
                auto_resize=True,
            )
            for key, value in pairs:
                table.put(key, value)
            save_snapshot(table, args.output, pretty=args.pretty)
            return 0

        if args.command == "stats":
            table = load_snapshot(args.snapshot)
            print(json.dumps(table.stats(), indent=2 if args.pretty else None))
            return 0

        if args.command == "lookup":
            table = load_snapshot(args.snapshot)
            value, probes = table.get_with_metrics(args.key)
            if value is None:
                print(json.dumps({"found": False, "key": args.key, "probes": probes}))
            else:
                print(json.dumps({"found": True, "key": args.key, "value": value, "probes": probes}))
            return 0

        if args.command == "remove":
            table = load_snapshot(args.snapshot)
            removed = table.delete(args.key)
            save_snapshot(table, args.output, pretty=args.pretty)
            print(json.dumps({"removed": removed, "key": args.key, "size": table.size}))
            return 0

        if args.command == "export":
            table = load_snapshot(args.snapshot)
            export_entries(table, args.output)
            return 0

        if args.command == "benchmark":
            rows = run_benchmark(
                capacity=args.capacity,
                load_factors=parse_load_factors(args.load_factors),
                trials=args.trials,
                seed=args.seed,
            )
            save_benchmark(rows, args.output, capacity=args.capacity)
            return 0
    except (InputDataError, SnapshotError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
