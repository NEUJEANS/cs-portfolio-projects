from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SnapshotError(ValueError):
    """Raised when a persisted snapshot is malformed."""


class WorkloadError(ValueError):
    """Raised when a workload file is malformed."""


class BenchmarkError(ValueError):
    """Raised when a benchmark suite or comparison run is malformed."""


FNV_OFFSET_BASIS_64 = 14695981039346656037
FNV_PRIME_64 = 1099511628211
CUCKOO_LAB_PATH = Path(__file__).resolve().parents[1] / "cuckoo-hashing-lab" / "cuckoo_hashing_lab.py"
_CUCKOO_HASH_TABLE_CLASS: type[Any] | None = None


@dataclass
class Bucket:
    bucket_id: int
    local_depth: int
    entries: dict[str, str] = field(default_factory=dict)

    def sorted_items(self) -> list[tuple[str, str]]:
        return sorted(self.entries.items())


@dataclass
class WorkloadOpResult:
    step: int
    op: str
    key: str
    value: str | None
    outcome: str
    global_depth: int
    bucket_count: int
    entry_count: int


@dataclass
class WorkloadResult:
    table: "ExtendibleHashTable"
    history: list[WorkloadOpResult]


def stable_hash(value: str) -> int:
    hash_value = FNV_OFFSET_BASIS_64
    for byte in value.encode("utf-8"):
        hash_value ^= byte
        hash_value = (hash_value * FNV_PRIME_64) & 0xFFFFFFFFFFFFFFFF
    return hash_value


def get_cuckoo_hash_table_class() -> type[Any]:
    global _CUCKOO_HASH_TABLE_CLASS
    if _CUCKOO_HASH_TABLE_CLASS is not None:
        return _CUCKOO_HASH_TABLE_CLASS
    if not CUCKOO_LAB_PATH.exists():
        raise BenchmarkError(f"cuckoo hashing lab not found at {CUCKOO_LAB_PATH}")
    spec = importlib.util.spec_from_file_location("extendible_hashing_lab_cuckoo", CUCKOO_LAB_PATH)
    if spec is None or spec.loader is None:
        raise BenchmarkError("failed to load cuckoo hashing lab module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _CUCKOO_HASH_TABLE_CLASS = module.CuckooHashTable
    return _CUCKOO_HASH_TABLE_CLASS


class ExtendibleHashTable:
    def __init__(self, bucket_capacity: int = 2) -> None:
        if bucket_capacity < 1:
            raise ValueError("bucket_capacity must be at least 1")
        self.bucket_capacity = bucket_capacity
        self.global_depth = 0
        self.directory: list[int] = [0]
        self.buckets: dict[int, Bucket] = {0: Bucket(bucket_id=0, local_depth=0)}
        self.next_bucket_id = 1
        self.split_count = 0
        self.merge_count = 0
        self.directory_growth_count = 0
        self.directory_shrink_count = 0

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> "ExtendibleHashTable":
        if not isinstance(payload, dict):
            raise SnapshotError("snapshot must be a JSON object")
        bucket_capacity = payload.get("bucket_capacity")
        global_depth = payload.get("global_depth")
        directory = payload.get("directory")
        buckets_payload = payload.get("buckets")
        next_bucket_id = payload.get("next_bucket_id")
        if not isinstance(bucket_capacity, int) or bucket_capacity < 1:
            raise SnapshotError("snapshot bucket_capacity must be a positive integer")
        if not isinstance(global_depth, int) or global_depth < 0:
            raise SnapshotError("snapshot global_depth must be a non-negative integer")
        if not isinstance(directory, list) or not directory:
            raise SnapshotError("snapshot directory must be a non-empty list")
        if len(directory) != (1 << global_depth):
            raise SnapshotError("directory size must equal 2 ** global_depth")
        if not isinstance(buckets_payload, list) or not buckets_payload:
            raise SnapshotError("snapshot buckets must be a non-empty list")
        if not isinstance(next_bucket_id, int) or next_bucket_id < 1:
            raise SnapshotError("snapshot next_bucket_id must be a positive integer")

        table = cls(bucket_capacity=bucket_capacity)
        table.global_depth = global_depth
        table.directory = []
        table.buckets = {}
        table.next_bucket_id = next_bucket_id

        max_bucket_id = -1
        for item in buckets_payload:
            if not isinstance(item, dict):
                raise SnapshotError("bucket entries must be objects")
            bucket_id = item.get("bucket_id")
            local_depth = item.get("local_depth")
            entries = item.get("entries")
            if not isinstance(bucket_id, int) or bucket_id < 0:
                raise SnapshotError("bucket_id must be a non-negative integer")
            if bucket_id in table.buckets:
                raise SnapshotError(f"duplicate bucket_id {bucket_id}")
            if not isinstance(local_depth, int) or local_depth < 0:
                raise SnapshotError("bucket local_depth must be a non-negative integer")
            if local_depth > global_depth:
                raise SnapshotError("bucket local_depth cannot exceed global_depth")
            if not isinstance(entries, list):
                raise SnapshotError("bucket entries must be a list")
            normalized_entries: dict[str, str] = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    raise SnapshotError("each bucket entry must be an object")
                key = entry.get("key")
                value = entry.get("value")
                if not isinstance(key, str) or not isinstance(value, str):
                    raise SnapshotError("entry key/value must be strings")
                if key in normalized_entries:
                    raise SnapshotError(f"duplicate key {key!r} inside bucket {bucket_id}")
                normalized_entries[key] = value
            if len(normalized_entries) > bucket_capacity:
                raise SnapshotError(f"bucket {bucket_id} exceeds bucket capacity")
            table.buckets[bucket_id] = Bucket(
                bucket_id=bucket_id,
                local_depth=local_depth,
                entries=normalized_entries,
            )
            max_bucket_id = max(max_bucket_id, bucket_id)

        if next_bucket_id <= max_bucket_id:
            raise SnapshotError("snapshot next_bucket_id must be greater than all bucket ids")

        for pointer in directory:
            if not isinstance(pointer, int) or pointer not in table.buckets:
                raise SnapshotError("directory contains an unknown bucket id")
            table.directory.append(pointer)

        for bucket_id, bucket in table.buckets.items():
            bucket_indices = table._bucket_directory_indices(bucket_id)
            expected_aliases = 1 << (global_depth - bucket.local_depth)
            if len(bucket_indices) != expected_aliases:
                raise SnapshotError(
                    f"bucket {bucket_id} should have {expected_aliases} directory aliases but has {len(bucket_indices)}"
                )
            if bucket.local_depth:
                suffix_mask = (1 << bucket.local_depth) - 1
                suffixes = {index & suffix_mask for index in bucket_indices}
                if len(suffixes) != 1:
                    raise SnapshotError(
                        f"bucket {bucket_id} directory aliases do not share a consistent local-depth suffix"
                    )
            for key in bucket.entries:
                directory_bucket_id = table.directory[table._directory_index_for_key(key)]
                if directory_bucket_id != bucket_id:
                    raise SnapshotError(
                        f"key {key!r} is stored in bucket {bucket_id} but routes to bucket {directory_bucket_id}"
                    )

        return table

    def clone(self) -> "ExtendibleHashTable":
        return self.from_snapshot(self.to_snapshot())

    def _directory_mask(self) -> int:
        return (1 << self.global_depth) - 1 if self.global_depth else 0

    def _directory_index_for_key(self, key: str) -> int:
        if self.global_depth == 0:
            return 0
        return stable_hash(key) & self._directory_mask()

    def _get_bucket_for_key(self, key: str) -> Bucket:
        bucket_id = self.directory[self._directory_index_for_key(key)]
        return self.buckets[bucket_id]

    def _bucket_directory_indices(self, bucket_id: int) -> list[int]:
        return [index for index, pointer in enumerate(self.directory) if pointer == bucket_id]

    def _bucket_representative_index(self, bucket_id: int) -> int:
        indices = self._bucket_directory_indices(bucket_id)
        if not indices:
            raise SnapshotError(f"bucket {bucket_id} is not referenced by the directory")
        return min(indices)

    def put(self, key: str, value: str) -> str:
        while True:
            bucket = self._get_bucket_for_key(key)
            if key in bucket.entries:
                bucket.entries[key] = value
                return "updated"
            if len(bucket.entries) < self.bucket_capacity:
                bucket.entries[key] = value
                return "inserted"
            self._split_bucket(bucket.bucket_id)

    def get(self, key: str) -> str | None:
        bucket = self._get_bucket_for_key(key)
        return bucket.entries.get(key)

    def delete(self, key: str) -> bool:
        bucket = self._get_bucket_for_key(key)
        if key not in bucket.entries:
            return False
        del bucket.entries[key]
        self._rebalance_after_delete(bucket.bucket_id)
        return True

    def items(self) -> list[tuple[str, str]]:
        all_items: list[tuple[str, str]] = []
        for bucket in self.buckets.values():
            all_items.extend(bucket.sorted_items())
        return sorted(all_items, key=lambda item: item[0])

    def _split_bucket(self, bucket_id: int) -> None:
        bucket = self.buckets[bucket_id]
        old_local_depth = bucket.local_depth
        if old_local_depth == self.global_depth:
            self.directory.extend(self.directory)
            self.global_depth += 1
            self.directory_growth_count += 1

        bucket.local_depth += 1
        new_bucket = Bucket(bucket_id=self.next_bucket_id, local_depth=bucket.local_depth)
        self.buckets[new_bucket.bucket_id] = new_bucket
        self.next_bucket_id += 1
        self.split_count += 1

        for index, pointer in enumerate(self.directory):
            if pointer != bucket_id:
                continue
            if (index >> old_local_depth) & 1:
                self.directory[index] = new_bucket.bucket_id

        existing_items = list(bucket.entries.items())
        bucket.entries.clear()
        for entry_key, entry_value in existing_items:
            target_bucket = self._get_bucket_for_key(entry_key)
            target_bucket.entries[entry_key] = entry_value

    def _rebalance_after_delete(self, bucket_id: int) -> None:
        current_bucket_id = bucket_id
        while True:
            merged_bucket_id = self._merge_bucket_if_possible(current_bucket_id)
            if merged_bucket_id is None:
                break
            current_bucket_id = merged_bucket_id
        self._shrink_directory()

    def _merge_bucket_if_possible(self, bucket_id: int) -> int | None:
        bucket = self.buckets.get(bucket_id)
        if bucket is None or bucket.local_depth == 0:
            return None

        representative_index = self._bucket_representative_index(bucket_id)
        buddy_index = representative_index ^ (1 << (bucket.local_depth - 1))
        buddy_bucket_id = self.directory[buddy_index]
        if buddy_bucket_id == bucket_id:
            return None

        buddy_bucket = self.buckets[buddy_bucket_id]
        if buddy_bucket.local_depth != bucket.local_depth:
            return None
        if len(bucket.entries) + len(buddy_bucket.entries) > self.bucket_capacity:
            return None

        bucket_rep_index = representative_index
        buddy_rep_index = self._bucket_representative_index(buddy_bucket_id)
        if bucket_rep_index <= buddy_rep_index:
            survivor = bucket
            retired = buddy_bucket
        else:
            survivor = buddy_bucket
            retired = bucket

        merged_entries = dict(survivor.entries)
        merged_entries.update(retired.entries)
        survivor.entries = merged_entries
        survivor.local_depth -= 1

        for index, pointer in enumerate(self.directory):
            if pointer == retired.bucket_id:
                self.directory[index] = survivor.bucket_id

        del self.buckets[retired.bucket_id]
        self.merge_count += 1
        return survivor.bucket_id

    def _shrink_directory(self) -> None:
        while self.global_depth > 0:
            if any(bucket.local_depth == self.global_depth for bucket in self.buckets.values()):
                return
            half = len(self.directory) // 2
            if self.directory[:half] != self.directory[half:]:
                return
            self.directory = self.directory[:half]
            self.global_depth -= 1
            self.directory_shrink_count += 1

    def stats(self) -> dict[str, Any]:
        bucket_aliases: list[dict[str, Any]] = []
        for bucket_id in sorted(self.buckets):
            bucket = self.buckets[bucket_id]
            aliases = sum(1 for pointer in self.directory if pointer == bucket_id)
            bucket_aliases.append(
                {
                    "bucket_id": bucket_id,
                    "local_depth": bucket.local_depth,
                    "aliases": aliases,
                    "size": len(bucket.entries),
                    "keys": [key for key, _ in bucket.sorted_items()],
                }
            )
        entry_count = sum(len(bucket.entries) for bucket in self.buckets.values())
        capacity = self.bucket_capacity * max(len(self.buckets), 1)
        return {
            "bucket_capacity": self.bucket_capacity,
            "global_depth": self.global_depth,
            "directory_slots": len(self.directory),
            "bucket_count": len(self.buckets),
            "entry_count": entry_count,
            "load_factor": round(entry_count / capacity, 4) if capacity else 0.0,
            "buckets": bucket_aliases,
        }

    def directory_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        width = max(self.global_depth, 1)
        for index, bucket_id in enumerate(self.directory):
            bucket = self.buckets[bucket_id]
            rows.append(
                {
                    "index": index,
                    "bits": format(index, f"0{width}b"),
                    "bucket_id": bucket_id,
                    "local_depth": bucket.local_depth,
                    "entries": [f"{key}={value}" for key, value in bucket.sorted_items()],
                }
            )
        return rows

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "bucket_capacity": self.bucket_capacity,
            "global_depth": self.global_depth,
            "next_bucket_id": self.next_bucket_id,
            "directory": list(self.directory),
            "buckets": [
                {
                    "bucket_id": bucket.bucket_id,
                    "local_depth": bucket.local_depth,
                    "entries": [
                        {"key": key, "value": value}
                        for key, value in bucket.sorted_items()
                    ],
                }
                for bucket in sorted(self.buckets.values(), key=lambda item: item.bucket_id)
            ],
        }


def render_markdown_report(title: str, table: ExtendibleHashTable, history: list[WorkloadOpResult] | None = None) -> str:
    stats = table.stats()
    lines = [
        f"# {title}",
        "",
        "## Summary",
        f"- bucket capacity: `{stats['bucket_capacity']}`",
        f"- global depth: `{stats['global_depth']}`",
        f"- directory slots: `{stats['directory_slots']}`",
        f"- bucket count: `{stats['bucket_count']}`",
        f"- entry count: `{stats['entry_count']}`",
        f"- load factor: `{stats['load_factor']}`",
        "",
    ]

    if history:
        lines.extend(
            [
                "## Workload trace",
                "| step | op | key | value | outcome | global depth | bucket count | entry count |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in history:
            lines.append(
                f"| {item.step} | {item.op} | `{item.key}` | `{item.value or ''}` | {item.outcome} | {item.global_depth} | {item.bucket_count} | {item.entry_count} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Directory",
            "| index | bits | bucket | local depth | entries |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in table.directory_rows():
        entries = "<br>".join(row["entries"]) or "_empty_"
        lines.append(
            f"| {row['index']} | `{row['bits']}` | {row['bucket_id']} | {row['local_depth']} | {entries} |"
        )
    lines.append("")
    return "\n".join(lines)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_snapshot(path: Path) -> ExtendibleHashTable:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SnapshotError("snapshot JSON must be an object")
    return ExtendibleHashTable.from_snapshot(payload)


def save_snapshot(path: Path, table: ExtendibleHashTable) -> None:
    save_json(path, table.to_snapshot())


def validate_workload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise WorkloadError("workload must be a JSON object")
    bucket_capacity = payload.get("bucket_capacity", 2)
    operations = payload.get("operations")
    if not isinstance(bucket_capacity, int) or bucket_capacity < 1:
        raise WorkloadError("workload bucket_capacity must be a positive integer")
    if not isinstance(operations, list) or not operations:
        raise WorkloadError("workload operations must be a non-empty list")

    normalized_ops: list[dict[str, str | None]] = []
    for index, item in enumerate(operations, start=1):
        if not isinstance(item, dict):
            raise WorkloadError(f"operation {index} must be an object")
        op = item.get("op")
        key = item.get("key")
        value = item.get("value")
        if op not in {"put", "get", "delete"}:
            raise WorkloadError(f"operation {index} uses unsupported op {op!r}")
        if not isinstance(key, str) or not key:
            raise WorkloadError(f"operation {index} key must be a non-empty string")
        if op == "put" and not isinstance(value, str):
            raise WorkloadError(f"operation {index} put must include a string value")
        if op in {"get", "delete"} and value is not None:
            raise WorkloadError(f"operation {index} should not include a value")
        normalized_ops.append({"op": op, "key": key, "value": value})
    return {"bucket_capacity": bucket_capacity, "operations": normalized_ops}


def run_workload(payload: dict[str, Any]) -> WorkloadResult:
    workload = validate_workload(payload)
    table = ExtendibleHashTable(bucket_capacity=workload["bucket_capacity"])
    history: list[WorkloadOpResult] = []
    for step, operation in enumerate(workload["operations"], start=1):
        op = operation["op"]
        key = operation["key"]
        value = operation["value"]
        if op == "put":
            assert value is not None
            outcome = table.put(key, value)
        elif op == "get":
            result = table.get(key)
            outcome = f"found:{result}" if result is not None else "missing"
        else:
            outcome = "deleted" if table.delete(key) else "missing"
        history.append(
            WorkloadOpResult(
                step=step,
                op=op,
                key=key,
                value=value,
                outcome=outcome,
                global_depth=table.global_depth,
                bucket_count=len(table.buckets),
                entry_count=sum(len(bucket.entries) for bucket in table.buckets.values()),
            )
        )
    return WorkloadResult(table=table, history=history)


def validate_benchmark_suite(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise BenchmarkError("benchmark suite must be a JSON object")
    bucket_capacity = payload.get("bucket_capacity", 2)
    cuckoo_capacity = payload.get("cuckoo_capacity", 11)
    max_displacements = payload.get("max_displacements", 16)
    trials = payload.get("trials", 3)
    scenarios = payload.get("scenarios")
    title = payload.get("title", "Extendible hashing benchmark suite")

    if not isinstance(title, str) or not title.strip():
        raise BenchmarkError("benchmark title must be a non-empty string")
    if not isinstance(bucket_capacity, int) or bucket_capacity < 1:
        raise BenchmarkError("benchmark bucket_capacity must be a positive integer")
    if not isinstance(cuckoo_capacity, int) or cuckoo_capacity < 3:
        raise BenchmarkError("benchmark cuckoo_capacity must be an integer >= 3")
    if not isinstance(max_displacements, int) or max_displacements < 1:
        raise BenchmarkError("benchmark max_displacements must be a positive integer")
    if not isinstance(trials, int) or trials < 1:
        raise BenchmarkError("benchmark trials must be a positive integer")
    if not isinstance(scenarios, list) or not scenarios:
        raise BenchmarkError("benchmark scenarios must be a non-empty list")

    normalized_scenarios: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise BenchmarkError(f"scenario {index} must be an object")
        name = scenario.get("name")
        description = scenario.get("description", "")
        if not isinstance(name, str) or not name.strip():
            raise BenchmarkError(f"scenario {index} name must be a non-empty string")
        if name in seen_names:
            raise BenchmarkError(f"duplicate scenario name {name!r}")
        seen_names.add(name)
        if not isinstance(description, str):
            raise BenchmarkError(f"scenario {name!r} description must be a string")
        workload = validate_workload(
            {
                "bucket_capacity": bucket_capacity,
                "operations": scenario.get("operations"),
            }
        )
        normalized_scenarios.append(
            {
                "name": name,
                "description": description,
                "operations": workload["operations"],
            }
        )

    return {
        "title": title.strip(),
        "bucket_capacity": bucket_capacity,
        "cuckoo_capacity": cuckoo_capacity,
        "max_displacements": max_displacements,
        "trials": trials,
        "scenarios": normalized_scenarios,
    }


def _record_operation_mix_counts(operation_mix: dict[str, int], op: str, outcome: str) -> None:
    if op == "put":
        operation_mix["puts"] += 1
        if outcome == "inserted":
            operation_mix["insertions"] += 1
        else:
            operation_mix["updates"] += 1
        return
    if op == "get":
        operation_mix["gets"] += 1
        if outcome.startswith("found:"):
            operation_mix["get_hits"] += 1
        else:
            operation_mix["get_misses"] += 1
        return
    operation_mix["deletes"] += 1
    if outcome == "deleted":
        operation_mix["delete_hits"] += 1
    else:
        operation_mix["delete_misses"] += 1


def _run_benchmark_trial(
    scenario: dict[str, Any],
    bucket_capacity: int,
    cuckoo_capacity: int,
    max_displacements: int,
    trial: int,
) -> dict[str, Any]:
    extendible = ExtendibleHashTable(bucket_capacity=bucket_capacity)
    cuckoo_class = get_cuckoo_hash_table_class()
    cuckoo = cuckoo_class(
        capacity=cuckoo_capacity,
        max_displacements=max_displacements,
        salt_a=f"extendible-benchmark-a-{scenario['name']}-{trial}",
        salt_b=f"extendible-benchmark-b-{scenario['name']}-{trial}",
    )

    operation_mix = {
        "puts": 0,
        "insertions": 0,
        "updates": 0,
        "gets": 0,
        "get_hits": 0,
        "get_misses": 0,
        "deletes": 0,
        "delete_hits": 0,
        "delete_misses": 0,
    }
    reference: dict[str, str] = {}
    peak_global_depth = extendible.global_depth
    peak_bucket_count = len(extendible.buckets)
    peak_directory_slots = len(extendible.directory)

    for operation in scenario["operations"]:
        op = operation["op"]
        key = operation["key"]
        value = operation["value"]

        if op == "put":
            assert value is not None
            expected_outcome = "updated" if key in reference else "inserted"
            reference[key] = value
            extendible_outcome = extendible.put(key, value)
            if extendible_outcome != expected_outcome:
                raise BenchmarkError(
                    f"extendible hashing returned {extendible_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            cuckoo_existing = cuckoo.get(key)
            cuckoo.insert(key, value)
            cuckoo_outcome = "updated" if cuckoo_existing is not None else "inserted"
            if cuckoo_outcome != expected_outcome:
                raise BenchmarkError(
                    f"cuckoo hashing returned {cuckoo_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            outcome = expected_outcome
        elif op == "get":
            expected_value = reference.get(key)
            extendible_value = extendible.get(key)
            cuckoo_value = cuckoo.get(key)
            if extendible_value != expected_value:
                raise BenchmarkError(
                    f"extendible hashing lookup for {key!r} returned {extendible_value!r}; expected {expected_value!r}"
                )
            if cuckoo_value != expected_value:
                raise BenchmarkError(
                    f"cuckoo hashing lookup for {key!r} returned {cuckoo_value!r}; expected {expected_value!r}"
                )
            outcome = f"found:{expected_value}" if expected_value is not None else "missing"
        else:
            expected_removed = key in reference
            if expected_removed:
                del reference[key]
            extendible_removed = extendible.delete(key)
            cuckoo_removed = cuckoo.remove(key)
            if extendible_removed != expected_removed:
                raise BenchmarkError(
                    f"extendible hashing delete for {key!r} returned {extendible_removed}; expected {expected_removed}"
                )
            if cuckoo_removed != expected_removed:
                raise BenchmarkError(
                    f"cuckoo hashing delete for {key!r} returned {cuckoo_removed}; expected {expected_removed}"
                )
            outcome = "deleted" if expected_removed else "missing"

        _record_operation_mix_counts(operation_mix, op, outcome)
        peak_global_depth = max(peak_global_depth, extendible.global_depth)
        peak_bucket_count = max(peak_bucket_count, len(extendible.buckets))
        peak_directory_slots = max(peak_directory_slots, len(extendible.directory))

    expected_items = sorted(reference.items(), key=lambda item: item[0])
    extendible_items = extendible.items()
    cuckoo_items = cuckoo.items()
    if extendible_items != expected_items:
        raise BenchmarkError(
            f"extendible hashing final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )
    if cuckoo_items != expected_items:
        raise BenchmarkError(
            f"cuckoo hashing final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )

    extendible_stats = extendible.stats()
    cuckoo_stats = cuckoo.stats()
    return {
        "trial": trial,
        "operation_mix": operation_mix,
        "final_entry_count": len(expected_items),
        "extendible": {
            "final_global_depth": extendible.global_depth,
            "peak_global_depth": peak_global_depth,
            "final_bucket_count": len(extendible.buckets),
            "peak_bucket_count": peak_bucket_count,
            "peak_directory_slots": peak_directory_slots,
            "load_factor": extendible_stats["load_factor"],
            "split_count": extendible.split_count,
            "merge_count": extendible.merge_count,
            "directory_growth_count": extendible.directory_growth_count,
            "directory_shrink_count": extendible.directory_shrink_count,
        },
        "cuckoo": {
            "final_capacity": cuckoo_stats["capacity"],
            "load_factor": cuckoo_stats["load_factor"],
            "rehash_count": cuckoo_stats["rehash_count"],
            "displacement_count": cuckoo_stats["displacement_count"],
            "empty_slots": cuckoo_stats["empty_slots"],
        },
    }


def _average(values: list[int | float], digits: int = 3) -> float:
    return round(sum(values) / len(values), digits)


def summarize_benchmark_trials(scenario: dict[str, Any], trial_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not trial_rows:
        raise BenchmarkError(f"scenario {scenario['name']!r} produced no trial rows")
    first_row = trial_rows[0]

    operation_mix_signatures = {tuple(sorted(row["operation_mix"].items())) for row in trial_rows}
    if len(operation_mix_signatures) != 1:
        raise BenchmarkError(
            f"scenario {scenario['name']!r} produced inconsistent operation counts across trials"
        )

    final_entry_counts = {row["final_entry_count"] for row in trial_rows}
    if len(final_entry_counts) != 1:
        raise BenchmarkError(
            f"scenario {scenario['name']!r} produced inconsistent final entry counts across trials"
        )

    extendible_signatures = {
        json.dumps(row["extendible"], sort_keys=True)
        for row in trial_rows
    }
    if len(extendible_signatures) != 1:
        raise BenchmarkError(
            f"scenario {scenario['name']!r} produced inconsistent extendible-hashing metrics across trials"
        )

    return {
        "name": scenario["name"],
        "description": scenario["description"],
        "operation_count": len(scenario["operations"]),
        "final_entry_count": first_row["final_entry_count"],
        "operation_mix": dict(first_row["operation_mix"]),
        "validation": {
            "trials": len(trial_rows),
            "final_state_match": True,
        },
        "extendible": dict(first_row["extendible"]),
        "cuckoo": {
            "average_rehash_count": _average([row["cuckoo"]["rehash_count"] for row in trial_rows], digits=3),
            "average_displacement_count": _average(
                [row["cuckoo"]["displacement_count"] for row in trial_rows],
                digits=3,
            ),
            "average_load_factor": _average([row["cuckoo"]["load_factor"] for row in trial_rows], digits=4),
            "final_capacity_range": [
                min(row["cuckoo"]["final_capacity"] for row in trial_rows),
                max(row["cuckoo"]["final_capacity"] for row in trial_rows),
            ],
            "empty_slot_range": [
                min(row["cuckoo"]["empty_slots"] for row in trial_rows),
                max(row["cuckoo"]["empty_slots"] for row in trial_rows),
            ],
        },
        "trial_rows": trial_rows,
    }


def run_benchmark_suite(payload: dict[str, Any]) -> dict[str, Any]:
    suite = validate_benchmark_suite(payload)
    results: list[dict[str, Any]] = []
    for scenario in suite["scenarios"]:
        trial_rows = [
            _run_benchmark_trial(
                scenario=scenario,
                bucket_capacity=suite["bucket_capacity"],
                cuckoo_capacity=suite["cuckoo_capacity"],
                max_displacements=suite["max_displacements"],
                trial=trial,
            )
            for trial in range(1, suite["trials"] + 1)
        ]
        results.append(summarize_benchmark_trials(scenario, trial_rows))
    return {
        "title": suite["title"],
        "bucket_capacity": suite["bucket_capacity"],
        "cuckoo_capacity": suite["cuckoo_capacity"],
        "max_displacements": suite["max_displacements"],
        "trials": suite["trials"],
        "scenario_count": len(suite["scenarios"]),
        "results": results,
    }


def render_benchmark_markdown_report(title: str, summary: dict[str, Any], suite_source: str | None = None) -> str:
    lines = [
        f"# {title}",
        "",
    ]
    if suite_source:
        lines.append(f"- Suite source: `{suite_source}`")
    lines.extend(
        [
            f"- Scenario count: `{summary['scenario_count']}`",
            f"- Extendible bucket capacity: `{summary['bucket_capacity']}`",
            f"- Cuckoo starting capacity: `{summary['cuckoo_capacity']}`",
            f"- Cuckoo max displacements: `{summary['max_displacements']}`",
            f"- Trials per scenario: `{summary['trials']}`",
            "",
            "## Scenario scoreboard",
            "| Scenario | Ops | Final entries | Ext splits | Ext merges | Dir grows | Dir shrinks | Peak depth | Peak buckets | Cuckoo avg rehashes | Cuckoo avg displacements | Cuckoo capacity range |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary["results"]:
        lines.append(
            "| {name} | {ops} | {entries} | {splits} | {merges} | {dir_grows} | {dir_shrinks} | {peak_depth} | {peak_buckets} | {rehashes} | {displacements} | `{capacity_min}-{capacity_max}` |".format(
                name=row["name"],
                ops=row["operation_count"],
                entries=row["final_entry_count"],
                splits=row["extendible"]["split_count"],
                merges=row["extendible"]["merge_count"],
                dir_grows=row["extendible"]["directory_growth_count"],
                dir_shrinks=row["extendible"]["directory_shrink_count"],
                peak_depth=row["extendible"]["peak_global_depth"],
                peak_buckets=row["extendible"]["peak_bucket_count"],
                rehashes=row["cuckoo"]["average_rehash_count"],
                displacements=row["cuckoo"]["average_displacement_count"],
                capacity_min=row["cuckoo"]["final_capacity_range"][0],
                capacity_max=row["cuckoo"]["final_capacity_range"][1],
            )
        )
    lines.append("")

    for row in summary["results"]:
        lines.extend(
            [
                f"## Scenario — {row['name']}",
                "",
                f"- Description: {row['description'] or 'No description provided.'}",
                f"- Operation mix: `puts={row['operation_mix']['puts']}` (`insertions={row['operation_mix']['insertions']}`, `updates={row['operation_mix']['updates']}`), `gets={row['operation_mix']['gets']}` (`hits={row['operation_mix']['get_hits']}`, `misses={row['operation_mix']['get_misses']}`), `deletes={row['operation_mix']['deletes']}` (`hits={row['operation_mix']['delete_hits']}`, `misses={row['operation_mix']['delete_misses']}`)",
                f"- Extendible hashing finished at global depth `{row['extendible']['final_global_depth']}` with `{row['extendible']['final_bucket_count']}` buckets and load factor `{row['extendible']['load_factor']}` after `{row['extendible']['split_count']}` splits / `{row['extendible']['merge_count']}` merges and `{row['extendible']['directory_growth_count']}` directory growth(s) / `{row['extendible']['directory_shrink_count']}` directory shrink(s).",
                f"- Cuckoo hashing averaged `{row['cuckoo']['average_rehash_count']}` rehashes and `{row['cuckoo']['average_displacement_count']}` displacements, finishing between capacities `{row['cuckoo']['final_capacity_range'][0]}` and `{row['cuckoo']['final_capacity_range'][1]}`.",
                f"- Validation: final states matched across `{row['validation']['trials']}` deterministic trial(s).",
                "",
                "| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for trial_row in row["trial_rows"]:
            lines.append(
                f"| {trial_row['trial']} | {trial_row['extendible']['split_count']} | {trial_row['extendible']['merge_count']} | {trial_row['extendible']['peak_global_depth']} | {trial_row['extendible']['peak_bucket_count']} | {trial_row['extendible']['peak_directory_slots']} | {trial_row['cuckoo']['rehash_count']} | {trial_row['cuckoo']['displacement_count']} | {trial_row['cuckoo']['final_capacity']} |"
            )
        lines.append("")

    return "\n".join(lines)


def save_benchmark_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario",
                "operation_count",
                "final_entry_count",
                "puts",
                "insertions",
                "updates",
                "gets",
                "get_hits",
                "get_misses",
                "deletes",
                "delete_hits",
                "delete_misses",
                "extendible_split_count",
                "extendible_merge_count",
                "extendible_directory_growth_count",
                "extendible_directory_shrink_count",
                "extendible_final_global_depth",
                "extendible_peak_global_depth",
                "extendible_final_bucket_count",
                "extendible_peak_bucket_count",
                "extendible_peak_directory_slots",
                "extendible_load_factor",
                "cuckoo_average_rehash_count",
                "cuckoo_average_displacement_count",
                "cuckoo_average_load_factor",
                "cuckoo_final_capacity_min",
                "cuckoo_final_capacity_max",
                "cuckoo_empty_slots_min",
                "cuckoo_empty_slots_max",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "scenario": row["name"],
                    "operation_count": row["operation_count"],
                    "final_entry_count": row["final_entry_count"],
                    "puts": row["operation_mix"]["puts"],
                    "insertions": row["operation_mix"]["insertions"],
                    "updates": row["operation_mix"]["updates"],
                    "gets": row["operation_mix"]["gets"],
                    "get_hits": row["operation_mix"]["get_hits"],
                    "get_misses": row["operation_mix"]["get_misses"],
                    "deletes": row["operation_mix"]["deletes"],
                    "delete_hits": row["operation_mix"]["delete_hits"],
                    "delete_misses": row["operation_mix"]["delete_misses"],
                    "extendible_split_count": row["extendible"]["split_count"],
                    "extendible_merge_count": row["extendible"]["merge_count"],
                    "extendible_directory_growth_count": row["extendible"]["directory_growth_count"],
                    "extendible_directory_shrink_count": row["extendible"]["directory_shrink_count"],
                    "extendible_final_global_depth": row["extendible"]["final_global_depth"],
                    "extendible_peak_global_depth": row["extendible"]["peak_global_depth"],
                    "extendible_final_bucket_count": row["extendible"]["final_bucket_count"],
                    "extendible_peak_bucket_count": row["extendible"]["peak_bucket_count"],
                    "extendible_peak_directory_slots": row["extendible"]["peak_directory_slots"],
                    "extendible_load_factor": row["extendible"]["load_factor"],
                    "cuckoo_average_rehash_count": row["cuckoo"]["average_rehash_count"],
                    "cuckoo_average_displacement_count": row["cuckoo"]["average_displacement_count"],
                    "cuckoo_average_load_factor": row["cuckoo"]["average_load_factor"],
                    "cuckoo_final_capacity_min": row["cuckoo"]["final_capacity_range"][0],
                    "cuckoo_final_capacity_max": row["cuckoo"]["final_capacity_range"][1],
                    "cuckoo_empty_slots_min": row["cuckoo"]["empty_slot_range"][0],
                    "cuckoo_empty_slots_max": row["cuckoo"]["empty_slot_range"][1],
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extendible hashing lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a workload from scratch")
    run_parser.add_argument("--input", required=True, type=Path, help="workload JSON file")
    run_parser.add_argument("--output", required=True, type=Path, help="where to write the snapshot JSON")
    run_parser.add_argument("--report", type=Path, help="optional markdown report output")
    run_parser.add_argument(
        "--title",
        default="Extendible hashing workload report",
        help="title to use if --report is enabled",
    )

    inspect_parser = subparsers.add_parser("inspect", help="inspect a snapshot")
    inspect_parser.add_argument("--snapshot", required=True, type=Path)
    inspect_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="output format",
    )

    lookup_parser = subparsers.add_parser("lookup", help="lookup a key in a snapshot")
    lookup_parser.add_argument("--snapshot", required=True, type=Path)
    lookup_parser.add_argument("key")

    delete_parser = subparsers.add_parser("delete", help="delete a key from a snapshot")
    delete_parser.add_argument("--snapshot", required=True, type=Path)
    delete_parser.add_argument("--output", required=True, type=Path)
    delete_parser.add_argument("key")

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare extendible hashing against the repo's cuckoo hashing lab across mixed workloads",
    )
    benchmark_parser.add_argument("--input", required=True, type=Path, help="benchmark suite JSON file")
    benchmark_parser.add_argument("--json-out", type=Path, help="optional JSON summary output")
    benchmark_parser.add_argument("--markdown-out", type=Path, help="optional Markdown report output")
    benchmark_parser.add_argument("--csv-out", type=Path, help="optional CSV summary output")
    benchmark_parser.add_argument(
        "--title",
        default="Extendible hashing benchmark comparison",
        help="report title to use for --markdown-out",
    )

    return parser


def command_run(args: argparse.Namespace) -> int:
    workload = load_json(args.input)
    result = run_workload(workload)
    save_snapshot(args.output, result.table)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            render_markdown_report(args.title, result.table, result.history) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result.table.stats(), indent=2))
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    table = load_snapshot(args.snapshot)
    if args.format == "markdown":
        print(render_markdown_report("Extendible hashing snapshot", table))
    else:
        print(json.dumps(table.to_snapshot(), indent=2))
    return 0


def command_lookup(args: argparse.Namespace) -> int:
    table = load_snapshot(args.snapshot)
    value = table.get(args.key)
    if value is None:
        print(f"{args.key}: NOT_FOUND")
        return 1
    print(f"{args.key}: {value}")
    return 0


def command_delete(args: argparse.Namespace) -> int:
    table = load_snapshot(args.snapshot)
    removed = table.delete(args.key)
    save_snapshot(args.output, table)
    print(f"{args.key}: {'deleted' if removed else 'missing'}")
    return 0 if removed else 1


def command_benchmark(args: argparse.Namespace) -> int:
    suite = load_json(args.input)
    summary = run_benchmark_suite(suite)
    if args.json_out:
        save_json(args.json_out, summary)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(
            render_benchmark_markdown_report(args.title, summary, suite_source=str(args.input)) + "\n",
            encoding="utf-8",
        )
    if args.csv_out:
        save_benchmark_csv(args.csv_out, summary["results"])
    print(json.dumps({"input": str(args.input), **summary}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return command_run(args)
    if args.command == "inspect":
        return command_inspect(args)
    if args.command == "lookup":
        return command_lookup(args)
    if args.command == "delete":
        return command_delete(args)
    if args.command == "benchmark":
        return command_benchmark(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
