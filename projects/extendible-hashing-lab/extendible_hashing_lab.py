from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SnapshotError(ValueError):
    """Raised when a persisted snapshot is malformed."""


class WorkloadError(ValueError):
    """Raised when a workload file is malformed."""


FNV_OFFSET_BASIS_64 = 14695981039346656037
FNV_PRIME_64 = 1099511628211


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


class ExtendibleHashTable:
    def __init__(self, bucket_capacity: int = 2) -> None:
        if bucket_capacity < 1:
            raise ValueError("bucket_capacity must be at least 1")
        self.bucket_capacity = bucket_capacity
        self.global_depth = 0
        self.directory: list[int] = [0]
        self.buckets: dict[int, Bucket] = {0: Bucket(bucket_id=0, local_depth=0)}
        self.next_bucket_id = 1

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

    def _split_bucket(self, bucket_id: int) -> None:
        bucket = self.buckets[bucket_id]
        old_local_depth = bucket.local_depth
        if old_local_depth == self.global_depth:
            self.directory.extend(self.directory)
            self.global_depth += 1

        bucket.local_depth += 1
        new_bucket = Bucket(bucket_id=self.next_bucket_id, local_depth=bucket.local_depth)
        self.buckets[new_bucket.bucket_id] = new_bucket
        self.next_bucket_id += 1

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

    normalized_ops: list[dict[str, str]] = []
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
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
