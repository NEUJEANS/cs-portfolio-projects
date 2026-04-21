from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
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
BTREE_BENCHMARK_KEY_MASK = 0x7FFFFFFFFFFFFFFF
CUCKOO_LAB_PATH = Path(__file__).resolve().parents[1] / "cuckoo-hashing-lab" / "cuckoo_hashing_lab.py"
B_TREE_LAB_PATH = Path(__file__).resolve().parents[1] / "b-tree-index-lab" / "btree_index.py"
_CUCKOO_HASH_TABLE_CLASS: type[Any] | None = None
_BTREE_INDEX_CLASS: type[Any] | None = None


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
    split_delta: int = 0
    merge_delta: int = 0
    directory_growth_delta: int = 0
    directory_shrink_delta: int = 0
    snapshot: dict[str, Any] | None = None


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


def get_btree_index_class() -> type[Any]:
    global _BTREE_INDEX_CLASS
    if _BTREE_INDEX_CLASS is not None:
        return _BTREE_INDEX_CLASS
    if not B_TREE_LAB_PATH.exists():
        raise BenchmarkError(f"B-tree index lab not found at {B_TREE_LAB_PATH}")
    spec = importlib.util.spec_from_file_location("extendible_hashing_lab_btree", B_TREE_LAB_PATH)
    if spec is None or spec.loader is None:
        raise BenchmarkError("failed to load B-tree index lab module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _BTREE_INDEX_CLASS = module.BTreeIndex
    return _BTREE_INDEX_CLASS


def benchmark_btree_key(key: str) -> int:
    return stable_hash(f"btree-benchmark::{key}") & BTREE_BENCHMARK_KEY_MASK


@dataclass
class LinearProbingEntry:
    key: str
    value: str


class _LinearTombstone:
    pass


LINEAR_TOMBSTONE = _LinearTombstone()
LINEAR_PROBING_THEORY_FORMULA = "successful ≈ 0.5 * (1 + 1 / (1 - α)); unsuccessful ≈ 0.5 * (1 + 1 / (1 - α)^2)"
LINEAR_PROBING_THEORY_REFERENCE_BASIS = (
    "Use the average occupied load factor α across benchmark steps as the compact baseline; "
    "final and peak occupied load factors are included for context."
)


def _empty_probe_summary() -> dict[str, Any]:
    return {
        "count": 0,
        "average_probe_count": 0.0,
        "max_probe_count": 0,
        "p50_probe_count": 0,
        "p95_probe_count": 0,
    }


def summarize_probe_samples(probes: list[int]) -> dict[str, Any]:
    if not probes:
        return _empty_probe_summary()
    ordered = sorted(probes)

    def percentile(percent: int) -> int:
        rank = max(0, math.ceil((percent / 100) * len(ordered)) - 1)
        return ordered[min(rank, len(ordered) - 1)]

    return {
        "count": len(ordered),
        "average_probe_count": round(sum(ordered) / len(ordered), 3),
        "max_probe_count": ordered[-1],
        "p50_probe_count": percentile(50),
        "p95_probe_count": percentile(95),
    }


class LinearProbingHashTable:
    def __init__(
        self,
        capacity: int = 8,
        max_load_factor: float = 0.75,
        max_tombstone_ratio: float = 0.25,
    ) -> None:
        if capacity < 4:
            raise ValueError("capacity must be at least 4")
        if not 0 < float(max_load_factor) < 1:
            raise ValueError("max_load_factor must be between 0 and 1")
        if not 0 <= float(max_tombstone_ratio) < 1:
            raise ValueError("max_tombstone_ratio must be between 0 and 1")
        self.initial_capacity = capacity
        self.capacity = capacity
        self.max_load_factor = float(max_load_factor)
        self.max_tombstone_ratio = float(max_tombstone_ratio)
        self.slots: list[LinearProbingEntry | _LinearTombstone | None] = [None] * capacity
        self.size = 0
        self.tombstones = 0
        self.resize_count = 0
        self.total_probe_count = 0
        self.max_probe_count = 0
        self.operation_count = 0
        self.rebuild_probe_count = 0
        self.probe_samples_by_kind: dict[str, list[int]] = {
            "put_inserted": [],
            "put_updated": [],
            "get_hit": [],
            "get_miss": [],
            "delete_hit": [],
            "delete_miss": [],
        }

    def _hash(self, key: str) -> int:
        return stable_hash(f"linear-probing::{key}") % self.capacity

    def _record_probes(self, probes: int, kind: str) -> None:
        self.total_probe_count += probes
        self.operation_count += 1
        self.max_probe_count = max(self.max_probe_count, probes)
        self.probe_samples_by_kind[kind].append(probes)

    def _should_grow_for_insert(self) -> bool:
        return ((self.size + 1) / self.capacity) > self.max_load_factor or (self.size + self.tombstones) >= self.capacity

    def _should_rebuild_for_tombstones(self) -> bool:
        if self.capacity == 0:
            return False
        return self.tombstones > 0 and (self.tombstones / self.capacity) > self.max_tombstone_ratio

    def _locate_slot(self, key: str) -> tuple[int | None, int | None, int]:
        first_tombstone: int | None = None
        start = self._hash(key)
        for probe in range(self.capacity):
            index = (start + probe) % self.capacity
            slot = self.slots[index]
            if slot is None:
                return None, first_tombstone if first_tombstone is not None else index, probe + 1
            if slot is LINEAR_TOMBSTONE:
                if first_tombstone is None:
                    first_tombstone = index
                continue
            if slot.key == key:
                return index, index, probe + 1
        return None, first_tombstone, self.capacity

    def _live_entries(self) -> list[LinearProbingEntry]:
        return [
            LinearProbingEntry(slot.key, slot.value)
            for slot in self.slots
            if isinstance(slot, LinearProbingEntry)
        ]

    def _resize(self, new_capacity: int) -> None:
        target_capacity = max(int(new_capacity), self.initial_capacity, 4)
        entries = self._live_entries()
        self.resize_count += 1
        self.capacity = target_capacity
        self.slots = [None] * target_capacity
        self.size = 0
        self.tombstones = 0
        probes_spent = 0
        for entry in entries:
            _, insert_index, probes = self._locate_slot(entry.key)
            if insert_index is None:
                raise BenchmarkError("linear probing resize failed to find an insertion slot")
            self.slots[insert_index] = LinearProbingEntry(entry.key, entry.value)
            self.size += 1
            probes_spent += probes
        self.rebuild_probe_count += probes_spent

    def put(self, key: str, value: str) -> str:
        found_index, insert_index, probes = self._locate_slot(key)
        if found_index is not None:
            self._record_probes(probes, "put_updated")
            self.slots[found_index] = LinearProbingEntry(key, value)
            return "updated"

        if insert_index is None or self._should_grow_for_insert() or self._should_rebuild_for_tombstones():
            self._resize(self.capacity * 2 if insert_index is None or self._should_grow_for_insert() else self.capacity)
            _, insert_index, resize_probes = self._locate_slot(key)
            probes += resize_probes

        if insert_index is None:
            raise BenchmarkError("linear probing insert failed to find an insertion slot")

        self._record_probes(probes, "put_inserted")
        if self.slots[insert_index] is LINEAR_TOMBSTONE:
            self.tombstones -= 1
        self.slots[insert_index] = LinearProbingEntry(key, value)
        self.size += 1
        return "inserted"

    def get(self, key: str) -> str | None:
        found_index, _, probes = self._locate_slot(key)
        self._record_probes(probes, "get_hit" if found_index is not None else "get_miss")
        if found_index is None:
            return None
        slot = self.slots[found_index]
        assert isinstance(slot, LinearProbingEntry)
        return slot.value

    def delete(self, key: str) -> bool:
        found_index, _, probes = self._locate_slot(key)
        self._record_probes(probes, "delete_hit" if found_index is not None else "delete_miss")
        if found_index is None:
            if self._should_rebuild_for_tombstones():
                self._resize(self.capacity)
            return False

        self.slots[found_index] = LINEAR_TOMBSTONE
        self.size -= 1
        self.tombstones += 1
        if self.size and self._should_rebuild_for_tombstones():
            self._resize(self.capacity)
        return True

    def items(self) -> list[tuple[str, str]]:
        return sorted(
            [(slot.key, slot.value) for slot in self.slots if isinstance(slot, LinearProbingEntry)],
            key=lambda item: item[0],
        )

    def stats(self) -> dict[str, Any]:
        average_probe_count = round(self.total_probe_count / self.operation_count, 3) if self.operation_count else 0.0
        gets_summary = summarize_probe_samples(self.probe_samples_by_kind["get_hit"] + self.probe_samples_by_kind["get_miss"])
        puts_summary = summarize_probe_samples(self.probe_samples_by_kind["put_inserted"] + self.probe_samples_by_kind["put_updated"])
        deletes_summary = summarize_probe_samples(self.probe_samples_by_kind["delete_hit"] + self.probe_samples_by_kind["delete_miss"])
        return {
            "capacity": self.capacity,
            "size": self.size,
            "tombstones": self.tombstones,
            "load_factor": round(self.size / self.capacity, 4),
            "occupied_load_factor": round((self.size + self.tombstones) / self.capacity, 4),
            "resize_count": self.resize_count,
            "total_probe_count": self.total_probe_count,
            "average_probe_count": average_probe_count,
            "max_probe_count": self.max_probe_count,
            "rebuild_probe_count": self.rebuild_probe_count,
            "lookup_probe_breakdown": {
                "successful": summarize_probe_samples(self.probe_samples_by_kind["get_hit"]),
                "unsuccessful": summarize_probe_samples(self.probe_samples_by_kind["get_miss"]),
            },
            "phase_probe_breakdown": {
                "puts": puts_summary,
                "gets": gets_summary,
                "deletes": deletes_summary,
            },
            "outcome_probe_breakdown": {
                kind: summarize_probe_samples(samples)
                for kind, samples in self.probe_samples_by_kind.items()
            },
        }


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
                "| step | op | key | value | outcome | events | global depth | bucket count | entry count |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in history:
            lines.append(
                f"| {item.step} | {item.op} | `{item.key}` | `{item.value or ''}` | {item.outcome} | {_format_step_events(item)} | {item.global_depth} | {item.bucket_count} | {item.entry_count} |"
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


def _truncate_text(value: str, limit: int = 52) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _format_step_events(item: WorkloadOpResult) -> str:
    events: list[str] = []
    if item.split_delta:
        label = "split" if item.split_delta == 1 else "splits"
        events.append(f"{item.split_delta} {label}")
    if item.merge_delta:
        label = "merge" if item.merge_delta == 1 else "merges"
        events.append(f"{item.merge_delta} {label}")
    if item.directory_growth_delta:
        label = "directory growth" if item.directory_growth_delta == 1 else "directory growths"
        events.append(f"{item.directory_growth_delta} {label}")
    if item.directory_shrink_delta:
        label = "directory shrink" if item.directory_shrink_delta == 1 else "directory shrinks"
        events.append(f"{item.directory_shrink_delta} {label}")
    return ", ".join(events) if events else "steady-state"


def _bucket_palette(bucket_id: int) -> str:
    colors = [
        "#dbeafe",
        "#dcfce7",
        "#fef3c7",
        "#fae8ff",
        "#fee2e2",
        "#cffafe",
        "#ede9fe",
        "#e2e8f0",
    ]
    return colors[bucket_id % len(colors)]


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: str = "400", fill: str = "#0f172a") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Inter,Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def _svg_multiline_text(
    x: float,
    y: float,
    lines: list[str],
    *,
    size: int = 14,
    weight: str = "400",
    fill: str = "#0f172a",
    line_height: int = 16,
) -> str:
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        tspans.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" font-family="Inter,Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{"".join(tspans)}</text>'
    )


def _svg_group(*elements: str, tooltip: str | None = None) -> str:
    parts = ["<g>"]
    if tooltip:
        parts.append(f"<title>{escape(tooltip)}</title>")
    parts.extend(elements)
    parts.append("</g>")
    return "".join(parts)


def _svg_reference_id(prefix: str, *parts: str) -> str:
    seed = "|".join(parts)
    return f"{prefix}-{stable_hash(seed):016x}"


def render_visualization_svg(
    title: str,
    table: ExtendibleHashTable,
    history: list[WorkloadOpResult],
    source_label: str | None = None,
) -> str:
    card_width = 1240
    row_height = 24
    header_height = 64
    card_gap = 18
    y = 118
    cards: list[str] = []

    for item in history:
        snapshot = item.snapshot or {"stats": {"buckets": []}, "directory_rows": []}
        stats = snapshot["stats"]
        directory_rows = snapshot["directory_rows"]
        bucket_rows = stats["buckets"]
        content_rows = max(len(directory_rows), len(bucket_rows), 1)
        card_height = header_height + (content_rows + 2) * row_height + 34
        card_top = y
        cards.append(
            f'<rect x="40" y="{card_top}" width="{card_width}" height="{card_height}" rx="20" fill="#ffffff" stroke="#cbd5e1" />'
        )
        cards.append(
            _svg_group(
                _svg_text(62, card_top + 30, f"Step {item.step} · {item.op.upper()} {_truncate_text(item.key, 28)}", size=22, weight="700"),
                _svg_text(62, card_top + 54, f"Outcome: {item.outcome} · Events: {_format_step_events(item)}", size=13, fill="#334155"),
                _svg_text(
                    860,
                    card_top + 30,
                    f"depth {item.global_depth} · buckets {item.bucket_count} · entries {item.entry_count}",
                    size=13,
                    weight="600",
                    fill="#1d4ed8",
                ),
                tooltip=(
                    f"Step {item.step} · {item.op.upper()} {item.key} · Outcome: {item.outcome} · Events: {_format_step_events(item)} "
                    f"· depth {item.global_depth} · buckets {item.bucket_count} · entries {item.entry_count}"
                ),
            )
        )

        grid_top = card_top + header_height
        cards.append(_svg_text(62, grid_top + 18, "Directory aliases", size=15, weight="700"))
        cards.append(_svg_text(474, grid_top + 18, "Bucket state", size=15, weight="700"))
        cards.append(_svg_text(62, grid_top + 40, "idx / bits / bucket / entries", size=12, weight="600", fill="#475569"))
        cards.append(_svg_text(474, grid_top + 40, "bucket / ld / aliases / size / keys", size=12, weight="600", fill="#475569"))

        for row_index, row in enumerate(directory_rows):
            row_y = grid_top + 52 + row_index * row_height
            fill = _bucket_palette(int(row["bucket_id"]))
            entry_text = ", ".join(value.split("=", 1)[0] for value in row["entries"]) or "empty"
            full_directory_label = f"{row['index']:>2} · {row['bits']} · B{row['bucket_id']} · {entry_text}"
            cards.append(
                _svg_group(
                    f'<rect x="58" y="{row_y - 15}" width="388" height="20" rx="10" fill="{fill}" stroke="#bfdbfe" />',
                    _svg_text(
                        68,
                        row_y,
                        f"{row['index']:>2} · {row['bits']} · B{row['bucket_id']} · {_truncate_text(entry_text, 32)}",
                        size=12,
                    ),
                    tooltip=full_directory_label,
                )
            )

        for row_index, bucket in enumerate(bucket_rows):
            row_y = grid_top + 52 + row_index * row_height
            fill = _bucket_palette(int(bucket["bucket_id"]))
            key_text = ", ".join(bucket["keys"]) or "empty"
            full_bucket_label = (
                f"B{bucket['bucket_id']} · ld={bucket['local_depth']} · aliases={bucket['aliases']} "
                f"· size={bucket['size']} · {key_text}"
            )
            cards.append(
                _svg_group(
                    f'<rect x="470" y="{row_y - 15}" width="770" height="20" rx="10" fill="{fill}" stroke="#cbd5e1" />',
                    _svg_text(
                        480,
                        row_y,
                        f"B{bucket['bucket_id']} · ld={bucket['local_depth']} · aliases={bucket['aliases']} · size={bucket['size']} · {_truncate_text(key_text, 84)}",
                        size=12,
                    ),
                    tooltip=full_bucket_label,
                )
            )

        y += card_height + card_gap

    height = max(y + 24, 260)
    subtitle = source_label or "Workload-driven extendible hashing aliasing trace"
    summary_line = (
        f"Final depth {table.global_depth} · buckets {len(table.buckets)} · splits {table.split_count} · merges {table.merge_count} "
        f"· directory grows {table.directory_growth_count} · directory shrinks {table.directory_shrink_count}"
    )
    title_id = _svg_reference_id("viz-title", title, subtitle)
    desc_id = _svg_reference_id("viz-desc", title, subtitle, summary_line)
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="{height}" viewBox="0 0 1320 {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f"<title id=\"{title_id}\">{escape(title)}</title>",
            f"<desc id=\"{desc_id}\">{escape(subtitle + '. ' + summary_line)}</desc>",
            '<rect width="1320" height="100%" fill="#f8fafc" />',
            _svg_text(40, 42, title, size=30, weight="700"),
            _svg_text(40, 68, subtitle, size=14, fill="#334155"),
            _svg_text(40, 92, summary_line, size=14, weight="600", fill="#1d4ed8"),
            *cards,
            "</svg>",
        ]
    )


def render_visualization_html(
    title: str,
    table: ExtendibleHashTable,
    history: list[WorkloadOpResult],
    source_label: str | None = None,
) -> str:
    svg = render_visualization_svg(title, table, history, source_label=source_label)
    step_cards: list[str] = []
    for item in history:
        snapshot = item.snapshot or {"stats": {"buckets": []}, "directory_rows": []}
        stats = snapshot["stats"]
        directory_rows = snapshot["directory_rows"]
        bucket_rows = stats["buckets"]
        directory_html = "".join(
            (
                "<tr>"
                f"<td>{row['index']}</td>"
                f"<td><code>{escape(row['bits'])}</code></td>"
                f"<td>B{row['bucket_id']}</td>"
                f"<td>{row['local_depth']}</td>"
                f"<td>{escape(', '.join(value.split('=', 1)[0] for value in row['entries']) or 'empty')}</td>"
                "</tr>"
            )
            for row in directory_rows
        )
        buckets_html = "".join(
            (
                "<tr>"
                f"<td>B{bucket['bucket_id']}</td>"
                f"<td>{bucket['local_depth']}</td>"
                f"<td>{bucket['aliases']}</td>"
                f"<td>{bucket['size']}</td>"
                f"<td>{escape(', '.join(bucket['keys']) or 'empty')}</td>"
                "</tr>"
            )
            for bucket in bucket_rows
        )
        step_cards.append(
            f'''<section class="step-card">
<h2>Step {item.step} · {escape(item.op.upper())} <code>{escape(item.key)}</code></h2>
<p class="step-meta">Outcome: <strong>{escape(item.outcome)}</strong> · Events: <strong>{escape(_format_step_events(item))}</strong> · Depth <strong>{item.global_depth}</strong> · Buckets <strong>{item.bucket_count}</strong> · Entries <strong>{item.entry_count}</strong></p>
<div class="step-grid">
  <div>
    <h3>Directory aliases</h3>
    <table>
      <thead><tr><th>idx</th><th>bits</th><th>bucket</th><th>ld</th><th>keys</th></tr></thead>
      <tbody>{directory_html}</tbody>
    </table>
  </div>
  <div>
    <h3>Bucket state</h3>
    <table>
      <thead><tr><th>bucket</th><th>ld</th><th>aliases</th><th>size</th><th>keys</th></tr></thead>
      <tbody>{buckets_html}</tbody>
    </table>
  </div>
</div>
</section>'''
        )

    summary_items = [
        f"<li><strong>Final global depth:</strong> {table.global_depth}</li>",
        f"<li><strong>Final bucket count:</strong> {len(table.buckets)}</li>",
        f"<li><strong>Splits / merges:</strong> {table.split_count} / {table.merge_count}</li>",
        f"<li><strong>Directory grows / shrinks:</strong> {table.directory_growth_count} / {table.directory_shrink_count}</li>",
        f"<li><strong>Source:</strong> <code>{escape(source_label or 'inline workload')}</code></li>",
    ]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: Inter, Segoe UI, Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
  main {{ max-width: 1320px; margin: 0 auto; padding: 32px 20px 48px; }}
  h1 {{ margin-bottom: 8px; }}
  .lede {{ color: #334155; margin-top: 0; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; padding-left: 18px; }}
  .visual {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 20px; padding: 14px; overflow-x: auto; }}
  .visual svg {{ width: 100%; height: auto; display: block; }}
  .step-card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 18px; margin-top: 18px; }}
  .step-meta {{ color: #334155; }}
  .step-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th, td {{ border-bottom: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #eff6ff; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
</style>
</head>
<body>
<main>
  <h1>{escape(title)}</h1>
  <p class="lede">Self-contained artifact for visualizing how directory aliases, local depth, and bucket contents evolve over a workload.</p>
  <ul class="summary">{"".join(summary_items)}</ul>
  <section class="visual">{svg}</section>
  {"".join(step_cards)}
</main>
</body>
</html>
'''


def _chunk_thumbnail_segments(label: str, segments: list[str], *, line_limit: int = 46) -> list[str]:
    if not segments:
        return [f"{label}: none"]
    chunks: list[list[str]] = []
    current: list[str] = []
    current_length = 0
    for segment in segments:
        segment_length = len(segment) if not current else len(segment) + 3
        prefix_length = len(label) + 2 if not chunks and not current else 0
        if current and current_length + segment_length > line_limit:
            chunks.append(current)
            current = [segment]
            current_length = len(segment)
            continue
        if not current and prefix_length + len(segment) > line_limit and chunks:
            chunks.append([segment])
            current = []
            current_length = 0
            continue
        current.append(segment)
        current_length += segment_length
    if current:
        chunks.append(current)
    return [f"{label}: {' · '.join(chunk)}" for chunk in chunks]


def _thumbnail_directory_segments(directory_rows: list[dict[str, Any]]) -> list[str]:
    return [f"{row['bits']}→B{row['bucket_id']}" for row in directory_rows]


def _thumbnail_bucket_segments(bucket_rows: list[dict[str, Any]]) -> list[str]:
    return [
        f"B{bucket['bucket_id']}(ld{bucket['local_depth']},a{bucket['aliases']},n{bucket['size']})"
        for bucket in bucket_rows
    ]


def _truncate_thumbnail_lines(lines: list[str], *, max_lines: int = 3, overflow_label: str = "more") -> list[str]:
    if len(lines) <= max_lines:
        return lines
    hidden = len(lines) - (max_lines - 1)
    return [*lines[: max_lines - 1], f"(+{hidden} {overflow_label})"]


def _thumbnail_accent_color(item: WorkloadOpResult) -> str:
    if item.split_delta or item.directory_growth_delta:
        return "#2563eb"
    if item.merge_delta or item.directory_shrink_delta:
        return "#059669"
    if item.op == "delete":
        return "#dc2626" if item.outcome == "deleted" else "#f97316"
    if item.op == "get":
        return "#7c3aed" if item.outcome != "missing" else "#ea580c"
    return "#475569"


def render_visualization_thumbnail_strip_svg(
    title: str,
    table: ExtendibleHashTable,
    history: list[WorkloadOpResult],
    source_label: str | None = None,
) -> str:
    columns = 3 if len(history) >= 5 else 2 if len(history) >= 3 else 1
    margin_x = 40
    margin_y = 118
    gap_x = 20
    gap_y = 20
    total_width = 1320
    available_width = total_width - (margin_x * 2) - (gap_x * (columns - 1))
    card_width = available_width // columns
    card_height = 224
    cards: list[str] = []

    for index, item in enumerate(history):
        snapshot = item.snapshot or {"stats": {"buckets": []}, "directory_rows": []}
        stats = snapshot["stats"]
        directory_rows = snapshot["directory_rows"]
        bucket_rows = stats["buckets"]
        col = index % columns
        row = index // columns
        card_left = margin_x + col * (card_width + gap_x)
        card_top = margin_y + row * (card_height + gap_y)
        accent = _thumbnail_accent_color(item)
        directory_lines_full = _chunk_thumbnail_segments("Dir", _thumbnail_directory_segments(directory_rows), line_limit=50)
        bucket_lines_full = _chunk_thumbnail_segments("Buckets", _thumbnail_bucket_segments(bucket_rows), line_limit=50)
        directory_lines = _truncate_thumbnail_lines(directory_lines_full, max_lines=3, overflow_label="more dir rows")
        bucket_lines = _truncate_thumbnail_lines(bucket_lines_full, max_lines=3, overflow_label="more bucket rows")
        bucket_block_y = card_top + 126 + max(0, len(directory_lines) - 1) * 16
        tooltip = (
            f"Step {item.step} · {item.op.upper()} {item.key} · Outcome: {item.outcome} · Events: {_format_step_events(item)} "
            f"· depth {item.global_depth} · buckets {item.bucket_count} · entries {item.entry_count} "
            f"· {' | '.join(directory_lines_full + bucket_lines_full)}"
        )
        cards.append(
            _svg_group(
                f'<rect x="{card_left}" y="{card_top}" width="{card_width}" height="{card_height}" rx="20" fill="#ffffff" stroke="#dbe4f0" />',
                f'<rect x="{card_left + 16}" y="{card_top + 16}" width="10" height="{card_height - 32}" rx="5" fill="{accent}" />',
                _svg_text(card_left + 40, card_top + 34, f"Step {item.step} · {item.op.upper()} {_truncate_text(item.key, 18)}", size=18, weight="700"),
                _svg_text(card_left + 40, card_top + 58, _truncate_text(f"Outcome: {item.outcome} · {_format_step_events(item)}", 44), size=12, weight="600", fill="#334155"),
                _svg_text(
                    card_left + 40,
                    card_top + 80,
                    f"depth {item.global_depth} · buckets {item.bucket_count} · entries {item.entry_count}",
                    size=12,
                    weight="600",
                    fill="#1d4ed8",
                ),
                f'<line x1="{card_left + 40}" y1="{card_top + 94}" x2="{card_left + card_width - 20}" y2="{card_top + 94}" stroke="#dbe4f0" />',
                _svg_multiline_text(card_left + 40, card_top + 118, directory_lines, size=12, fill="#334155", line_height=16),
                _svg_multiline_text(card_left + 40, bucket_block_y, bucket_lines, size=12, fill="#334155", line_height=16),
                _svg_text(card_left + 40, card_top + card_height - 18, "Compact lifecycle strip for README thumbnails and slide decks.", size=11, fill="#64748b"),
                tooltip=tooltip,
            )
        )

    row_count = max(1, math.ceil(len(history) / columns))
    height = margin_y + row_count * card_height + (row_count - 1) * gap_y + 40
    subtitle = source_label or "Workload-driven extendible hashing lifecycle strip"
    summary_line = (
        f"Final depth {table.global_depth} · buckets {len(table.buckets)} · splits {table.split_count} · merges {table.merge_count} "
        f"· directory grows {table.directory_growth_count} · directory shrinks {table.directory_shrink_count}"
    )
    title_id = _svg_reference_id("viz-strip-title", title, subtitle)
    desc_id = _svg_reference_id("viz-strip-desc", title, subtitle, summary_line)
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" viewBox="0 0 {total_width} {height}" preserveAspectRatio="xMidYMin meet" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'<title id="{title_id}">{escape(title)} thumbnail strip</title>',
            f'<desc id="{desc_id}">{escape(subtitle + ". " + summary_line)}</desc>',
            f'<rect width="{total_width}" height="{height}" fill="#f8fafc" />',
            _svg_text(40, 42, f"{title} · thumbnail strip", size=30, weight="700"),
            _svg_text(40, 68, subtitle, size=14, fill="#334155"),
            _svg_text(40, 92, summary_line, size=14, weight="600", fill="#1d4ed8"),
            *cards,
            "</svg>",
        ]
    )


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
        before_split = table.split_count
        before_merge = table.merge_count
        before_growth = table.directory_growth_count
        before_shrink = table.directory_shrink_count
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
                split_delta=table.split_count - before_split,
                merge_delta=table.merge_count - before_merge,
                directory_growth_delta=table.directory_growth_count - before_growth,
                directory_shrink_delta=table.directory_shrink_count - before_shrink,
                snapshot={"stats": table.stats(), "directory_rows": table.directory_rows()},
            )
        )
    return WorkloadResult(table=table, history=history)


def validate_benchmark_suite(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise BenchmarkError("benchmark suite must be a JSON object")
    bucket_capacity = payload.get("bucket_capacity", 2)
    cuckoo_capacity = payload.get("cuckoo_capacity", 11)
    max_displacements = payload.get("max_displacements", 16)
    linear_capacity = payload.get("linear_capacity", 8)
    linear_max_load_factor = payload.get("linear_max_load_factor", 0.75)
    linear_max_tombstone_ratio = payload.get("linear_max_tombstone_ratio", 0.25)
    btree_minimum_degree = payload.get("btree_minimum_degree", 2)
    btree_page_size = payload.get("btree_page_size", 512)
    btree_value_bytes = payload.get("btree_value_bytes", 32)
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
    if not isinstance(linear_capacity, int) or linear_capacity < 4:
        raise BenchmarkError("benchmark linear_capacity must be an integer >= 4")
    if isinstance(linear_max_load_factor, bool) or not isinstance(linear_max_load_factor, (int, float)) or not 0 < float(linear_max_load_factor) < 1:
        raise BenchmarkError("benchmark linear_max_load_factor must be between 0 and 1")
    if isinstance(linear_max_tombstone_ratio, bool) or not isinstance(linear_max_tombstone_ratio, (int, float)) or not 0 <= float(linear_max_tombstone_ratio) < 1:
        raise BenchmarkError("benchmark linear_max_tombstone_ratio must be between 0 and 1")
    if not isinstance(btree_minimum_degree, int) or btree_minimum_degree < 2:
        raise BenchmarkError("benchmark btree_minimum_degree must be an integer >= 2")
    if not isinstance(btree_page_size, int) or btree_page_size < 1:
        raise BenchmarkError("benchmark btree_page_size must be a positive integer")
    if not isinstance(btree_value_bytes, int) or btree_value_bytes < 2:
        raise BenchmarkError("benchmark btree_value_bytes must be an integer >= 2")
    if not isinstance(trials, int) or trials < 1:
        raise BenchmarkError("benchmark trials must be a positive integer")
    if not isinstance(scenarios, list) or not scenarios:
        raise BenchmarkError("benchmark scenarios must be a non-empty list")

    normalized_scenarios: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_btree_keys: dict[int, str]
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
        btree_key_map: dict[str, int] = {}
        seen_btree_keys = {}
        for operation in workload["operations"]:
            key = operation["key"]
            if key in btree_key_map:
                continue
            mapped_key = benchmark_btree_key(key)
            previous_key = seen_btree_keys.get(mapped_key)
            if previous_key is not None and previous_key != key:
                raise BenchmarkError(
                    f"scenario {name!r} maps benchmark keys {previous_key!r} and {key!r} to the same B-tree key {mapped_key}"
                )
            btree_key_map[key] = mapped_key
            seen_btree_keys[mapped_key] = key
        normalized_scenarios.append(
            {
                "name": name,
                "description": description,
                "operations": workload["operations"],
                "btree_key_map": btree_key_map,
            }
        )

    return {
        "title": title.strip(),
        "bucket_capacity": bucket_capacity,
        "cuckoo_capacity": cuckoo_capacity,
        "max_displacements": max_displacements,
        "linear_capacity": linear_capacity,
        "linear_max_load_factor": float(linear_max_load_factor),
        "linear_max_tombstone_ratio": float(linear_max_tombstone_ratio),
        "btree_minimum_degree": btree_minimum_degree,
        "btree_page_size": btree_page_size,
        "btree_value_bytes": btree_value_bytes,
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


def _btree_expected_items(reference: dict[str, str], btree_key_map: dict[str, int]) -> list[dict[str, str | int]]:
    return [
        {"key": btree_key_map[key], "value": value}
        for key, value in sorted(reference.items(), key=lambda item: btree_key_map[item[0]])
    ]


def _run_benchmark_trial(
    scenario: dict[str, Any],
    bucket_capacity: int,
    cuckoo_capacity: int,
    max_displacements: int,
    linear_capacity: int,
    linear_max_load_factor: float,
    linear_max_tombstone_ratio: float,
    btree_minimum_degree: int,
    btree_page_size: int,
    btree_value_bytes: int,
    trial: int,
) -> dict[str, Any]:
    extendible = ExtendibleHashTable(bucket_capacity=bucket_capacity)
    cuckoo_class = get_cuckoo_hash_table_class()
    btree_class = get_btree_index_class()
    cuckoo = cuckoo_class(
        capacity=cuckoo_capacity,
        max_displacements=max_displacements,
        salt_a=f"extendible-benchmark-a-{scenario['name']}-{trial}",
        salt_b=f"extendible-benchmark-b-{scenario['name']}-{trial}",
    )
    linear = LinearProbingHashTable(
        capacity=linear_capacity,
        max_load_factor=linear_max_load_factor,
        max_tombstone_ratio=linear_max_tombstone_ratio,
    )
    btree = btree_class(minimum_degree=btree_minimum_degree)

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
    btree_stats = btree.stats()
    peak_btree_height = btree_stats["height"]
    peak_btree_node_count = btree_stats["nodes"]
    btree_key_map = scenario["btree_key_map"]
    initial_linear_stats = linear.stats()
    average_linear_load_factor_total = 0.0
    average_linear_occupied_load_factor_total = 0.0
    linear_load_samples = 0
    peak_linear_load_factor = initial_linear_stats["load_factor"]
    peak_linear_occupied_load_factor = initial_linear_stats["occupied_load_factor"]

    for operation in scenario["operations"]:
        op = operation["op"]
        key = operation["key"]
        value = operation["value"]
        btree_key = btree_key_map[key]

        if op == "put":
            assert value is not None
            expected_outcome = "updated" if key in reference else "inserted"
            reference[key] = value
            extendible_outcome = extendible.put(key, value)
            if extendible_outcome != expected_outcome:
                raise BenchmarkError(
                    f"extendible hashing returned {extendible_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            linear_outcome = linear.put(key, value)
            if linear_outcome != expected_outcome:
                raise BenchmarkError(
                    f"linear probing returned {linear_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            cuckoo_existing = cuckoo.get(key)
            cuckoo.insert(key, value)
            cuckoo_outcome = "updated" if cuckoo_existing is not None else "inserted"
            if cuckoo_outcome != expected_outcome:
                raise BenchmarkError(
                    f"cuckoo hashing returned {cuckoo_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            btree_existing = btree.search(btree_key)
            btree.insert(btree_key, value)
            btree_outcome = "updated" if btree_existing is not None else "inserted"
            if btree_outcome != expected_outcome:
                raise BenchmarkError(
                    f"B-tree returned {btree_outcome!r} for {key!r}; expected {expected_outcome!r}"
                )
            outcome = expected_outcome
        elif op == "get":
            expected_value = reference.get(key)
            extendible_value = extendible.get(key)
            linear_value = linear.get(key)
            cuckoo_value = cuckoo.get(key)
            btree_value = btree.search(btree_key)
            if extendible_value != expected_value:
                raise BenchmarkError(
                    f"extendible hashing lookup for {key!r} returned {extendible_value!r}; expected {expected_value!r}"
                )
            if linear_value != expected_value:
                raise BenchmarkError(
                    f"linear probing lookup for {key!r} returned {linear_value!r}; expected {expected_value!r}"
                )
            if cuckoo_value != expected_value:
                raise BenchmarkError(
                    f"cuckoo hashing lookup for {key!r} returned {cuckoo_value!r}; expected {expected_value!r}"
                )
            if btree_value != expected_value:
                raise BenchmarkError(
                    f"B-tree lookup for {key!r} returned {btree_value!r}; expected {expected_value!r}"
                )
            outcome = f"found:{expected_value}" if expected_value is not None else "missing"
        else:
            expected_removed = key in reference
            if expected_removed:
                del reference[key]
            extendible_removed = extendible.delete(key)
            linear_removed = linear.delete(key)
            cuckoo_removed = cuckoo.remove(key)
            btree_removed = btree.delete(btree_key)
            if extendible_removed != expected_removed:
                raise BenchmarkError(
                    f"extendible hashing delete for {key!r} returned {extendible_removed}; expected {expected_removed}"
                )
            if linear_removed != expected_removed:
                raise BenchmarkError(
                    f"linear probing delete for {key!r} returned {linear_removed}; expected {expected_removed}"
                )
            if cuckoo_removed != expected_removed:
                raise BenchmarkError(
                    f"cuckoo hashing delete for {key!r} returned {cuckoo_removed}; expected {expected_removed}"
                )
            if btree_removed != expected_removed:
                raise BenchmarkError(
                    f"B-tree delete for {key!r} returned {btree_removed}; expected {expected_removed}"
                )
            outcome = "deleted" if expected_removed else "missing"

        _record_operation_mix_counts(operation_mix, op, outcome)
        peak_global_depth = max(peak_global_depth, extendible.global_depth)
        peak_bucket_count = max(peak_bucket_count, len(extendible.buckets))
        peak_directory_slots = max(peak_directory_slots, len(extendible.directory))
        btree_stats = btree.stats()
        peak_btree_height = max(peak_btree_height, btree_stats["height"])
        peak_btree_node_count = max(peak_btree_node_count, btree_stats["nodes"])
        linear_stats = linear.stats()
        average_linear_load_factor_total += linear_stats["load_factor"]
        average_linear_occupied_load_factor_total += linear_stats["occupied_load_factor"]
        linear_load_samples += 1
        peak_linear_load_factor = max(peak_linear_load_factor, linear_stats["load_factor"])
        peak_linear_occupied_load_factor = max(peak_linear_occupied_load_factor, linear_stats["occupied_load_factor"])

    expected_items = sorted(reference.items(), key=lambda item: item[0])
    extendible_items = extendible.items()
    linear_items = linear.items()
    cuckoo_items = cuckoo.items()
    btree_items = btree.items()
    if extendible_items != expected_items:
        raise BenchmarkError(
            f"extendible hashing final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )
    if linear_items != expected_items:
        raise BenchmarkError(
            f"linear probing final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )
    if cuckoo_items != expected_items:
        raise BenchmarkError(
            f"cuckoo hashing final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )
    if btree_items != _btree_expected_items(reference, btree_key_map):
        raise BenchmarkError(
            f"B-tree final items did not match reference for scenario {scenario['name']!r} trial {trial}"
        )

    extendible_stats = extendible.stats()
    linear_stats = linear.stats()
    linear_metrics = {
        "initial_capacity": linear.initial_capacity,
        "max_load_factor": linear.max_load_factor,
        "max_tombstone_ratio": linear.max_tombstone_ratio,
        "final_capacity": linear_stats["capacity"],
        "final_load_factor": linear_stats["load_factor"],
        "occupied_load_factor": linear_stats["occupied_load_factor"],
        "average_load_factor": round(average_linear_load_factor_total / max(linear_load_samples, 1), 4),
        "average_occupied_load_factor": round(average_linear_occupied_load_factor_total / max(linear_load_samples, 1), 4),
        "peak_load_factor": round(peak_linear_load_factor, 4),
        "peak_occupied_load_factor": round(peak_linear_occupied_load_factor, 4),
        "tombstone_count": linear_stats["tombstones"],
        "resize_count": linear_stats["resize_count"],
        "average_probe_count": linear_stats["average_probe_count"],
        "max_probe_count": linear_stats["max_probe_count"],
        "rebuild_probe_count": linear_stats["rebuild_probe_count"],
        "lookup_probe_breakdown": linear_stats["lookup_probe_breakdown"],
        "phase_probe_breakdown": linear_stats["phase_probe_breakdown"],
        "outcome_probe_breakdown": linear_stats["outcome_probe_breakdown"],
    }
    linear_metrics["theory_overlay"] = summarize_linear_theory_overlay(linear_metrics)
    cuckoo_stats = cuckoo.stats()
    btree_stats = btree.stats()
    btree_layout = btree.page_layout(page_size=btree_page_size, value_bytes=btree_value_bytes)
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
        "linear": linear_metrics,
        "cuckoo": {
            "final_capacity": cuckoo_stats["capacity"],
            "load_factor": cuckoo_stats["load_factor"],
            "rehash_count": cuckoo_stats["rehash_count"],
            "displacement_count": cuckoo_stats["displacement_count"],
            "empty_slots": cuckoo_stats["empty_slots"],
        },
        "btree": {
            "minimum_degree": btree_minimum_degree,
            "page_size": btree_page_size,
            "value_bytes": btree_value_bytes,
            "final_height": btree_stats["height"],
            "peak_height": peak_btree_height,
            "final_node_count": btree_stats["nodes"],
            "peak_node_count": peak_btree_node_count,
            "root_keys": btree_stats["root_keys"],
            "page_padding_bytes": btree_layout["padding_bytes"],
            "paged_file_bytes": btree_layout["header_bytes"] + (btree_stats["nodes"] * btree_page_size),
        },
    }


def _average(values: list[int | float], digits: int = 3) -> float:
    return round(sum(values) / len(values), digits)


def _linear_probing_expected_probes(load_factor: int | float) -> dict[str, float]:
    alpha = max(0.0, min(float(load_factor), 0.999))
    remainder = max(1e-9, 1.0 - alpha)
    return {
        "load_factor": round(alpha, 4),
        "successful_average_probe_count": round(0.5 * (1 + (1 / remainder)), 3),
        "unsuccessful_average_probe_count": round(0.5 * (1 + (1 / (remainder * remainder))), 3),
    }


def summarize_linear_theory_overlay(linear: dict[str, Any]) -> dict[str, Any]:
    average_reference = _linear_probing_expected_probes(linear["average_occupied_load_factor"])
    final_reference = _linear_probing_expected_probes(linear["occupied_load_factor"])
    peak_reference = _linear_probing_expected_probes(linear["peak_occupied_load_factor"])
    observed_successful = linear["lookup_probe_breakdown"]["successful"]["average_probe_count"]
    observed_unsuccessful = linear["lookup_probe_breakdown"]["unsuccessful"]["average_probe_count"]

    def format_value(value: int | float, digits: int = 3) -> str:
        rounded = round(float(value), digits)
        if rounded.is_integer():
            return str(int(rounded))
        return f"{rounded:.{digits}f}".rstrip("0").rstrip(".")

    return {
        "formula": LINEAR_PROBING_THEORY_FORMULA,
        "reference_basis": LINEAR_PROBING_THEORY_REFERENCE_BASIS,
        "average_occupied_reference": average_reference,
        "final_occupied_reference": final_reference,
        "peak_occupied_reference": peak_reference,
        "observed": {
            "successful_average_probe_count": observed_successful,
            "unsuccessful_average_probe_count": observed_unsuccessful,
        },
        "delta_vs_average_reference": {
            "successful_average_probe_count": round(
                observed_successful - average_reference["successful_average_probe_count"],
                3,
            ),
            "unsuccessful_average_probe_count": round(
                observed_unsuccessful - average_reference["unsuccessful_average_probe_count"],
                3,
            ),
        },
        "summary_note": (
            f"Average occupied α≈{format_value(average_reference['load_factor'], digits=4)} predicts about "
            f"{format_value(average_reference['successful_average_probe_count'])} successful probes and "
            f"{format_value(average_reference['unsuccessful_average_probe_count'])} unsuccessful probes; "
            f"observed hit/miss averages were {format_value(observed_successful)} and "
            f"{format_value(observed_unsuccessful)}. Peak occupied α≈"
            f"{format_value(peak_reference['load_factor'], digits=4)} gives miss-cost context for the clustering spikes."
        ),
    }


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

    linear_signatures = {
        json.dumps(row["linear"], sort_keys=True)
        for row in trial_rows
    }
    if len(linear_signatures) != 1:
        raise BenchmarkError(
            f"scenario {scenario['name']!r} produced inconsistent linear-probing metrics across trials"
        )

    btree_signatures = {
        json.dumps(row["btree"], sort_keys=True)
        for row in trial_rows
    }
    if len(btree_signatures) != 1:
        raise BenchmarkError(
            f"scenario {scenario['name']!r} produced inconsistent B-tree metrics across trials"
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
        "linear": dict(first_row["linear"]),
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
        "btree": dict(first_row["btree"]),
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
                linear_capacity=suite["linear_capacity"],
                linear_max_load_factor=suite["linear_max_load_factor"],
                linear_max_tombstone_ratio=suite["linear_max_tombstone_ratio"],
                btree_minimum_degree=suite["btree_minimum_degree"],
                btree_page_size=suite["btree_page_size"],
                btree_value_bytes=suite["btree_value_bytes"],
                trial=trial,
            )
            for trial in range(1, suite["trials"] + 1)
        ]
        results.append(summarize_benchmark_trials(scenario, trial_rows))
    return {
        "title": suite["title"],
        "linear_theory_note": {
            "formula": LINEAR_PROBING_THEORY_FORMULA,
            "reference_basis": LINEAR_PROBING_THEORY_REFERENCE_BASIS,
        },
        "bucket_capacity": suite["bucket_capacity"],
        "cuckoo_capacity": suite["cuckoo_capacity"],
        "max_displacements": suite["max_displacements"],
        "linear_capacity": suite["linear_capacity"],
        "linear_max_load_factor": suite["linear_max_load_factor"],
        "linear_max_tombstone_ratio": suite["linear_max_tombstone_ratio"],
        "btree_minimum_degree": suite["btree_minimum_degree"],
        "btree_page_size": suite["btree_page_size"],
        "btree_value_bytes": suite["btree_value_bytes"],
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
            f"- Linear probing capacity / max load / tombstone ratio: `{summary['linear_capacity']}` / `{summary['linear_max_load_factor']}` / `{summary['linear_max_tombstone_ratio']}`",
            f"- Cuckoo starting capacity: `{summary['cuckoo_capacity']}`",
            f"- Cuckoo max displacements: `{summary['max_displacements']}`",
            f"- B-tree minimum degree: `{summary['btree_minimum_degree']}`",
            f"- B-tree page size / value bytes: `{summary['btree_page_size']}` / `{summary['btree_value_bytes']}`",
            f"- Trials per scenario: `{summary['trials']}`",
            "",
            "## Linear probing theory overlay",
            f"- Formula: `{summary['linear_theory_note']['formula']}`",
            f"- Reference basis: {summary['linear_theory_note']['reference_basis']}",
            "",
            "| Scenario | Avg occupied α | Peak occupied α | Expected hit @ avg α | Observed hit | Δ | Expected miss @ avg α | Observed miss | Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["results"]:
        overlay = row["linear"]["theory_overlay"]
        average_reference = overlay["average_occupied_reference"]
        peak_reference = overlay["peak_occupied_reference"]
        lines.append(
            "| {name} | {avg_alpha} | {peak_alpha} | {expected_hit} | {observed_hit} | {delta_hit} | {expected_miss} | {observed_miss} | {delta_miss} |".format(
                name=row["name"],
                avg_alpha=average_reference["load_factor"],
                peak_alpha=peak_reference["load_factor"],
                expected_hit=average_reference["successful_average_probe_count"],
                observed_hit=overlay["observed"]["successful_average_probe_count"],
                delta_hit=overlay["delta_vs_average_reference"]["successful_average_probe_count"],
                expected_miss=average_reference["unsuccessful_average_probe_count"],
                observed_miss=overlay["observed"]["unsuccessful_average_probe_count"],
                delta_miss=overlay["delta_vs_average_reference"]["unsuccessful_average_probe_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Scenario scoreboard",
            "| Scenario | Ops | Final entries | Ext splits | Ext merges | Peak depth | Linear avg probes | Linear get hit/miss avg | Linear max probe | Cuckoo avg rehashes | Cuckoo avg displacements | B-tree height | B-tree nodes | B-tree paged bytes |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["results"]:
        lines.append(
            "| {name} | {ops} | {entries} | {splits} | {merges} | {peak_depth} | {linear_avg} | {linear_hit_miss} | {linear_max} | {rehashes} | {displacements} | {btree_height} | {btree_nodes} | {btree_bytes} |".format(
                name=row["name"],
                ops=row["operation_count"],
                entries=row["final_entry_count"],
                splits=row["extendible"]["split_count"],
                merges=row["extendible"]["merge_count"],
                peak_depth=row["extendible"]["peak_global_depth"],
                linear_avg=row["linear"]["average_probe_count"],
                linear_hit_miss=(
                    f"{row['linear']['lookup_probe_breakdown']['successful']['average_probe_count']}"
                    f" / {row['linear']['lookup_probe_breakdown']['unsuccessful']['average_probe_count']}"
                ),
                linear_max=row["linear"]["max_probe_count"],
                rehashes=row["cuckoo"]["average_rehash_count"],
                displacements=row["cuckoo"]["average_displacement_count"],
                btree_height=row["btree"]["final_height"],
                btree_nodes=row["btree"]["final_node_count"],
                btree_bytes=row["btree"]["paged_file_bytes"],
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
                f"- Linear probing baseline finished at capacity `{row['linear']['final_capacity']}` with load factor `{row['linear']['final_load_factor']}`, tombstones `{row['linear']['tombstone_count']}`, average probe count `{row['linear']['average_probe_count']}`, max probe `{row['linear']['max_probe_count']}`, and `{row['linear']['resize_count']}` rebuild(s).",
                f"- Linear lookup probe split: successful gets avg/p50/p95/max = `{_format_probe_summary(row['linear']['lookup_probe_breakdown']['successful'])}`; unsuccessful gets avg/p50/p95/max = `{_format_probe_summary(row['linear']['lookup_probe_breakdown']['unsuccessful'])}`.",
                f"- Linear theory overlay: {row['linear']['theory_overlay']['summary_note']}",
                f"- Linear phase probe split: puts avg/p50/p95/max = `{_format_probe_summary(row['linear']['phase_probe_breakdown']['puts'])}`; gets avg/p50/p95/max = `{_format_probe_summary(row['linear']['phase_probe_breakdown']['gets'])}`; deletes avg/p50/p95/max = `{_format_probe_summary(row['linear']['phase_probe_breakdown']['deletes'])}`.",
                f"- Cuckoo hashing averaged `{row['cuckoo']['average_rehash_count']}` rehashes and `{row['cuckoo']['average_displacement_count']}` displacements, finishing between capacities `{row['cuckoo']['final_capacity_range'][0]}` and `{row['cuckoo']['final_capacity_range'][1]}`.",
                f"- B-tree page baseline finished at height `{row['btree']['final_height']}` across `{row['btree']['final_node_count']}` node(s); at `page_size={row['btree']['page_size']}` and `value_bytes={row['btree']['value_bytes']}` the paged snapshot would occupy `{row['btree']['paged_file_bytes']}` bytes with `{row['btree']['page_padding_bytes']}` bytes of fixed slack per page.",
                f"- Validation: final states matched across `{row['validation']['trials']}` deterministic trial(s).",
                "",
                "| Linear phase | Count | Avg probes | P50 | P95 | Max |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
                f"| puts | {row['linear']['phase_probe_breakdown']['puts']['count']} | {row['linear']['phase_probe_breakdown']['puts']['average_probe_count']} | {row['linear']['phase_probe_breakdown']['puts']['p50_probe_count']} | {row['linear']['phase_probe_breakdown']['puts']['p95_probe_count']} | {row['linear']['phase_probe_breakdown']['puts']['max_probe_count']} |",
                f"| gets | {row['linear']['phase_probe_breakdown']['gets']['count']} | {row['linear']['phase_probe_breakdown']['gets']['average_probe_count']} | {row['linear']['phase_probe_breakdown']['gets']['p50_probe_count']} | {row['linear']['phase_probe_breakdown']['gets']['p95_probe_count']} | {row['linear']['phase_probe_breakdown']['gets']['max_probe_count']} |",
                f"| deletes | {row['linear']['phase_probe_breakdown']['deletes']['count']} | {row['linear']['phase_probe_breakdown']['deletes']['average_probe_count']} | {row['linear']['phase_probe_breakdown']['deletes']['p50_probe_count']} | {row['linear']['phase_probe_breakdown']['deletes']['p95_probe_count']} | {row['linear']['phase_probe_breakdown']['deletes']['max_probe_count']} |",
                "",
                "| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Linear avg probes | Linear get hit avg | Linear get miss avg | Linear get miss p95 | Linear max probe | Linear rebuilds | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for trial_row in row["trial_rows"]:
            lines.append(
                f"| {trial_row['trial']} | {trial_row['extendible']['split_count']} | {trial_row['extendible']['merge_count']} | {trial_row['extendible']['peak_global_depth']} | {trial_row['extendible']['peak_bucket_count']} | {trial_row['extendible']['peak_directory_slots']} | {trial_row['linear']['average_probe_count']} | {trial_row['linear']['lookup_probe_breakdown']['successful']['average_probe_count']} | {trial_row['linear']['lookup_probe_breakdown']['unsuccessful']['average_probe_count']} | {trial_row['linear']['lookup_probe_breakdown']['unsuccessful']['p95_probe_count']} | {trial_row['linear']['max_probe_count']} | {trial_row['linear']['resize_count']} | {trial_row['cuckoo']['rehash_count']} | {trial_row['cuckoo']['displacement_count']} | {trial_row['cuckoo']['final_capacity']} | {trial_row['btree']['final_height']} | {trial_row['btree']['final_node_count']} | {trial_row['btree']['paged_file_bytes']} |"
            )
        lines.append("")

    return "\n".join(lines)


def _format_probe_summary(summary: dict[str, Any]) -> str:
    return (
        f"{summary['average_probe_count']} / {summary['p50_probe_count']} / "
        f"{summary['p95_probe_count']} / {summary['max_probe_count']}"
    )


def _format_dashboard_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    rounded = round(float(value), 4)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def _render_benchmark_dashboard_metric(
    label: str,
    value: int | float,
    maximum: int | float,
    *,
    accent: str,
    detail: str | None = None,
) -> str:
    numeric_value = float(value)
    numeric_max = float(maximum)
    width = 0.0 if numeric_max <= 0 else max(0.0, min(100.0, (numeric_value / numeric_max) * 100.0))
    detail_html = f'<div class="metric-detail">{escape(detail)}</div>' if detail else ""
    return f'''<div class="metric">
  <div class="metric-head">
    <span>{escape(label)}</span>
    <strong>{escape(_format_dashboard_number(value))}</strong>
  </div>
  <div class="metric-bar" aria-hidden="true"><span style="width: {width:.1f}%; background: {escape(accent)};"></span></div>
  {detail_html}
</div>'''


def render_benchmark_dashboard_html(title: str, summary: dict[str, Any], suite_source: str | None = None) -> str:
    results = summary["results"]
    if not results:
        raise BenchmarkError("benchmark summary must include at least one scenario result")

    totals = {
        "operation_count": sum(row["operation_count"] for row in results),
        "max_final_entry_count": max(row["final_entry_count"] for row in results),
        "max_extendible_peak_depth": max(row["extendible"]["peak_global_depth"] for row in results),
        "max_btree_bytes": max(row["btree"]["paged_file_bytes"] for row in results),
    }
    maxima = {
        "extendible_split_count": max(row["extendible"]["split_count"] for row in results),
        "extendible_merge_count": max(row["extendible"]["merge_count"] for row in results),
        "extendible_peak_global_depth": max(row["extendible"]["peak_global_depth"] for row in results),
        "extendible_peak_directory_slots": max(row["extendible"]["peak_directory_slots"] for row in results),
        "extendible_load_factor": max(row["extendible"]["load_factor"] for row in results),
        "linear_average_probe_count": max(row["linear"]["average_probe_count"] for row in results),
        "linear_max_probe_count": max(row["linear"]["max_probe_count"] for row in results),
        "linear_successful_lookup_average_probe_count": max(
            row["linear"]["lookup_probe_breakdown"]["successful"]["average_probe_count"] for row in results
        ),
        "linear_unsuccessful_lookup_average_probe_count": max(
            row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["average_probe_count"] for row in results
        ),
        "linear_resize_count": max(row["linear"]["resize_count"] for row in results),
        "linear_final_load_factor": max(row["linear"]["final_load_factor"] for row in results),
        "cuckoo_average_rehash_count": max(row["cuckoo"]["average_rehash_count"] for row in results),
        "cuckoo_average_displacement_count": max(row["cuckoo"]["average_displacement_count"] for row in results),
        "cuckoo_average_load_factor": max(row["cuckoo"]["average_load_factor"] for row in results),
        "btree_final_height": max(row["btree"]["final_height"] for row in results),
        "btree_final_node_count": max(row["btree"]["final_node_count"] for row in results),
        "btree_paged_file_bytes": max(row["btree"]["paged_file_bytes"] for row in results),
    }

    summary_cards = [
        ("Scenarios", summary["scenario_count"], f"{summary['trials']} deterministic trial(s) each"),
        ("Operations", totals["operation_count"], f"largest final live set: {totals['max_final_entry_count']} entries"),
        ("Peak extendible depth", totals["max_extendible_peak_depth"], "highest global-depth spike in the suite"),
        ("Largest B-tree snapshot", totals["max_btree_bytes"], "max paged-file bytes across scenarios"),
    ]
    summary_cards_html = "".join(
        f'''<article class="summary-card">
  <h2>{escape(label)}</h2>
  <strong>{escape(_format_dashboard_number(value))}</strong>
  <p>{escape(detail)}</p>
</article>'''
        for label, value, detail in summary_cards
    )

    scoreboard_rows = "".join(
        f'''<tr>
  <th scope="row">{escape(row['name'])}</th>
  <td>{row['operation_count']}</td>
  <td>{row['final_entry_count']}</td>
  <td>{row['extendible']['split_count']} / {row['extendible']['merge_count']}</td>
  <td>{row['extendible']['peak_global_depth']} / {row['extendible']['peak_directory_slots']}</td>
  <td>{escape(_format_dashboard_number(row['linear']['average_probe_count']))} / {row['linear']['max_probe_count']}</td>
  <td>{escape(_format_dashboard_number(row['linear']['lookup_probe_breakdown']['successful']['average_probe_count']))} / {escape(_format_dashboard_number(row['linear']['lookup_probe_breakdown']['unsuccessful']['average_probe_count']))}</td>
  <td>{escape(_format_dashboard_number(row['cuckoo']['average_rehash_count']))} / {escape(_format_dashboard_number(row['cuckoo']['average_displacement_count']))}</td>
  <td>{row['btree']['final_height']} / {row['btree']['final_node_count']}</td>
  <td>{row['btree']['paged_file_bytes']}</td>
</tr>'''
        for row in results
    )

    scenario_sections: list[str] = []
    for row in results:
        operation_mix = row["operation_mix"]
        chips = [
            f"ops {row['operation_count']}",
            f"entries {row['final_entry_count']}",
            f"puts {operation_mix['puts']}",
            f"gets {operation_mix['gets']}",
            f"deletes {operation_mix['deletes']}",
            f"trials {row['validation']['trials']}",
        ]
        chip_html = "".join(f'<li>{escape(chip)}</li>' for chip in chips)
        successful_lookup = row["linear"]["lookup_probe_breakdown"]["successful"]
        unsuccessful_lookup = row["linear"]["lookup_probe_breakdown"]["unsuccessful"]
        linear_lookup_split_html = (
            f'<div class="split-callout"><strong>Lookup split:</strong> hits avg/p95/max '
            f'{escape(_format_dashboard_number(successful_lookup["average_probe_count"]))} / {successful_lookup["p95_probe_count"]} / {successful_lookup["max_probe_count"]}'
            f' · misses avg/p95/max {escape(_format_dashboard_number(unsuccessful_lookup["average_probe_count"]))} / {unsuccessful_lookup["p95_probe_count"]} / {unsuccessful_lookup["max_probe_count"]}</div>'
        )
        theory_overlay = row["linear"]["theory_overlay"]
        linear_theory_callout_html = (
            f'<div class="theory-callout"><strong>Theory overlay:</strong> {escape(theory_overlay["summary_note"])}</div>'
        )
        phase_rows = []
        for label, key in (("puts", "puts"), ("gets", "gets"), ("deletes", "deletes")):
            phase = row["linear"]["phase_probe_breakdown"][key]
            phase_rows.append(
                f'''<tr>
  <th scope="row">{escape(label)}</th>
  <td>{phase['count']}</td>
  <td>{escape(_format_dashboard_number(phase['average_probe_count']))}</td>
  <td>{phase['p50_probe_count']}</td>
  <td>{phase['p95_probe_count']}</td>
  <td>{phase['max_probe_count']}</td>
</tr>'''
            )
        linear_phase_table_html = (
            '<div class="phase-table-wrap"><table><caption>Linear phase split for '
            f"{escape(row['name'])}</caption><thead><tr><th scope=\"col\">Phase</th><th scope=\"col\">Count</th><th scope=\"col\">Avg probes</th><th scope=\"col\">P50</th><th scope=\"col\">P95</th><th scope=\"col\">Max</th></tr></thead><tbody>"
            + "".join(phase_rows)
            + "</tbody></table></div>"
        )
        extendible_metrics = "".join(
            [
                _render_benchmark_dashboard_metric(
                    "splits",
                    row["extendible"]["split_count"],
                    maxima["extendible_split_count"],
                    accent="#2563eb",
                    detail=f"final buckets {row['extendible']['final_bucket_count']}",
                ),
                _render_benchmark_dashboard_metric(
                    "merges",
                    row["extendible"]["merge_count"],
                    maxima["extendible_merge_count"],
                    accent="#0f766e",
                    detail=f"directory shrinks {row['extendible']['directory_shrink_count']}",
                ),
                _render_benchmark_dashboard_metric(
                    "peak depth",
                    row["extendible"]["peak_global_depth"],
                    maxima["extendible_peak_global_depth"],
                    accent="#7c3aed",
                    detail=f"final depth {row['extendible']['final_global_depth']}",
                ),
                _render_benchmark_dashboard_metric(
                    "peak directory slots",
                    row["extendible"]["peak_directory_slots"],
                    maxima["extendible_peak_directory_slots"],
                    accent="#9333ea",
                    detail=f"directory grows {row['extendible']['directory_growth_count']}",
                ),
                _render_benchmark_dashboard_metric(
                    "load factor",
                    row["extendible"]["load_factor"],
                    maxima["extendible_load_factor"],
                    accent="#f59e0b",
                    detail="final occupancy across live buckets",
                ),
            ]
        )
        linear_metrics = "".join(
            [
                _render_benchmark_dashboard_metric(
                    "avg probes",
                    row["linear"]["average_probe_count"],
                    maxima["linear_average_probe_count"],
                    accent="#2563eb",
                    detail=(
                        f"get hit avg {escape(_format_dashboard_number(successful_lookup['average_probe_count']))} · "
                        f"get miss avg {escape(_format_dashboard_number(unsuccessful_lookup['average_probe_count']))}"
                    ),
                ),
                _render_benchmark_dashboard_metric(
                    "max probe",
                    row["linear"]["max_probe_count"],
                    maxima["linear_max_probe_count"],
                    accent="#7c3aed",
                    detail=(
                        f"miss p95 {unsuccessful_lookup['p95_probe_count']} · rebuild probes {row['linear']['rebuild_probe_count']}"
                    ),
                ),
                _render_benchmark_dashboard_metric(
                    "get hit avg",
                    successful_lookup["average_probe_count"],
                    maxima["linear_successful_lookup_average_probe_count"],
                    accent="#0f766e",
                    detail=f"p95 {successful_lookup['p95_probe_count']} across {successful_lookup['count']} hit lookup(s)",
                ),
                _render_benchmark_dashboard_metric(
                    "get miss avg",
                    unsuccessful_lookup["average_probe_count"],
                    maxima["linear_unsuccessful_lookup_average_probe_count"],
                    accent="#dc2626",
                    detail=f"p95 {unsuccessful_lookup['p95_probe_count']} across {unsuccessful_lookup['count']} miss lookup(s)",
                ),
                _render_benchmark_dashboard_metric(
                    "rebuilds",
                    row["linear"]["resize_count"],
                    maxima["linear_resize_count"],
                    accent="#0f766e",
                    detail=f"tombstones {row['linear']['tombstone_count']}",
                ),
                _render_benchmark_dashboard_metric(
                    "final load",
                    row["linear"]["final_load_factor"],
                    maxima["linear_final_load_factor"],
                    accent="#f59e0b",
                    detail=f"occupied load {row['linear']['occupied_load_factor']}",
                ),
            ]
        )
        cuckoo_metrics = "".join(
            [
                _render_benchmark_dashboard_metric(
                    "avg rehashes",
                    row["cuckoo"]["average_rehash_count"],
                    maxima["cuckoo_average_rehash_count"],
                    accent="#dc2626",
                    detail=f"capacity range {row['cuckoo']['final_capacity_range'][0]}-{row['cuckoo']['final_capacity_range'][1]}",
                ),
                _render_benchmark_dashboard_metric(
                    "avg displacements",
                    row["cuckoo"]["average_displacement_count"],
                    maxima["cuckoo_average_displacement_count"],
                    accent="#ea580c",
                    detail=f"empty slots {row['cuckoo']['empty_slot_range'][0]}-{row['cuckoo']['empty_slot_range'][1]}",
                ),
                _render_benchmark_dashboard_metric(
                    "avg load factor",
                    row["cuckoo"]["average_load_factor"],
                    maxima["cuckoo_average_load_factor"],
                    accent="#0891b2",
                    detail="post-run table occupancy",
                ),
            ]
        )
        btree_metrics = "".join(
            [
                _render_benchmark_dashboard_metric(
                    "final height",
                    row["btree"]["final_height"],
                    maxima["btree_final_height"],
                    accent="#4f46e5",
                    detail=f"peak height {row['btree']['peak_height']}",
                ),
                _render_benchmark_dashboard_metric(
                    "node count",
                    row["btree"]["final_node_count"],
                    maxima["btree_final_node_count"],
                    accent="#9333ea",
                    detail=f"root keys {row['btree']['root_keys']}",
                ),
                _render_benchmark_dashboard_metric(
                    "paged file bytes",
                    row["btree"]["paged_file_bytes"],
                    maxima["btree_paged_file_bytes"],
                    accent="#16a34a",
                    detail=f"padding per page {row['btree']['page_padding_bytes']} bytes",
                ),
            ]
        )
        trial_rows = "".join(
            f'''<tr>
  <td>{trial_row['trial']}</td>
  <td>{trial_row['extendible']['split_count']}</td>
  <td>{trial_row['extendible']['merge_count']}</td>
  <td>{trial_row['extendible']['peak_global_depth']}</td>
  <td>{escape(_format_dashboard_number(trial_row['linear']['average_probe_count']))}</td>
  <td>{escape(_format_dashboard_number(trial_row['linear']['lookup_probe_breakdown']['successful']['average_probe_count']))}</td>
  <td>{escape(_format_dashboard_number(trial_row['linear']['lookup_probe_breakdown']['unsuccessful']['average_probe_count']))}</td>
  <td>{trial_row['linear']['lookup_probe_breakdown']['unsuccessful']['p95_probe_count']}</td>
  <td>{trial_row['linear']['max_probe_count']}</td>
  <td>{trial_row['linear']['resize_count']}</td>
  <td>{trial_row['cuckoo']['rehash_count']}</td>
  <td>{trial_row['cuckoo']['displacement_count']}</td>
  <td>{trial_row['btree']['final_height']}</td>
  <td>{trial_row['btree']['paged_file_bytes']}</td>
</tr>'''
            for trial_row in row["trial_rows"]
        )
        scenario_sections.append(
            f'''<section class="scenario-card">
  <header class="scenario-header">
    <div>
      <h2>{escape(row['name'])}</h2>
      <p>{escape(row['description'] or 'No description provided.')}</p>
    </div>
    <ul class="chips">{chip_html}</ul>
  </header>
  <div class="metric-grid">
    <article class="metric-panel">
      <h3>Extendible hashing</h3>
      <p>Directory growth and bucket-split behavior for the benchmark workload.</p>
      {extendible_metrics}
    </article>
    <article class="metric-panel">
      <h3>Linear probing baseline</h3>
      <p>Primary-clustering pressure, tombstone cleanup, and probe lengths for the same key stream.</p>
      {linear_metrics}
      {linear_lookup_split_html}
      {linear_theory_callout_html}
      {linear_phase_table_html}
    </article>
    <article class="metric-panel">
      <h3>Cuckoo hashing</h3>
      <p>Relocation pressure and occupancy characteristics across deterministic trials.</p>
      {cuckoo_metrics}
    </article>
    <article class="metric-panel">
      <h3>B-tree page baseline</h3>
      <p>Tree-shape and paged-storage estimates for the same key stream.</p>
      {btree_metrics}
    </article>
  </div>
  <div class="trial-table-wrap">
    <table>
      <caption>Per-trial validation for {escape(row['name'])}</caption>
      <thead>
        <tr>
          <th scope="col">Trial</th>
          <th scope="col">Ext splits</th>
          <th scope="col">Ext merges</th>
          <th scope="col">Peak depth</th>
          <th scope="col">Linear avg probes</th>
          <th scope="col">Linear get hit avg</th>
          <th scope="col">Linear get miss avg</th>
          <th scope="col">Linear get miss p95</th>
          <th scope="col">Linear max probe</th>
          <th scope="col">Linear rebuilds</th>
          <th scope="col">Cuckoo rehashes</th>
          <th scope="col">Cuckoo displacements</th>
          <th scope="col">B-tree height</th>
          <th scope="col">B-tree bytes</th>
        </tr>
      </thead>
      <tbody>{trial_rows}</tbody>
    </table>
  </div>
</section>'''
        )

    theory_rows = "".join(
        f'''<tr>
  <th scope="row">{escape(row["name"])}</th>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["average_occupied_reference"]["load_factor"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["peak_occupied_reference"]["load_factor"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["average_occupied_reference"]["successful_average_probe_count"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["observed"]["successful_average_probe_count"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["delta_vs_average_reference"]["successful_average_probe_count"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["average_occupied_reference"]["unsuccessful_average_probe_count"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["observed"]["unsuccessful_average_probe_count"]))}</td>
  <td>{escape(_format_dashboard_number(row["linear"]["theory_overlay"]["delta_vs_average_reference"]["unsuccessful_average_probe_count"]))}</td>
</tr>'''
        for row in results
    )
    theory_panel_html = f'''<section class="theory-panel">
    <h2>Linear probing theory overlay</h2>
    <p><strong>Formula:</strong> <code>{escape(summary['linear_theory_note']['formula'])}</code><br />
    <strong>Reference basis:</strong> {escape(summary['linear_theory_note']['reference_basis'])}</p>
    <table>
      <caption>Observed hit/miss probe averages compared with classic load-factor expectations</caption>
      <thead>
        <tr>
          <th scope="col">Scenario</th>
          <th scope="col">Avg occupied α</th>
          <th scope="col">Peak occupied α</th>
          <th scope="col">Expected hit @ avg α</th>
          <th scope="col">Observed hit</th>
          <th scope="col">Δ hit</th>
          <th scope="col">Expected miss @ avg α</th>
          <th scope="col">Observed miss</th>
          <th scope="col">Δ miss</th>
        </tr>
      </thead>
      <tbody>{theory_rows}</tbody>
    </table>
  </section>'''
    suite_source_html = (
        f'<p class="suite-source"><strong>Suite source:</strong> <code>{escape(suite_source)}</code></p>'
        if suite_source
        else ""
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Inter, Segoe UI, Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
  main {{ max-width: 1380px; margin: 0 auto; padding: 32px 20px 56px; }}
  h1 {{ margin-bottom: 10px; font-size: 2.2rem; }}
  .lede {{ margin: 0; color: #334155; max-width: 78ch; }}
  .suite-source {{ color: #475569; margin-top: 10px; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 24px 0; }}
  .summary-card, .scoreboard, .scenario-card, .theory-panel {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 20px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04); }}
  .summary-card {{ padding: 18px 20px; }}
  .summary-card h2 {{ margin: 0 0 8px; font-size: 0.95rem; color: #475569; }}
  .summary-card strong {{ display: block; font-size: 1.9rem; color: #0f172a; }}
  .summary-card p {{ margin: 8px 0 0; color: #475569; }}
  .scoreboard {{ padding: 18px 20px; overflow-x: auto; }}
  .theory-panel {{ padding: 18px 20px; margin-bottom: 18px; overflow-x: auto; }}
  .theory-panel p {{ color: #475569; max-width: 88ch; }}
  .scoreboard table, .trial-table-wrap table, .theory-panel table {{ width: 100%; border-collapse: collapse; }}
  caption {{ text-align: left; font-weight: 700; padding-bottom: 12px; color: #0f172a; }}
  thead th {{ background: #eff6ff; color: #1e3a8a; }}
  th, td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }}
  tbody tr:last-child td, tbody tr:last-child th {{ border-bottom: none; }}
  .scenario-stack {{ display: grid; gap: 18px; margin-top: 20px; }}
  .scenario-card {{ padding: 20px; }}
  .scenario-header {{ display: flex; gap: 16px; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; }}
  .scenario-header h2 {{ margin: 0 0 8px; font-size: 1.35rem; }}
  .scenario-header p {{ margin: 0; color: #475569; max-width: 72ch; }}
  .chips {{ list-style: none; display: flex; flex-wrap: wrap; gap: 8px; padding: 0; margin: 0; }}
  .chips li {{ background: #e2e8f0; color: #1e293b; border-radius: 999px; padding: 6px 10px; font-size: 0.88rem; }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-top: 18px; }}
  .metric-panel {{ background: #f8fafc; border: 1px solid #dbe4f0; border-radius: 18px; padding: 16px; }}
  .metric-panel h3 {{ margin: 0 0 6px; font-size: 1rem; }}
  .metric-panel p {{ margin: 0 0 16px; color: #475569; min-height: 38px; }}
  .metric + .metric {{ margin-top: 12px; }}
  .metric-head {{ display: flex; justify-content: space-between; gap: 12px; font-size: 0.92rem; }}
  .metric-head strong {{ color: #0f172a; }}
  .metric-bar {{ margin-top: 6px; width: 100%; height: 10px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }}
  .metric-bar span {{ display: block; height: 100%; border-radius: 999px; }}
  .metric-detail {{ margin-top: 6px; color: #475569; font-size: 0.84rem; }}
  .split-callout {{ margin-top: 16px; padding: 12px 14px; border-radius: 14px; background: #eef2ff; color: #312e81; font-size: 0.9rem; line-height: 1.45; }}
  .theory-callout {{ margin-top: 12px; padding: 12px 14px; border-radius: 14px; background: #f8fafc; border: 1px solid #dbe4f0; color: #334155; font-size: 0.9rem; line-height: 1.5; }}
  .phase-table-wrap {{ margin-top: 14px; overflow-x: auto; }}
  .phase-table-wrap table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; background: #fff; border: 1px solid #dbe4f0; border-radius: 14px; overflow: hidden; }}
  .phase-table-wrap caption {{ padding-bottom: 10px; }}
  .trial-table-wrap {{ margin-top: 18px; overflow-x: auto; }}
  @media (max-width: 720px) {{
    main {{ padding-left: 14px; padding-right: 14px; }}
    .scenario-card, .scoreboard {{ padding-left: 14px; padding-right: 14px; }}
    th, td {{ padding-left: 8px; padding-right: 8px; }}
  }}
</style>
</head>
<body>
<main>
  <h1>{escape(title)}</h1>
  <p class="lede">Compact benchmark dashboard for the extendible-hashing lab. It keeps the same deterministic benchmark data as the JSON, Markdown, and CSV exports while making the tradeoffs across extendible hashing, a simple linear-probing baseline, cuckoo hashing, and the B-tree page baseline easier to browse visually.</p>
  {suite_source_html}
  <section class="summary-grid">{summary_cards_html}</section>
  {theory_panel_html}
  <section class="scoreboard">
    <table>
      <caption>Scenario scoreboard with the headline metrics recruiters or reviewers usually compare first</caption>
      <thead>
        <tr>
          <th scope="col">Scenario</th>
          <th scope="col">Ops</th>
          <th scope="col">Final entries</th>
          <th scope="col">Ext splits / merges</th>
          <th scope="col">Ext depth / slots</th>
          <th scope="col">Linear avg / max probe</th>
          <th scope="col">Linear get hit / miss avg</th>
          <th scope="col">Cuckoo rehash / displacements</th>
          <th scope="col">B-tree height / nodes</th>
          <th scope="col">B-tree bytes</th>
        </tr>
      </thead>
      <tbody>{scoreboard_rows}</tbody>
    </table>
  </section>
  <section class="scenario-stack">{''.join(scenario_sections)}</section>
</main>
</body>
</html>
'''



def resolve_chrome_binary(preferred: str | Path | None = None) -> str:
    candidates: list[str] = []
    if preferred is not None:
        candidates.append(str(preferred))
    candidates.extend(["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"])
    for candidate in candidates:
        candidate_path = Path(candidate).expanduser()
        if candidate_path.is_absolute() and candidate_path.exists():
            return str(candidate_path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        "Could not find a Chrome/Chromium binary for PNG capture. Pass --chrome-binary or install google-chrome/chromium."
    )


def default_benchmark_png_height(summary: dict[str, Any], width: int) -> int:
    normalized_width = max(960, width)
    scenario_count = max(1, int(summary["scenario_count"]))
    if normalized_width >= 1320:
        per_scenario_height = 980
    elif normalized_width >= 1080:
        per_scenario_height = 1180
    else:
        per_scenario_height = 1620
    estimated_height = 1500 + (scenario_count * per_scenario_height)
    return max(1800, min(estimated_height, 7200))


def default_visualization_png_height(step_count: int, width: int) -> int:
    normalized_width = max(960, width)
    effective_steps = max(1, step_count)
    if normalized_width >= 1320:
        per_step_height = 360
    elif normalized_width >= 1080:
        per_step_height = 460
    else:
        per_step_height = 620
    estimated_height = 1400 + (effective_steps * per_step_height)
    return max(1800, min(estimated_height, 9600))


def measure_html_document_height(
    html_output_path: str | Path,
    *,
    capture_ms: int = 1500,
    chrome_binary: str | Path | None = None,
) -> int | None:
    html_path = Path(html_output_path)
    if not html_path.exists():
        return None
    html_text = html_path.read_text(encoding="utf-8")
    marker_id = "html-png-scroll-height"
    marker_script = (
        "<script>\n"
        'window.addEventListener("load", () => {\n'
        '  const marker = document.createElement("pre");\n'
        f'  marker.id = "{marker_id}";\n'
        '  marker.textContent = JSON.stringify({\n'
        '    bodyScrollHeight: document.body.scrollHeight,\n'
        '    docScrollHeight: document.documentElement.scrollHeight,\n'
        '    bodyClientHeight: document.body.clientHeight,\n'
        '    docClientHeight: document.documentElement.clientHeight,\n'
        '  });\n'
        '  document.body.appendChild(marker);\n'
        '});\n'
        "</script>\n"
    )
    instrumented_html = html_text.replace("</body>", marker_script + "</body>") if "</body>" in html_text else html_text + marker_script
    with tempfile.TemporaryDirectory() as tmp_dir:
        instrumented_path = Path(tmp_dir) / "html-png-height-probe.html"
        instrumented_path.write_text(instrumented_html, encoding="utf-8")
        command = [
            resolve_chrome_binary(chrome_binary),
            "--headless",
            "--disable-gpu",
            f"--virtual-time-budget={max(0, capture_ms)}",
            "--dump-dom",
            instrumented_path.resolve().as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    match = re.search(rf'<pre id="{marker_id}">([^<]+)</pre>', result.stdout)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    height_candidates = [payload.get("docScrollHeight"), payload.get("bodyScrollHeight"), payload.get("bodyClientHeight")]
    numeric_heights = [int(value) for value in height_candidates if isinstance(value, (int, float))]
    return max(numeric_heights) if numeric_heights else None


def build_html_png_command(
    html_output_path: str | Path,
    png_output_path: str | Path,
    *,
    width: int,
    height: int,
    capture_ms: int,
    chrome_binary: str | Path | None = None,
) -> list[str]:
    resolved_html = Path(html_output_path).resolve()
    resolved_png = Path(png_output_path).resolve()
    return [
        resolve_chrome_binary(chrome_binary),
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={capture_ms}",
        f"--screenshot={resolved_png}",
        resolved_html.as_uri(),
    ]


def build_benchmark_png_command(
    html_output_path: str | Path,
    png_output_path: str | Path,
    *,
    width: int,
    height: int,
    capture_ms: int,
    chrome_binary: str | Path | None = None,
) -> list[str]:
    return build_html_png_command(
        html_output_path,
        png_output_path,
        width=width,
        height=height,
        capture_ms=capture_ms,
        chrome_binary=chrome_binary,
    )


def build_visualization_png_command(
    html_output_path: str | Path,
    png_output_path: str | Path,
    *,
    width: int,
    height: int,
    capture_ms: int,
    chrome_binary: str | Path | None = None,
) -> list[str]:
    return build_html_png_command(
        html_output_path,
        png_output_path,
        width=width,
        height=height,
        capture_ms=capture_ms,
        chrome_binary=chrome_binary,
    )


def render_benchmark_png(
    html_output_path: str | Path,
    png_output_path: str | Path,
    summary: dict[str, Any],
    *,
    width: int = 1440,
    height: int | None = None,
    capture_ms: int = 1500,
    chrome_binary: str | Path | None = None,
) -> Path:
    html_path = Path(html_output_path)
    if not html_path.exists():
        raise RuntimeError(f"HTML dashboard not found for PNG capture: {html_path}")
    png_path = Path(png_output_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    effective_width = max(960, width)
    measured_height = None
    if height is None:
        measured_height = measure_html_document_height(
            html_path,
            capture_ms=max(0, capture_ms),
            chrome_binary=chrome_binary,
        )
    heuristic_height = default_benchmark_png_height(summary, effective_width)
    effective_height = height if height is not None else max(heuristic_height, (measured_height or 0) + 120)
    command = build_benchmark_png_command(
        html_path,
        png_path,
        width=effective_width,
        height=max(1200, effective_height),
        capture_ms=max(0, capture_ms),
        chrome_binary=chrome_binary,
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Chrome headless error"
        raise RuntimeError(f"PNG capture failed: {detail}")
    if not png_path.exists():
        raise RuntimeError(f"PNG capture did not create the expected output file: {png_path}")
    return png_path


def render_visualization_png(
    html_output_path: str | Path,
    png_output_path: str | Path,
    *,
    step_count: int,
    width: int = 1440,
    height: int | None = None,
    capture_ms: int = 1500,
    chrome_binary: str | Path | None = None,
) -> Path:
    html_path = Path(html_output_path)
    if not html_path.exists():
        raise RuntimeError(f"HTML visualization not found for PNG capture: {html_path}")
    png_path = Path(png_output_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    effective_width = max(960, width)
    measured_height = None
    if height is None:
        measured_height = measure_html_document_height(
            html_path,
            capture_ms=max(0, capture_ms),
            chrome_binary=chrome_binary,
        )
    heuristic_height = default_visualization_png_height(step_count, effective_width)
    effective_height = height if height is not None else max(heuristic_height, (measured_height or 0) + 120)
    command = build_visualization_png_command(
        html_path,
        png_path,
        width=effective_width,
        height=max(1200, effective_height),
        capture_ms=max(0, capture_ms),
        chrome_binary=chrome_binary,
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Chrome headless error"
        raise RuntimeError(f"Visualization PNG capture failed: {detail}")
    if not png_path.exists():
        raise RuntimeError(f"Visualization PNG capture did not create the expected output file: {png_path}")
    return png_path


def save_benchmark_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
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
                "linear_initial_capacity",
                "linear_max_load_factor",
                "linear_max_tombstone_ratio",
                "linear_final_capacity",
                "linear_final_load_factor",
                "linear_occupied_load_factor",
                "linear_average_occupied_load_factor",
                "linear_peak_occupied_load_factor",
                "linear_theory_expected_hit_probe_count",
                "linear_theory_observed_hit_probe_count",
                "linear_theory_hit_delta",
                "linear_theory_expected_miss_probe_count",
                "linear_theory_observed_miss_probe_count",
                "linear_theory_miss_delta",
                "linear_tombstone_count",
                "linear_resize_count",
                "linear_average_probe_count",
                "linear_max_probe_count",
                "linear_rebuild_probe_count",
                "linear_put_phase_count",
                "linear_put_phase_average_probe_count",
                "linear_put_phase_p50_probe_count",
                "linear_put_phase_p95_probe_count",
                "linear_put_phase_max_probe_count",
                "linear_get_phase_count",
                "linear_get_phase_average_probe_count",
                "linear_get_phase_p50_probe_count",
                "linear_get_phase_p95_probe_count",
                "linear_get_phase_max_probe_count",
                "linear_delete_phase_count",
                "linear_delete_phase_average_probe_count",
                "linear_delete_phase_p50_probe_count",
                "linear_delete_phase_p95_probe_count",
                "linear_delete_phase_max_probe_count",
                "linear_get_hit_count",
                "linear_get_hit_average_probe_count",
                "linear_get_hit_p50_probe_count",
                "linear_get_hit_p95_probe_count",
                "linear_get_hit_max_probe_count",
                "linear_get_miss_count",
                "linear_get_miss_average_probe_count",
                "linear_get_miss_p50_probe_count",
                "linear_get_miss_p95_probe_count",
                "linear_get_miss_max_probe_count",
                "cuckoo_average_rehash_count",
                "cuckoo_average_displacement_count",
                "cuckoo_average_load_factor",
                "cuckoo_final_capacity_min",
                "cuckoo_final_capacity_max",
                "cuckoo_empty_slots_min",
                "cuckoo_empty_slots_max",
                "btree_minimum_degree",
                "btree_page_size",
                "btree_value_bytes",
                "btree_final_height",
                "btree_peak_height",
                "btree_final_node_count",
                "btree_peak_node_count",
                "btree_root_keys",
                "btree_page_padding_bytes",
                "btree_paged_file_bytes",
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
                    "linear_initial_capacity": row["linear"]["initial_capacity"],
                    "linear_max_load_factor": row["linear"]["max_load_factor"],
                    "linear_max_tombstone_ratio": row["linear"]["max_tombstone_ratio"],
                    "linear_final_capacity": row["linear"]["final_capacity"],
                    "linear_final_load_factor": row["linear"]["final_load_factor"],
                    "linear_occupied_load_factor": row["linear"]["occupied_load_factor"],
                    "linear_average_occupied_load_factor": row["linear"]["average_occupied_load_factor"],
                    "linear_peak_occupied_load_factor": row["linear"]["peak_occupied_load_factor"],
                    "linear_theory_expected_hit_probe_count": row["linear"]["theory_overlay"]["average_occupied_reference"]["successful_average_probe_count"],
                    "linear_theory_observed_hit_probe_count": row["linear"]["theory_overlay"]["observed"]["successful_average_probe_count"],
                    "linear_theory_hit_delta": row["linear"]["theory_overlay"]["delta_vs_average_reference"]["successful_average_probe_count"],
                    "linear_theory_expected_miss_probe_count": row["linear"]["theory_overlay"]["average_occupied_reference"]["unsuccessful_average_probe_count"],
                    "linear_theory_observed_miss_probe_count": row["linear"]["theory_overlay"]["observed"]["unsuccessful_average_probe_count"],
                    "linear_theory_miss_delta": row["linear"]["theory_overlay"]["delta_vs_average_reference"]["unsuccessful_average_probe_count"],
                    "linear_tombstone_count": row["linear"]["tombstone_count"],
                    "linear_resize_count": row["linear"]["resize_count"],
                    "linear_average_probe_count": row["linear"]["average_probe_count"],
                    "linear_max_probe_count": row["linear"]["max_probe_count"],
                    "linear_rebuild_probe_count": row["linear"]["rebuild_probe_count"],
                    "linear_put_phase_count": row["linear"]["phase_probe_breakdown"]["puts"]["count"],
                    "linear_put_phase_average_probe_count": row["linear"]["phase_probe_breakdown"]["puts"]["average_probe_count"],
                    "linear_put_phase_p50_probe_count": row["linear"]["phase_probe_breakdown"]["puts"]["p50_probe_count"],
                    "linear_put_phase_p95_probe_count": row["linear"]["phase_probe_breakdown"]["puts"]["p95_probe_count"],
                    "linear_put_phase_max_probe_count": row["linear"]["phase_probe_breakdown"]["puts"]["max_probe_count"],
                    "linear_get_phase_count": row["linear"]["phase_probe_breakdown"]["gets"]["count"],
                    "linear_get_phase_average_probe_count": row["linear"]["phase_probe_breakdown"]["gets"]["average_probe_count"],
                    "linear_get_phase_p50_probe_count": row["linear"]["phase_probe_breakdown"]["gets"]["p50_probe_count"],
                    "linear_get_phase_p95_probe_count": row["linear"]["phase_probe_breakdown"]["gets"]["p95_probe_count"],
                    "linear_get_phase_max_probe_count": row["linear"]["phase_probe_breakdown"]["gets"]["max_probe_count"],
                    "linear_delete_phase_count": row["linear"]["phase_probe_breakdown"]["deletes"]["count"],
                    "linear_delete_phase_average_probe_count": row["linear"]["phase_probe_breakdown"]["deletes"]["average_probe_count"],
                    "linear_delete_phase_p50_probe_count": row["linear"]["phase_probe_breakdown"]["deletes"]["p50_probe_count"],
                    "linear_delete_phase_p95_probe_count": row["linear"]["phase_probe_breakdown"]["deletes"]["p95_probe_count"],
                    "linear_delete_phase_max_probe_count": row["linear"]["phase_probe_breakdown"]["deletes"]["max_probe_count"],
                    "linear_get_hit_count": row["linear"]["lookup_probe_breakdown"]["successful"]["count"],
                    "linear_get_hit_average_probe_count": row["linear"]["lookup_probe_breakdown"]["successful"]["average_probe_count"],
                    "linear_get_hit_p50_probe_count": row["linear"]["lookup_probe_breakdown"]["successful"]["p50_probe_count"],
                    "linear_get_hit_p95_probe_count": row["linear"]["lookup_probe_breakdown"]["successful"]["p95_probe_count"],
                    "linear_get_hit_max_probe_count": row["linear"]["lookup_probe_breakdown"]["successful"]["max_probe_count"],
                    "linear_get_miss_count": row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["count"],
                    "linear_get_miss_average_probe_count": row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["average_probe_count"],
                    "linear_get_miss_p50_probe_count": row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["p50_probe_count"],
                    "linear_get_miss_p95_probe_count": row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["p95_probe_count"],
                    "linear_get_miss_max_probe_count": row["linear"]["lookup_probe_breakdown"]["unsuccessful"]["max_probe_count"],
                    "cuckoo_average_rehash_count": row["cuckoo"]["average_rehash_count"],
                    "cuckoo_average_displacement_count": row["cuckoo"]["average_displacement_count"],
                    "cuckoo_average_load_factor": row["cuckoo"]["average_load_factor"],
                    "cuckoo_final_capacity_min": row["cuckoo"]["final_capacity_range"][0],
                    "cuckoo_final_capacity_max": row["cuckoo"]["final_capacity_range"][1],
                    "cuckoo_empty_slots_min": row["cuckoo"]["empty_slot_range"][0],
                    "cuckoo_empty_slots_max": row["cuckoo"]["empty_slot_range"][1],
                    "btree_minimum_degree": row["btree"]["minimum_degree"],
                    "btree_page_size": row["btree"]["page_size"],
                    "btree_value_bytes": row["btree"]["value_bytes"],
                    "btree_final_height": row["btree"]["final_height"],
                    "btree_peak_height": row["btree"]["peak_height"],
                    "btree_final_node_count": row["btree"]["final_node_count"],
                    "btree_peak_node_count": row["btree"]["peak_node_count"],
                    "btree_root_keys": row["btree"]["root_keys"],
                    "btree_page_padding_bytes": row["btree"]["page_padding_bytes"],
                    "btree_paged_file_bytes": row["btree"]["paged_file_bytes"],
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
        help="compare extendible hashing against linear probing, the repo's cuckoo hashing, and the B-tree lab across mixed workloads",
    )
    benchmark_parser.add_argument("--input", required=True, type=Path, help="benchmark suite JSON file")
    benchmark_parser.add_argument("--json-out", type=Path, help="optional JSON summary output")
    benchmark_parser.add_argument("--markdown-out", type=Path, help="optional Markdown report output")
    benchmark_parser.add_argument("--html-out", type=Path, help="optional self-contained HTML dashboard output")
    benchmark_parser.add_argument("--png-out", type=Path, help="optional PNG screenshot captured from the HTML dashboard")
    benchmark_parser.add_argument("--png-width", type=int, default=1440, help="viewport width in pixels for PNG capture (default: 1440)")
    benchmark_parser.add_argument("--png-height", type=int, help="optional viewport height override for PNG capture; defaults to an auto-sized dashboard height")
    benchmark_parser.add_argument("--png-capture-ms", type=int, default=1500, help="virtual time budget in milliseconds before capturing the PNG screenshot")
    benchmark_parser.add_argument("--chrome-binary", type=Path, help="optional Chrome/Chromium binary for PNG capture")
    benchmark_parser.add_argument("--csv-out", type=Path, help="optional CSV summary output")
    benchmark_parser.add_argument(
        "--title",
        help="optional title override for JSON/stdout and any saved report/dashboard outputs",
    )

    visualize_parser = subparsers.add_parser(
        "visualize",
        help="render split-sequence visualization artifacts for a workload",
    )
    visualize_parser.add_argument("--input", required=True, type=Path, help="workload JSON file")
    visualize_parser.add_argument("--svg-out", type=Path, help="optional self-contained SVG output")
    visualize_parser.add_argument("--html-out", type=Path, help="optional self-contained HTML output")
    visualize_parser.add_argument("--png-out", type=Path, help="optional PNG screenshot captured from the generated HTML visualization")
    visualize_parser.add_argument("--png-width", type=int, default=1440, help="viewport width in pixels for visualization PNG capture (default: 1440)")
    visualize_parser.add_argument("--png-height", type=int, help="optional viewport height override for visualization PNG capture; defaults to an auto-sized visualization height")
    visualize_parser.add_argument("--png-capture-ms", type=int, default=1500, help="virtual time budget in milliseconds before capturing the visualization PNG screenshot")
    visualize_parser.add_argument("--chrome-binary", type=Path, help="optional Chrome/Chromium binary for visualization PNG capture")
    visualize_parser.add_argument(
        "--thumbnail-svg-out",
        type=Path,
        help="optional compact SVG lifecycle strip for README thumbnails or slides",
    )
    visualize_parser.add_argument(
        "--title",
        default="Extendible hashing split and aliasing trace",
        help="title to use for visualization artifacts",
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
    if args.title:
        summary = {**summary, "title": args.title}
    if args.json_out:
        save_json(args.json_out, summary)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(
            render_benchmark_markdown_report(summary["title"], summary, suite_source=str(args.input)) + "\n",
            encoding="utf-8",
        )
    if args.html_out:
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(
            render_benchmark_dashboard_html(summary["title"], summary, suite_source=str(args.input)) + "\n",
            encoding="utf-8",
        )
    if args.png_out:
        render_benchmark_png(
            args.html_out,
            args.png_out,
            summary,
            width=args.png_width,
            height=args.png_height,
            capture_ms=args.png_capture_ms,
            chrome_binary=args.chrome_binary,
        )
    if args.csv_out:
        save_benchmark_csv(args.csv_out, summary["results"])
    print(json.dumps({"input": str(args.input), "png_out": str(args.png_out) if args.png_out else None, **summary}, indent=2))
    return 0


def command_visualize(args: argparse.Namespace) -> int:
    if not args.svg_out and not args.html_out and not args.png_out and not args.thumbnail_svg_out:
        raise ValueError("visualize requires --svg-out, --html-out, --png-out, and/or --thumbnail-svg-out")
    workload = load_json(args.input)
    result = run_workload(workload)
    if args.svg_out:
        args.svg_out.parent.mkdir(parents=True, exist_ok=True)
        args.svg_out.write_text(
            render_visualization_svg(args.title, result.table, result.history, source_label=str(args.input)) + "\n",
            encoding="utf-8",
        )
    if args.html_out:
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(
            render_visualization_html(args.title, result.table, result.history, source_label=str(args.input)) + "\n",
            encoding="utf-8",
        )
    if args.png_out:
        render_visualization_png(
            args.html_out,
            args.png_out,
            step_count=len(result.history),
            width=args.png_width,
            height=args.png_height,
            capture_ms=args.png_capture_ms,
            chrome_binary=args.chrome_binary,
        )
    if args.thumbnail_svg_out:
        args.thumbnail_svg_out.parent.mkdir(parents=True, exist_ok=True)
        args.thumbnail_svg_out.write_text(
            render_visualization_thumbnail_strip_svg(args.title, result.table, result.history, source_label=str(args.input)) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "input": str(args.input),
                "steps": len(result.history),
                "svg_out": str(args.svg_out) if args.svg_out else None,
                "html_out": str(args.html_out) if args.html_out else None,
                "png_out": str(args.png_out) if args.png_out else None,
                "thumbnail_svg_out": str(args.thumbnail_svg_out) if args.thumbnail_svg_out else None,
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "benchmark" and args.png_out is not None and args.html_out is None:
        parser.error("--png-out requires --html-out because the PNG is captured from the generated HTML dashboard")
    if args.command == "visualize" and args.png_out is not None and args.html_out is None:
        parser.error("--png-out requires --html-out because the PNG is captured from the generated HTML visualization")
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
    if args.command == "visualize":
        return command_visualize(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
