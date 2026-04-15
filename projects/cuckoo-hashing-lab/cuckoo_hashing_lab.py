import argparse
import csv
import json
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Entry:
    key: str
    value: str

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        return cls(key=data["key"], value=data["value"])


class CuckooHashTable:
    def __init__(self, capacity: int = 11, max_displacements: int = 32, salt_a: str = "cuckoo-a", salt_b: str = "cuckoo-b"):
        if capacity < 3:
            raise ValueError("capacity must be at least 3")
        if max_displacements < 1:
            raise ValueError("max_displacements must be positive")
        self.capacity = capacity
        self.max_displacements = max_displacements
        self.salt_a = salt_a
        self.salt_b = salt_b
        self.slots: list[Entry | None] = [None] * capacity
        self.size = 0
        self.rehash_count = 0
        self.displacement_count = 0

    def _hash(self, key: str, salt: str) -> int:
        digest = hashlib.blake2b(f"{salt}:{key}".encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.capacity

    def _positions(self, key: str) -> tuple[int, int]:
        first = self._hash(key, self.salt_a)
        second = self._hash(key, self.salt_b)
        if second == first:
            second = (second + 1) % self.capacity
        return first, second

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def get(self, key: str) -> str | None:
        for index in self._positions(key):
            entry = self.slots[index]
            if entry and entry.key == key:
                return entry.value
        return None

    def _place_without_resize(self, entry: Entry) -> bool:
        first, second = self._positions(entry.key)
        for index in (first, second):
            current = self.slots[index]
            if current is None:
                self.slots[index] = entry
                self.size += 1
                return True
            if current.key == entry.key:
                self.slots[index] = entry
                return True

        index = first
        current = entry
        for _ in range(self.max_displacements):
            self.displacement_count += 1
            current, self.slots[index] = self.slots[index], current
            if current is None:
                self.size += 1
                return True
            alternate_first, alternate_second = self._positions(current.key)
            index = alternate_second if index == alternate_first else alternate_first
            if self.slots[index] is None:
                self.slots[index] = current
                self.size += 1
                return True
        return False

    def insert(self, key: str, value: str) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        if self.get(key) is not None:
            for index in self._positions(key):
                entry = self.slots[index]
                if entry and entry.key == key:
                    self.slots[index] = Entry(key, value)
                    return

        entry = Entry(key, value)
        snapshot_entries = [existing for existing in self.slots if existing is not None]
        if not self._place_without_resize(entry):
            self._rehash_entries(snapshot_entries + [entry], self.capacity * 2 + 1)

    def remove(self, key: str) -> bool:
        for index in self._positions(key):
            entry = self.slots[index]
            if entry and entry.key == key:
                self.slots[index] = None
                self.size -= 1
                return True
        return False

    def items(self) -> list[tuple[str, str]]:
        pairs = [(entry.key, entry.value) for entry in self.slots if entry is not None]
        return sorted(pairs, key=lambda pair: pair[0])

    def _rebuild(self, entries: list[Entry], new_capacity: int) -> bool:
        old_capacity = self.capacity
        old_slots = self.slots
        old_size = self.size
        old_salt_a = self.salt_a
        old_salt_b = self.salt_b

        self.capacity = max(new_capacity, 3)
        self.slots = [None] * self.capacity
        self.size = 0
        for entry in entries:
            if not self._place_without_resize(entry):
                self.capacity = old_capacity
                self.slots = old_slots
                self.size = old_size
                self.salt_a = old_salt_a
                self.salt_b = old_salt_b
                return False
        return True

    def _rehash_entries(self, entries: list[Entry], new_capacity: int) -> None:
        while True:
            self.rehash_count += 1
            self.salt_a = f"cuckoo-a-r{self.rehash_count}"
            self.salt_b = f"cuckoo-b-r{self.rehash_count}"
            if self._rebuild(entries, new_capacity):
                return
            new_capacity = new_capacity * 2 + 1

    def extend(self, pairs: Iterable[tuple[str, str]]) -> int:
        inserted = 0
        for key, value in pairs:
            existed = key in self
            self.insert(key, value)
            if not existed:
                inserted += 1
        return inserted

    def stats(self) -> dict:
        return {
            "capacity": self.capacity,
            "size": self.size,
            "load_factor": round(self.size / self.capacity, 4),
            "rehash_count": self.rehash_count,
            "displacement_count": self.displacement_count,
            "empty_slots": self.capacity - self.size,
            "max_displacements": self.max_displacements,
        }

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "max_displacements": self.max_displacements,
            "salt_a": self.salt_a,
            "salt_b": self.salt_b,
            "rehash_count": self.rehash_count,
            "displacement_count": self.displacement_count,
            "entries": [entry.to_dict() for entry in self.slots if entry is not None],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CuckooHashTable":
        capacity = data["capacity"]
        if capacity < 3:
            raise ValueError("snapshot capacity must be at least 3")

        table = cls(
            capacity=capacity,
            max_displacements=data.get("max_displacements", 32),
            salt_a=data.get("salt_a", "cuckoo-a"),
            salt_b=data.get("salt_b", "cuckoo-b"),
        )
        table.rehash_count = data.get("rehash_count", 0)
        table.displacement_count = data.get("displacement_count", 0)
        if table.rehash_count < 0 or table.displacement_count < 0:
            raise ValueError("snapshot counters must be non-negative")
        seen_keys: set[str] = set()
        for entry_data in data.get("entries", []):
            entry = Entry.from_dict(entry_data)
            if not entry.key:
                raise ValueError("snapshot contains an empty key")
            if entry.key in seen_keys:
                raise ValueError(f"snapshot contains duplicate key: {entry.key}")
            seen_keys.add(entry.key)
            if not table._place_without_resize(entry):
                raise ValueError("snapshot contains entries that cannot be placed")
        return table


def parse_pair(line: str) -> tuple[str, str]:
    normalized = line.strip()
    if not normalized or normalized.startswith("#"):
        raise ValueError("skip")
    if "," in normalized:
        key, value = normalized.split(",", 1)
    elif "=" in normalized:
        key, value = normalized.split("=", 1)
    else:
        key, value = normalized, normalized
    key = key.strip()
    value = value.strip()
    if not key:
        raise ValueError("key must be non-empty")
    return key, value


def parse_load_factors(raw: str) -> list[float]:
    load_factors = []
    for chunk in raw.split(","):
        value = float(chunk.strip())
        if value <= 0 or value >= 1:
            raise ValueError("load factors must be between 0 and 1")
        load_factors.append(value)
    if not load_factors:
        raise ValueError("at least one load factor is required")
    return load_factors


def load_pairs(path: Path) -> list[tuple[str, str]]:
    pairs = []
    for raw_line in path.read_text().splitlines():
        try:
            pairs.append(parse_pair(raw_line))
        except ValueError as exc:
            if str(exc) == "skip":
                continue
            raise
    return pairs


def save_snapshot(path: Path, table: CuckooHashTable) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(table.to_dict(), indent=2) + "\n")


def load_snapshot(path: Path) -> CuckooHashTable:
    return CuckooHashTable.from_dict(json.loads(path.read_text()))


def run_benchmark(capacity: int, max_displacements: int, load_factors: list[float], trials: int) -> list[dict]:
    if trials < 1:
        raise ValueError("trials must be positive")

    results = []
    for load_factor in load_factors:
        target_size = max(1, min(capacity - 1, int(round(capacity * load_factor))))
        trial_rows = []
        for trial in range(trials):
            table = CuckooHashTable(
                capacity=capacity,
                max_displacements=max_displacements,
                salt_a=f"bench-a-{trial}",
                salt_b=f"bench-b-{trial}",
            )
            started = time.perf_counter()
            for index in range(target_size):
                key = f"trial{trial}-key-{index}"
                table.insert(key, f"value-{index}")
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            stats = table.stats()
            trial_rows.append(
                {
                    "trial": trial,
                    "elapsed_ms": elapsed_ms,
                    "load_factor": stats["load_factor"],
                    "rehash_count": stats["rehash_count"],
                    "displacement_count": stats["displacement_count"],
                    "size": stats["size"],
                    "capacity": stats["capacity"],
                }
            )

        results.append(
            {
                "target_load_factor": round(load_factor, 4),
                "target_size": target_size,
                "trials": trials,
                "average_elapsed_ms": round(sum(row["elapsed_ms"] for row in trial_rows) / trials, 3),
                "average_load_factor": round(sum(row["load_factor"] for row in trial_rows) / trials, 4),
                "average_rehash_count": round(sum(row["rehash_count"] for row in trial_rows) / trials, 3),
                "average_displacement_count": round(sum(row["displacement_count"] for row in trial_rows) / trials, 3),
                "peak_displacement_count": max(row["displacement_count"] for row in trial_rows),
                "final_capacity_range": [min(row["capacity"] for row in trial_rows), max(row["capacity"] for row in trial_rows)],
                "trial_rows": trial_rows,
            }
        )
    return results


def save_benchmark_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_load_factor",
                "target_size",
                "trials",
                "average_elapsed_ms",
                "average_load_factor",
                "average_rehash_count",
                "average_displacement_count",
                "peak_displacement_count",
                "final_capacity_min",
                "final_capacity_max",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "target_load_factor": row["target_load_factor"],
                    "target_size": row["target_size"],
                    "trials": row["trials"],
                    "average_elapsed_ms": row["average_elapsed_ms"],
                    "average_load_factor": row["average_load_factor"],
                    "average_rehash_count": row["average_rehash_count"],
                    "average_displacement_count": row["average_displacement_count"],
                    "peak_displacement_count": row["peak_displacement_count"],
                    "final_capacity_min": row["final_capacity_range"][0],
                    "final_capacity_max": row["final_capacity_range"][1],
                }
            )


def build_command(args: argparse.Namespace) -> int:
    table = CuckooHashTable(capacity=args.capacity, max_displacements=args.max_displacements)
    inserted = table.extend(load_pairs(Path(args.input)))
    if args.output:
        save_snapshot(Path(args.output), table)
    print(json.dumps({"inserted": inserted, "output": args.output, **table.stats()}, indent=2))
    return 0


def stats_command(args: argparse.Namespace) -> int:
    table = load_snapshot(Path(args.snapshot))
    print(json.dumps({**table.stats(), "items": table.items()}, indent=2))
    return 0


def lookup_command(args: argparse.Namespace) -> int:
    table = load_snapshot(Path(args.snapshot))
    value = table.get(args.key)
    print(json.dumps({"key": args.key, "value": value, "found": value is not None}, indent=2))
    return 0


def remove_command(args: argparse.Namespace) -> int:
    table = load_snapshot(Path(args.snapshot))
    removed = table.remove(args.key)
    if args.output:
        save_snapshot(Path(args.output), table)
    print(json.dumps({"key": args.key, "removed": removed, "output": args.output, **table.stats()}, indent=2))
    return 0


def export_command(args: argparse.Namespace) -> int:
    table = load_snapshot(Path(args.snapshot))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(f"{key},{value}" for key, value in table.items()) + "\n")
    print(json.dumps({"output": args.output, "exported": table.size}, indent=2))
    return 0


def benchmark_command(args: argparse.Namespace) -> int:
    results = run_benchmark(
        capacity=args.capacity,
        max_displacements=args.max_displacements,
        load_factors=parse_load_factors(args.load_factors),
        trials=args.trials,
    )
    if args.output:
        save_benchmark_csv(Path(args.output), results)
    print(
        json.dumps(
            {
                "capacity": args.capacity,
                "max_displacements": args.max_displacements,
                "load_factors": [row["target_load_factor"] for row in results],
                "trials": args.trials,
                "output": args.output,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and inspect a portfolio-friendly cuckoo hash table")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a table snapshot from key/value lines")
    build_parser.add_argument("--input", required=True, help="input file with key,value or key=value lines")
    build_parser.add_argument("--output", help="optional snapshot JSON output")
    build_parser.add_argument("--capacity", type=int, default=11, help="starting slot count")
    build_parser.add_argument("--max-displacements", type=int, default=32, help="limit before rehash")
    build_parser.set_defaults(func=build_command)

    stats_parser = subparsers.add_parser("stats", help="inspect a saved snapshot")
    stats_parser.add_argument("--snapshot", required=True, help="saved JSON snapshot")
    stats_parser.set_defaults(func=stats_command)

    lookup_parser = subparsers.add_parser("lookup", help="lookup a key in a saved snapshot")
    lookup_parser.add_argument("--snapshot", required=True, help="saved JSON snapshot")
    lookup_parser.add_argument("key", help="key to search")
    lookup_parser.set_defaults(func=lookup_command)

    remove_parser = subparsers.add_parser("remove", help="remove a key from a saved snapshot")
    remove_parser.add_argument("--snapshot", required=True, help="saved JSON snapshot")
    remove_parser.add_argument("--output", help="optional output path for the updated snapshot")
    remove_parser.add_argument("key", help="key to remove")
    remove_parser.set_defaults(func=remove_command)

    export_parser = subparsers.add_parser("export", help="export sorted table items as key,value text")
    export_parser.add_argument("--snapshot", required=True, help="saved JSON snapshot")
    export_parser.add_argument("--output", required=True, help="destination text file")
    export_parser.set_defaults(func=export_command)

    benchmark_parser = subparsers.add_parser("benchmark", help="benchmark displacement and rehash behavior across load factors")
    benchmark_parser.add_argument("--capacity", type=int, default=101, help="starting slot count for each trial")
    benchmark_parser.add_argument("--max-displacements", type=int, default=32, help="limit before rehash")
    benchmark_parser.add_argument("--load-factors", default="0.25,0.4,0.55,0.7,0.8", help="comma-separated target load factors between 0 and 1")
    benchmark_parser.add_argument("--trials", type=int, default=5, help="number of repeated trials per load factor")
    benchmark_parser.add_argument("--output", help="optional CSV summary path")
    benchmark_parser.set_defaults(func=benchmark_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
