from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
from dataclasses import dataclass
from html import escape
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
    strategy: str
    workload: str
    trial: int
    load_factor: float
    effective_load_factor: float
    entry_count: int
    remaining_entry_count: int
    deleted_entry_count: int
    average_insert_probes: float
    average_delete_probes: float
    average_successful_lookup_probes: float
    average_probe_distance: float
    probe_distance_stddev: float
    max_probe_distance: int
    max_cluster_length: int
    swap_count: int
    probe_distance_histogram: dict[int, int]

    def to_dict(self, capacity: int) -> dict[str, Any]:
        return {
            "capacity": capacity,
            "strategy": self.strategy,
            "workload": self.workload,
            "trial": self.trial,
            "load_factor": round(self.load_factor, 4),
            "effective_load_factor": round(self.effective_load_factor, 4),
            "entry_count": self.entry_count,
            "remaining_entry_count": self.remaining_entry_count,
            "deleted_entry_count": self.deleted_entry_count,
            "average_insert_probes": round(self.average_insert_probes, 4),
            "average_delete_probes": round(self.average_delete_probes, 4),
            "average_successful_lookup_probes": round(self.average_successful_lookup_probes, 4),
            "average_probe_distance": round(self.average_probe_distance, 4),
            "probe_distance_stddev": round(self.probe_distance_stddev, 4),
            "max_probe_distance": self.max_probe_distance,
            "max_cluster_length": self.max_cluster_length,
            "swap_count": self.swap_count,
            "probe_distance_histogram": {
                str(distance): count for distance, count in sorted(self.probe_distance_histogram.items())
            },
        }


STRATEGY_LABELS = {
    "robin-hood": "Robin Hood hashing",
    "linear-probing": "Linear probing",
}

WORKLOAD_LABELS = {
    "fill-only": "Fill-only",
    "delete-heavy": "Delete-heavy",
}


def stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _cluster_lengths(slots: list[Entry | None]) -> list[int]:
    occupied = [slot is not None for slot in slots]
    capacity = len(slots)
    if not any(occupied):
        return []
    if all(occupied):
        return [capacity]
    start = occupied.index(False)
    lengths: list[int] = []
    current = 0
    for offset in range(1, capacity + 1):
        filled = occupied[(start + offset) % capacity]
        if filled:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def _probe_distance_histogram(slots: list[Entry | None]) -> dict[int, int]:
    histogram: dict[int, int] = {}
    for entry in slots:
        if entry is None:
            continue
        histogram[entry.probe_distance] = histogram.get(entry.probe_distance, 0) + 1
    return dict(sorted(histogram.items()))


def _build_stats(*, capacity: int, size: int, max_load_factor: float, auto_resize: bool, slots: list[Entry | None]) -> dict[str, Any]:
    probe_distances = [entry.probe_distance for entry in slots if entry is not None]
    clusters = _cluster_lengths(slots)
    histogram = _probe_distance_histogram(slots)
    return {
        "capacity": capacity,
        "size": size,
        "load_factor": round(size / capacity, 4),
        "max_load_factor": max_load_factor,
        "auto_resize": auto_resize,
        "max_probe_distance": max(probe_distances, default=0),
        "average_probe_distance": round(statistics.fmean(probe_distances), 4) if probe_distances else 0.0,
        "probe_distance_stddev": round(statistics.pstdev(probe_distances), 4) if len(probe_distances) > 1 else 0.0,
        "probe_distance_histogram": histogram,
        "cluster_count": len(clusters),
        "cluster_lengths": clusters,
        "entries": [
            {
                "slot": index,
                "key": entry.key,
                "value": entry.value,
                "home_slot": entry.hash_value % capacity,
                "probe_distance": entry.probe_distance,
            }
            for index, entry in enumerate(slots)
            if entry is not None
        ],
    }


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

    def delete_with_metrics(self, key: str) -> OperationResult:
        hash_value = stable_hash(key)
        index = hash_value % self.capacity
        probe_distance = 0
        probes = 0
        while probe_distance < self.capacity:
            probes += 1
            resident = self.slots[index]
            if resident is None:
                return OperationResult(action="missing", probes=probes)
            if resident.probe_distance < probe_distance:
                return OperationResult(action="missing", probes=probes)
            if resident.key == key:
                self._delete_at_index(index)
                self.size -= 1
                return OperationResult(action="deleted", probes=probes, probe_distance=resident.probe_distance)
            index = (index + 1) % self.capacity
            probe_distance += 1
        return OperationResult(action="missing", probes=probes)

    def delete(self, key: str) -> bool:
        return self.delete_with_metrics(key).action == "deleted"

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
        return _cluster_lengths(self.slots)

    def stats(self) -> dict[str, Any]:
        return _build_stats(
            capacity=self.capacity,
            size=self.size,
            max_load_factor=self.max_load_factor,
            auto_resize=self.auto_resize,
            slots=self.slots,
        )

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


class LinearProbingHashTable:
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
        home_slot = incoming.hash_value % self.capacity
        probes = 0
        for offset in range(self.capacity):
            probes += 1
            index = (home_slot + offset) % self.capacity
            resident = self.slots[index]
            if resident is None:
                incoming.probe_distance = offset
                self.slots[index] = incoming
                self.size += 1
                return OperationResult(action="inserted", probes=probes, probe_distance=offset)
            if resident.key == incoming.key:
                resident.value = incoming.value
                return OperationResult(action="updated", probes=probes, probe_distance=resident.probe_distance)
        raise RuntimeError("hash table is full; choose a larger capacity")

    def get(self, key: str) -> str | None:
        value, _ = self.get_with_metrics(key)
        return value

    def get_with_metrics(self, key: str) -> tuple[str | None, int]:
        hash_value = stable_hash(key)
        home_slot = hash_value % self.capacity
        probes = 0
        for offset in range(self.capacity):
            probes += 1
            resident = self.slots[(home_slot + offset) % self.capacity]
            if resident is None:
                return None, probes
            if resident.key == key:
                return resident.value, probes
        return None, probes

    def delete_with_metrics(self, key: str) -> OperationResult:
        hash_value = stable_hash(key)
        home_slot = hash_value % self.capacity
        probes = 0
        for offset in range(self.capacity):
            probes += 1
            index = (home_slot + offset) % self.capacity
            resident = self.slots[index]
            if resident is None:
                return OperationResult(action="missing", probes=probes)
            if resident.key == key:
                self._delete_at_index(index)
                self.size -= 1
                return OperationResult(action="deleted", probes=probes, probe_distance=resident.probe_distance)
        return OperationResult(action="missing", probes=probes)

    def delete(self, key: str) -> bool:
        return self.delete_with_metrics(key).action == "deleted"

    def _delete_at_index(self, index: int) -> None:
        hole = index
        cursor = (index + 1) % self.capacity
        while True:
            resident = self.slots[cursor]
            if resident is None:
                self.slots[hole] = None
                return
            home_slot = resident.hash_value % self.capacity
            current_distance = (cursor - home_slot) % self.capacity
            hole_distance = (hole - home_slot) % self.capacity
            if hole_distance < current_distance:
                self.slots[hole] = Entry(
                    key=resident.key,
                    value=resident.value,
                    hash_value=resident.hash_value,
                    probe_distance=hole_distance,
                )
                hole = cursor
            cursor = (cursor + 1) % self.capacity

    def cluster_lengths(self) -> list[int]:
        return _cluster_lengths(self.slots)

    def stats(self) -> dict[str, Any]:
        return _build_stats(
            capacity=self.capacity,
            size=self.size,
            max_load_factor=self.max_load_factor,
            auto_resize=self.auto_resize,
            slots=self.slots,
        )


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


def normalize_strategy(raw: str) -> str:
    key = raw.strip().lower().replace("_", "-")
    if key in {"robin", "robinhood", "robin-hood"}:
        return "robin-hood"
    if key in {"linear", "linear-probing", "linearprobing"}:
        return "linear-probing"
    raise InputDataError(f"unknown benchmark strategy: {raw}")


def parse_strategies(raw: str) -> list[str]:
    strategies: list[str] = []
    seen: set[str] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        strategy = normalize_strategy(chunk)
        if strategy in seen:
            continue
        strategies.append(strategy)
        seen.add(strategy)
    if not strategies:
        raise InputDataError("at least one benchmark strategy is required")
    return strategies


def normalize_workload(raw: str) -> str:
    key = raw.strip().lower().replace("_", "-")
    if key in {"fill", "fill-only", "fillonly", "baseline"}:
        return "fill-only"
    if key in {"delete", "delete-heavy", "deleteheavy", "post-delete"}:
        return "delete-heavy"
    raise InputDataError(f"unknown benchmark workload: {raw}")


def parse_workloads(raw: str) -> list[str]:
    workloads: list[str] = []
    seen: set[str] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        workload = normalize_workload(chunk)
        if workload in seen:
            continue
        workloads.append(workload)
        seen.add(workload)
    if not workloads:
        raise InputDataError("at least one benchmark workload is required")
    return workloads


def benchmark_delete_count(entry_count: int, delete_fraction: float) -> int:
    if not 0 < delete_fraction < 1:
        raise InputDataError("delete fraction must be between 0 and 1")
    if entry_count < 2:
        raise InputDataError("delete-heavy workloads require at least 2 entries")
    requested = max(1, int(round(entry_count * delete_fraction)))
    return min(entry_count - 1, requested)


def create_benchmark_table(strategy: str, capacity: int) -> RobinHoodHashTable | LinearProbingHashTable:
    if strategy == "robin-hood":
        return RobinHoodHashTable(capacity=capacity, max_load_factor=0.95, auto_resize=False)
    if strategy == "linear-probing":
        return LinearProbingHashTable(capacity=capacity, max_load_factor=0.95, auto_resize=False)
    raise InputDataError(f"unsupported benchmark strategy: {strategy}")


def run_benchmark(
    *,
    capacity: int,
    load_factors: Iterable[float],
    trials: int,
    seed: int,
    strategies: Iterable[str],
    workloads: Iterable[str],
    delete_fraction: float,
) -> list[BenchmarkRow]:
    if capacity < 3:
        raise InputDataError("benchmark capacity must be at least 3")
    if trials < 1:
        raise InputDataError("trials must be at least 1")
    if not 0 < delete_fraction < 1:
        raise InputDataError("delete fraction must be between 0 and 1")

    strategy_list = list(strategies)
    if not strategy_list:
        raise InputDataError("at least one benchmark strategy is required")
    workload_list = list(workloads)
    if not workload_list:
        raise InputDataError("at least one benchmark workload is required")

    rows: list[BenchmarkRow] = []
    for load_factor in load_factors:
        target_count = max(1, int(round(capacity * load_factor)))
        if target_count >= capacity:
            raise InputDataError("benchmark target entry count must stay below capacity")
        for trial in range(1, trials + 1):
            rng = random.Random(f"robin-hood-benchmark:{capacity}:{load_factor}:{trial}:{seed}")
            keys = [f"key-{trial}-{index}-{rng.randrange(10**9)}" for index in range(target_count)]
            values = [f"value-{rng.randrange(10**9)}" for _ in range(target_count)]
            delete_order = list(keys)
            rng.shuffle(delete_order)
            for strategy in strategy_list:
                for workload in workload_list:
                    table = create_benchmark_table(strategy, capacity)
                    insert_probe_counts: list[int] = []
                    swap_total = 0
                    for key, value in zip(keys, values, strict=True):
                        result = table.put(key, value)
                        insert_probe_counts.append(result.probes)
                        swap_total += result.swaps

                    delete_probe_counts: list[int] = []
                    surviving_keys = list(keys)
                    if workload == "delete-heavy":
                        delete_count = benchmark_delete_count(target_count, delete_fraction)
                        deleted_keys = delete_order[:delete_count]
                        deleted_lookup = set(deleted_keys)
                        surviving_keys = [key for key in keys if key not in deleted_lookup]
                        for key in deleted_keys:
                            result = table.delete_with_metrics(key)
                            if result.action != "deleted":
                                raise RuntimeError(f"failed to delete benchmark key: {key}")
                            delete_probe_counts.append(result.probes)
                    else:
                        delete_count = 0

                    if not surviving_keys:
                        raise RuntimeError("benchmark workload must leave at least one surviving key")

                    lookup_probe_counts = [table.get_with_metrics(key)[1] for key in surviving_keys]
                    stats = table.stats()
                    rows.append(
                        BenchmarkRow(
                            strategy=strategy,
                            workload=workload,
                            trial=trial,
                            load_factor=load_factor,
                            effective_load_factor=round(len(surviving_keys) / capacity, 4),
                            entry_count=target_count,
                            remaining_entry_count=len(surviving_keys),
                            deleted_entry_count=delete_count,
                            average_insert_probes=statistics.fmean(insert_probe_counts),
                            average_delete_probes=statistics.fmean(delete_probe_counts) if delete_probe_counts else 0.0,
                            average_successful_lookup_probes=statistics.fmean(lookup_probe_counts),
                            average_probe_distance=stats["average_probe_distance"],
                            probe_distance_stddev=stats["probe_distance_stddev"],
                            max_probe_distance=stats["max_probe_distance"],
                            max_cluster_length=max(stats["cluster_lengths"], default=0),
                            swap_count=swap_total,
                            probe_distance_histogram=stats["probe_distance_histogram"],
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
                "strategy",
                "workload",
                "trial",
                "load_factor",
                "effective_load_factor",
                "entry_count",
                "remaining_entry_count",
                "deleted_entry_count",
                "average_insert_probes",
                "average_delete_probes",
                "average_successful_lookup_probes",
                "average_probe_distance",
                "probe_distance_stddev",
                "max_probe_distance",
                "max_cluster_length",
                "swap_count",
                "probe_distance_histogram",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in payload:
            writer.writerow(
                {
                    **row,
                    "probe_distance_histogram": json.dumps(row["probe_distance_histogram"]),
                }
            )


def _mean(values: list[int | float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _merge_histogram_counts(histograms: Iterable[dict[int, int]]) -> dict[int, int]:
    merged: dict[int, int] = {}
    for histogram in histograms:
        for distance, count in histogram.items():
            merged[distance] = merged.get(distance, 0) + count
    return dict(sorted(merged.items()))


def _histogram_rows(histogram: dict[int, int]) -> list[dict[str, Any]]:
    total = sum(histogram.values())
    return [
        {
            "distance": distance,
            "count": count,
            "share": round(count / total, 4) if total else 0.0,
        }
        for distance, count in histogram.items()
    ]


def _histogram_stats(histogram: dict[int, int]) -> tuple[float, float]:
    total = sum(histogram.values())
    if total <= 0:
        return 0.0, 0.0
    mean = sum(distance * count for distance, count in histogram.items()) / total
    variance = sum(((distance - mean) ** 2) * count for distance, count in histogram.items()) / total
    return round(mean, 4), round(variance**0.5, 4)


def summarize_benchmark(
    rows: list[BenchmarkRow],
    *,
    capacity: int,
    strategies: list[str],
    workloads: list[str],
    trials: int,
    title: str,
    delete_fraction: float,
) -> dict[str, Any]:
    grouped: dict[tuple[str, float, str], list[BenchmarkRow]] = {}
    for row in rows:
        grouped.setdefault((row.workload, row.load_factor, row.strategy), []).append(row)

    load_factors = sorted({row.load_factor for row in rows})
    results: list[dict[str, Any]] = []
    for workload in workloads:
        for load_factor in load_factors:
            for strategy in strategies:
                bucket = grouped.get((workload, load_factor, strategy), [])
                if not bucket:
                    continue
                merged_histogram = _merge_histogram_counts(row.probe_distance_histogram for row in bucket)
                average_probe_distance, probe_distance_stddev = _histogram_stats(merged_histogram)
                results.append(
                    {
                        "workload": workload,
                        "workload_label": workload_label(workload, delete_fraction=delete_fraction),
                        "load_factor": load_factor,
                        "strategy": strategy,
                        "strategy_label": STRATEGY_LABELS[strategy],
                        "trial_count": len(bucket),
                        "entry_count": bucket[0].entry_count,
                        "remaining_entry_count": bucket[0].remaining_entry_count,
                        "deleted_entry_count": bucket[0].deleted_entry_count,
                        "effective_load_factor": round(_mean([row.effective_load_factor for row in bucket]), 4),
                        "average_insert_probes": round(_mean([row.average_insert_probes for row in bucket]), 4),
                        "average_delete_probes": round(_mean([row.average_delete_probes for row in bucket]), 4),
                        "average_successful_lookup_probes": round(
                            _mean([row.average_successful_lookup_probes for row in bucket]), 4
                        ),
                        "average_probe_distance": average_probe_distance,
                        "probe_distance_stddev": probe_distance_stddev,
                        "max_probe_distance": max(row.max_probe_distance for row in bucket),
                        "max_cluster_length": max(row.max_cluster_length for row in bucket),
                        "average_swap_count": round(_mean([row.swap_count for row in bucket]), 4),
                        "probe_distance_histogram": _histogram_rows(merged_histogram),
                    }
                )

    comparisons: list[dict[str, Any]] = []
    for workload in workloads:
        for load_factor in load_factors:
            robin = next(
                (
                    row
                    for row in results
                    if row["workload"] == workload and row["load_factor"] == load_factor and row["strategy"] == "robin-hood"
                ),
                None,
            )
            linear = next(
                (
                    row
                    for row in results
                    if row["workload"] == workload and row["load_factor"] == load_factor and row["strategy"] == "linear-probing"
                ),
                None,
            )
            if robin and linear:
                lookup_delta = round(linear["average_successful_lookup_probes"] - robin["average_successful_lookup_probes"], 4)
                dispersion_delta = round(linear["probe_distance_stddev"] - robin["probe_distance_stddev"], 4)
                delete_delta = round(linear["average_delete_probes"] - robin["average_delete_probes"], 4)
                if abs(lookup_delta) < 1e-9:
                    lookup_winner = "Tie"
                elif robin["average_successful_lookup_probes"] < linear["average_successful_lookup_probes"]:
                    lookup_winner = robin["strategy_label"]
                else:
                    lookup_winner = linear["strategy_label"]

                if abs(dispersion_delta) < 1e-9:
                    dispersion_winner = "Tie"
                elif robin["probe_distance_stddev"] < linear["probe_distance_stddev"]:
                    dispersion_winner = robin["strategy_label"]
                else:
                    dispersion_winner = linear["strategy_label"]

                if robin["deleted_entry_count"] == 0:
                    delete_winner = "—"
                elif abs(delete_delta) < 1e-9:
                    delete_winner = "Tie"
                elif robin["average_delete_probes"] < linear["average_delete_probes"]:
                    delete_winner = robin["strategy_label"]
                else:
                    delete_winner = linear["strategy_label"]

                comparisons.append(
                    {
                        "workload": workload,
                        "workload_label": workload_label(workload, delete_fraction=delete_fraction),
                        "load_factor": load_factor,
                        "effective_load_factor": robin["effective_load_factor"],
                        "entry_count": robin["entry_count"],
                        "remaining_entry_count": robin["remaining_entry_count"],
                        "deleted_entry_count": robin["deleted_entry_count"],
                        "lookup_delta_vs_linear": lookup_delta,
                        "probe_stddev_delta_vs_linear": dispersion_delta,
                        "delete_delta_vs_linear": delete_delta if robin["deleted_entry_count"] else None,
                        "lookup_winner": lookup_winner,
                        "dispersion_winner": dispersion_winner,
                        "delete_winner": delete_winner,
                    }
                )

    return {
        "title": title,
        "capacity": capacity,
        "trials": trials,
        "strategies": strategies,
        "workloads": workloads,
        "delete_fraction": delete_fraction,
        "load_factors": load_factors,
        "results": results,
        "comparisons": comparisons,
    }


def _format_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    rounded = round(value, 4)
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def _format_percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _markdown_histogram_bar(share: float, *, width: int = 12) -> str:
    units = 0 if share <= 0 else max(1, round(share * width))
    return "█" * units


def _result_lookup(summary: dict[str, Any]) -> dict[tuple[str, float, str], dict[str, Any]]:
    return {(row["workload"], row["load_factor"], row["strategy"]): row for row in summary["results"]}


def workload_label(workload: str, *, delete_fraction: float) -> str:
    base = WORKLOAD_LABELS.get(workload, workload.replace("-", " ").title())
    if workload == "delete-heavy":
        return f"{base} ({_format_percentage(delete_fraction)} removals)"
    return base


def default_benchmark_title(strategies: list[str], workloads: list[str], *, delete_fraction: float) -> str:
    labels = [STRATEGY_LABELS[name] for name in strategies]
    include_delete_heavy = "delete-heavy" in workloads
    if not labels:
        return "Hash-table benchmark summary"
    if len(labels) == 1:
        if include_delete_heavy:
            return f"{labels[0]} fill vs delete-heavy benchmark summary"
        return f"{labels[0]} benchmark summary"
    if strategies == ["robin-hood", "linear-probing"]:
        if include_delete_heavy:
            return "Robin Hood hashing benchmark comparison with delete-heavy workloads"
        return "Robin Hood hashing benchmark comparison"
    if len(labels) == 2:
        suffix = " with delete-heavy workloads" if include_delete_heavy else ""
        return f"{labels[0]} vs {labels[1]} benchmark comparison{suffix}"
    suffix = " with delete-heavy workloads" if include_delete_heavy else ""
    return f"{' vs '.join(labels)} benchmark comparison{suffix}"


def _benchmark_intro(summary: dict[str, Any]) -> str:
    labels = [STRATEGY_LABELS[name] for name in summary["strategies"]]
    include_delete_heavy = "delete-heavy" in summary["workloads"]
    delete_note = ""
    if include_delete_heavy:
        delete_note = (
            f" It also includes a delete-heavy workload that removes {_format_percentage(summary['delete_fraction'])} "
            "of keys before the final lookup + histogram pass, so post-removal clustering is visible too."
        )
    if len(labels) == 1:
        return (
            f"Deterministic benchmark report for {labels[0]}, with probe-distance histograms that make dispersion visible at a glance."
            f"{delete_note}"
        )
    if summary["strategies"] == ["robin-hood", "linear-probing"]:
        return (
            "Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, "
            "with probe-distance histograms that make dispersion visible at a glance."
            f"{delete_note}"
        )
    return (
        f"Deterministic benchmark report comparing {' vs '.join(labels)}, with probe-distance histograms that make dispersion visible at a glance."
        f"{delete_note}"
    )


def render_benchmark_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# {summary['title']}", "", _benchmark_intro(summary), ""]
    strategies = ", ".join(STRATEGY_LABELS[name] for name in summary["strategies"])
    workloads = ", ".join(workload_label(name, delete_fraction=summary["delete_fraction"]) for name in summary["workloads"])
    load_factors = ", ".join(_format_number(value) for value in summary["load_factors"])
    lines.extend(
        [
            f"- Capacity: {summary['capacity']}",
            f"- Trials per workload/load factor: {summary['trials']}",
            f"- Strategies: {strategies}",
            f"- Workloads: {workloads}",
            f"- Requested load factors: {load_factors}",
            "- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.",
            "",
        ]
    )

    if summary["comparisons"]:
        lines.extend(
            [
                "## Headline comparisons",
                "",
                "| Workload | Requested load factor | Remaining load factor | Remaining entries | Lookup winner | Lookup delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |",
                "| --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: |",
            ]
        )
        for row in summary["comparisons"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["workload_label"],
                        _format_number(row["load_factor"]),
                        _format_number(row["effective_load_factor"]),
                        str(row["remaining_entry_count"]),
                        row["lookup_winner"],
                        _format_number(row["lookup_delta_vs_linear"]),
                        row["dispersion_winner"],
                        _format_number(row["probe_stddev_delta_vs_linear"]),
                        row["delete_winner"],
                        "—" if row["delete_delta_vs_linear"] is None else _format_number(row["delete_delta_vs_linear"]),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(
        [
            "## Aggregate metrics",
            "",
            "| Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["results"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["workload_label"],
                    _format_number(row["load_factor"]),
                    _format_number(row["effective_load_factor"]),
                    row["strategy_label"],
                    str(row["deleted_entry_count"]),
                    _format_number(row["average_insert_probes"]),
                    _format_number(row["average_delete_probes"]),
                    _format_number(row["average_successful_lookup_probes"]),
                    _format_number(row["average_probe_distance"]),
                    _format_number(row["probe_distance_stddev"]),
                    str(row["max_probe_distance"]),
                    str(row["max_cluster_length"]),
                    _format_number(row["average_swap_count"]),
                ]
            )
            + " |"
        )
    lines.append("")

    results_by_key = _result_lookup(summary)
    lines.extend(
        [
            "## Probe-distance histograms",
            "",
            "Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; for delete-heavy runs, the histograms are captured after the deterministic removal pass.",
            "",
        ]
    )
    for workload in summary["workloads"]:
        lines.append(f"### {workload_label(workload, delete_fraction=summary['delete_fraction'])}")
        lines.append("")
        for load_factor in summary["load_factors"]:
            present_rows = [
                results_by_key[(workload, load_factor, strategy)]
                for strategy in summary["strategies"]
                if (workload, load_factor, strategy) in results_by_key
            ]
            if not present_rows:
                continue
            distances = sorted(
                {
                    bucket["distance"]
                    for row in present_rows
                    for bucket in row["probe_distance_histogram"]
                }
            )
            lines.extend(
                [
                    f"#### Requested load factor {_format_number(load_factor)} → remaining {_format_number(present_rows[0]['effective_load_factor'])}",
                    "",
                    (
                        f"{present_rows[0]['entry_count']} starting entries per trial; "
                        f"{present_rows[0]['remaining_entry_count']} remain after the workload across {present_rows[0]['trial_count']} deterministic trial(s)."
                    ),
                    "",
                    "| Probe distance | " + " | ".join(row["strategy_label"] for row in present_rows) + " |",
                    "| --- | " + " | ".join(["---"] * len(present_rows)) + " |",
                ]
            )
            for distance in distances:
                cells = []
                for row in present_rows:
                    bucket = next(
                        (item for item in row["probe_distance_histogram"] if item["distance"] == distance),
                        {"count": 0, "share": 0.0},
                    )
                    cell = f"{bucket['count']} ({_format_percentage(bucket['share'])})"
                    bar = _markdown_histogram_bar(bucket["share"])
                    if bar:
                        cell = f"{cell} {bar}"
                    cells.append(cell)
                lines.append("| " + " | ".join([str(distance), *cells]) + " |")
            lines.append("")
    return "\n".join(lines)


def render_benchmark_html(summary: dict[str, Any]) -> str:
    results = summary["results"]
    comparisons = summary["comparisons"]
    results_by_key = _result_lookup(summary)
    max_lookup = max((row["average_successful_lookup_probes"] for row in results), default=1.0)
    max_stddev = max((row["probe_distance_stddev"] for row in results), default=1.0)
    max_cluster = max((row["max_cluster_length"] for row in results), default=1)

    def metric_bar(value: float, maximum: float, accent: str) -> str:
        width = 0.0 if maximum <= 0 else max(0.0, min(100.0, (value / maximum) * 100.0))
        return (
            f'<div class="metric-bar" aria-hidden="true"><span style="width:{width:.1f}%;background:{accent};"></span></div>'
        )

    summary_cards = [
        ("Capacity", str(summary["capacity"]), "slots in each deterministic run"),
        ("Trials", str(summary["trials"]), "repeated runs per workload/load factor"),
        ("Load factors", ", ".join(_format_number(value) for value in summary["load_factors"]), "starting fill levels"),
        (
            "Workloads",
            str(len(summary["workloads"])),
            ", ".join(workload_label(name, delete_fraction=summary["delete_fraction"]) for name in summary["workloads"]),
        ),
        (
            "Strategies",
            str(len(summary["strategies"])),
            ", ".join(STRATEGY_LABELS[name] for name in summary["strategies"]),
        ),
    ]
    summary_cards_html = "".join(
        f'''<article class="summary-card">
  <h2>{escape(label)}</h2>
  <strong>{escape(value)}</strong>
  <p>{escape(detail)}</p>
</article>'''
        for label, value, detail in summary_cards
    )

    comparison_rows_html = "".join(
        f'''<tr>
  <th scope="row">{escape(row['workload_label'])}</th>
  <td>{escape(_format_number(row['load_factor']))}</td>
  <td>{escape(_format_number(row['effective_load_factor']))}</td>
  <td>{row['remaining_entry_count']}</td>
  <td>{escape(row['lookup_winner'])}</td>
  <td>{escape(_format_number(row['lookup_delta_vs_linear']))}</td>
  <td>{escape(row['dispersion_winner'])}</td>
  <td>{escape(_format_number(row['probe_stddev_delta_vs_linear']))}</td>
  <td>{escape(row['delete_winner'])}</td>
  <td>{'—' if row['delete_delta_vs_linear'] is None else escape(_format_number(row['delete_delta_vs_linear']))}</td>
</tr>'''
        for row in comparisons
    )

    aggregate_rows_html = "".join(
        f'''<tr>
  <th scope="row">{escape(row['workload_label'])}</th>
  <td>{escape(_format_number(row['load_factor']))}</td>
  <td>{escape(_format_number(row['effective_load_factor']))}</td>
  <td>{escape(row['strategy_label'])}</td>
  <td>{row['deleted_entry_count']}</td>
  <td>
    <strong>{escape(_format_number(row['average_successful_lookup_probes']))}</strong>
    {metric_bar(row['average_successful_lookup_probes'], max_lookup, '#7c3aed')}
  </td>
  <td>
    <strong>{escape(_format_number(row['probe_distance_stddev']))}</strong>
    {metric_bar(row['probe_distance_stddev'], max_stddev, '#0891b2')}
  </td>
  <td>
    <strong>{row['max_cluster_length']}</strong>
    {metric_bar(float(row['max_cluster_length']), float(max_cluster), '#ea580c')}
  </td>
  <td>{escape(_format_number(row['average_insert_probes']))}</td>
  <td>{escape(_format_number(row['average_delete_probes']))}</td>
  <td>{row['max_probe_distance']}</td>
  <td>{escape(_format_number(row['average_swap_count']))}</td>
</tr>'''
        for row in results
    )

    detail_cards_html = "".join(
        f'''<article class="detail-card">
  <h2>{escape(row['workload_label'])} · start {escape(_format_number(row['load_factor']))} · {escape(row['strategy_label'])}</h2>
  <p>{row['entry_count']} starting entries across {row['trial_count']} deterministic trial(s); {row['remaining_entry_count']} remain after the workload.</p>
  <ul>
    <li>Avg successful lookup probes: <strong>{escape(_format_number(row['average_successful_lookup_probes']))}</strong></li>
    <li>Avg delete probes: <strong>{escape(_format_number(row['average_delete_probes']))}</strong></li>
    <li>Avg probe distance: <strong>{escape(_format_number(row['average_probe_distance']))}</strong></li>
    <li>Probe-distance stddev: <strong>{escape(_format_number(row['probe_distance_stddev']))}</strong></li>
    <li>Max probe distance: <strong>{row['max_probe_distance']}</strong></li>
    <li>Max cluster length: <strong>{row['max_cluster_length']}</strong></li>
    <li>Avg swaps: <strong>{escape(_format_number(row['average_swap_count']))}</strong></li>
  </ul>
</article>'''
        for row in results
    )

    histogram_sections: list[str] = []
    for workload in summary["workloads"]:
        for load_factor in summary["load_factors"]:
            present_rows = [
                results_by_key[(workload, load_factor, strategy)]
                for strategy in summary["strategies"]
                if (workload, load_factor, strategy) in results_by_key
            ]
            if not present_rows:
                continue
            distances = sorted(
                {
                    bucket["distance"]
                    for row in present_rows
                    for bucket in row["probe_distance_histogram"]
                }
            )
            max_share = max(
                (
                    bucket["share"]
                    for row in present_rows
                    for bucket in row["probe_distance_histogram"]
                ),
                default=1.0,
            )
            header_html = "".join(f"<th scope=\"col\">{escape(row['strategy_label'])}</th>" for row in present_rows)
            body_rows: list[str] = []
            for distance in distances:
                cells: list[str] = []
                for row in present_rows:
                    bucket = next(
                        (item for item in row["probe_distance_histogram"] if item["distance"] == distance),
                        {"count": 0, "share": 0.0},
                    )
                    cells.append(
                        f'''<td>
  <strong>{bucket['count']}</strong>
  <span class="histogram-meta">{escape(_format_percentage(bucket['share']))}</span>
  {metric_bar(bucket['share'], max_share, '#2563eb' if row['strategy'] == 'robin-hood' else '#d97706')}
</td>'''
                    )
                body_rows.append(
                    f'''<tr>
  <th scope="row">{distance}</th>
  {"".join(cells)}
</tr>'''
                )
            histogram_sections.append(
                f'''<section class="panel histogram-panel">
  <h2>Probe-distance histogram · {escape(workload_label(workload, delete_fraction=summary['delete_fraction']))} · requested load factor {escape(_format_number(load_factor))}</h2>
  <p>{present_rows[0]['entry_count']} starting entries per trial; {present_rows[0]['remaining_entry_count']} remain after the workload across {present_rows[0]['trial_count']} deterministic trial(s). Watch how much probability mass spills into the longer-distance tail for each strategy.</p>
  <table>
    <caption>Aggregated probe-distance counts by strategy after the workload completes.</caption>
    <thead>
      <tr>
        <th scope="col">Probe distance</th>
        {header_html}
      </tr>
    </thead>
    <tbody>
      {''.join(body_rows)}
    </tbody>
  </table>
</section>'''
            )
    histogram_sections_html = "".join(histogram_sections)

    comparison_table_html = ""
    if comparisons:
        comparison_table_html = f'''<section class="panel">
  <h2>Robin Hood vs linear probing</h2>
  <table>
    <caption>Per-workload winners and deltas against the linear-probing baseline.</caption>
    <thead>
      <tr>
        <th scope="col">Workload</th>
        <th scope="col">Requested load factor</th>
        <th scope="col">Remaining load factor</th>
        <th scope="col">Remaining entries</th>
        <th scope="col">Lookup winner</th>
        <th scope="col">Lookup delta vs linear</th>
        <th scope="col">Lower probe stddev</th>
        <th scope="col">Stddev delta vs linear</th>
        <th scope="col">Lower delete probes</th>
        <th scope="col">Delete delta vs linear</th>
      </tr>
    </thead>
    <tbody>
      {comparison_rows_html}
    </tbody>
  </table>
</section>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(summary['title'])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f8fafc;
      --panel: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #cbd5e1;
      --shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #eef2ff 0%, var(--bg) 22%, var(--bg) 100%);
      color: var(--text);
      font: 16px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }}
    h1, h2 {{ margin: 0 0 0.75rem; line-height: 1.2; }}
    p {{ margin: 0 0 1rem; color: var(--muted); }}
    .hero {{ margin-bottom: 1.5rem; }}
    .grid {{ display: grid; gap: 1rem; }}
    .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); margin: 1.5rem 0; }}
    .detail-grid {{ grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .summary-card, .panel, .detail-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }}
    .summary-card {{ padding: 1rem 1.1rem; }}
    .summary-card strong {{ display: block; font-size: 1.5rem; margin-bottom: 0.35rem; }}
    .panel {{ padding: 1rem 1.1rem; margin: 1rem 0; overflow-x: auto; }}
    .detail-card {{ padding: 1rem 1.1rem; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 860px; }}
    caption {{ text-align: left; font-weight: 600; margin-bottom: 0.7rem; }}
    th, td {{ padding: 0.75rem 0.65rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; text-align: left; }}
    thead th {{ background: #eff6ff; }}
    tbody tr:nth-child(even) {{ background: #f8fafc; }}
    ul {{ margin: 0; padding-left: 1.2rem; }}
    .metric-bar {{ height: 0.45rem; border-radius: 999px; background: #e2e8f0; margin-top: 0.4rem; overflow: hidden; }}
    .metric-bar span {{ display: block; height: 100%; border-radius: inherit; }}
    .histogram-panel td {{ min-width: 180px; }}
    .histogram-meta {{ display: inline-block; margin-left: 0.45rem; color: var(--muted); font-size: 0.95rem; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>{escape(summary['title'])}</h1>
      <p>{escape(_benchmark_intro(summary))}</p>
    </section>
    <section class="grid summary-grid">
      {summary_cards_html}
    </section>
    <p>Requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.</p>
    {comparison_table_html}
    <section class="panel">
      <h2>Aggregate metrics</h2>
      <table>
        <caption>Average metrics aggregated across deterministic trials for each workload, load factor, and strategy.</caption>
        <thead>
          <tr>
            <th scope="col">Workload</th>
            <th scope="col">Requested load factor</th>
            <th scope="col">Remaining load factor</th>
            <th scope="col">Strategy</th>
            <th scope="col">Deleted entries</th>
            <th scope="col">Avg successful lookup probes</th>
            <th scope="col">Probe-distance stddev</th>
            <th scope="col">Max cluster length</th>
            <th scope="col">Avg insert probes</th>
            <th scope="col">Avg delete probes</th>
            <th scope="col">Max probe distance</th>
            <th scope="col">Avg swaps</th>
          </tr>
        </thead>
        <tbody>
          {aggregate_rows_html}
        </tbody>
      </table>
    </section>
    <section>
      <h2>Probe-distance histograms</h2>
      <p>Aggregated histograms keep the report screenshot-friendly while showing how quickly each strategy spills into longer probe chains after fill-only and delete-heavy runs.</p>
      {histogram_sections_html}
    </section>
    <section>
      <h2>Per-slice detail cards</h2>
      <div class="grid detail-grid">
        {detail_cards_html}
      </div>
    </section>
  </main>
</body>
</html>
'''


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

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark probe behavior against a linear-probing baseline")
    benchmark_parser.add_argument("--capacity", type=int, default=127)
    benchmark_parser.add_argument("--load-factors", default="0.25,0.5,0.7,0.85")
    benchmark_parser.add_argument("--trials", type=int, default=5)
    benchmark_parser.add_argument("--seed", type=int, default=17)
    benchmark_parser.add_argument("--strategies", default="robin-hood,linear-probing")
    benchmark_parser.add_argument("--workloads", default="fill-only,delete-heavy")
    benchmark_parser.add_argument("--delete-fraction", type=float, default=0.3)
    benchmark_parser.add_argument("--markdown-out", type=Path, help="optional Markdown benchmark summary output")
    benchmark_parser.add_argument("--html-out", type=Path, help="optional self-contained HTML benchmark dashboard")
    benchmark_parser.add_argument("--title", help="optional benchmark title override")
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
            strategies = parse_strategies(args.strategies)
            workloads = parse_workloads(args.workloads)
            rows = run_benchmark(
                capacity=args.capacity,
                load_factors=parse_load_factors(args.load_factors),
                trials=args.trials,
                seed=args.seed,
                strategies=strategies,
                workloads=workloads,
                delete_fraction=args.delete_fraction,
            )
            save_benchmark(rows, args.output, capacity=args.capacity)
            summary = summarize_benchmark(
                rows,
                capacity=args.capacity,
                strategies=strategies,
                workloads=workloads,
                trials=args.trials,
                title=args.title or default_benchmark_title(strategies, workloads, delete_fraction=args.delete_fraction),
                delete_fraction=args.delete_fraction,
            )
            if args.markdown_out:
                args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
                args.markdown_out.write_text(render_benchmark_markdown(summary) + "\n", encoding="utf-8")
            if args.html_out:
                args.html_out.parent.mkdir(parents=True, exist_ok=True)
                args.html_out.write_text(render_benchmark_html(summary), encoding="utf-8")
            return 0
    except (InputDataError, SnapshotError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
