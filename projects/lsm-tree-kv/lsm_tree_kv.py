from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TOMBSTONE = "__TOMBSTONE__"
DEFAULT_BLOOM_BITS_PER_KEY = 10
MIN_BLOOM_FILTER_BITS = 64
DEFAULT_BENCHMARK_BITS_PER_KEY = [4, 8, 10, 12]


@dataclass(frozen=True)
class Entry:
    key: str
    value: str
    seq: int
    deleted: bool = False

    def to_json(self) -> dict[str, object]:
        return {
            "key": self.key,
            "value": None if self.deleted else self.value,
            "seq": self.seq,
            "deleted": self.deleted,
        }

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> "Entry":
        deleted = bool(payload["deleted"])
        value = "" if deleted else str(payload["value"])
        return cls(key=str(payload["key"]), value=value, seq=int(payload["seq"]), deleted=deleted)


class BloomFilter:
    def __init__(self, bit_count: int, hash_count: int, bits: int = 0) -> None:
        self.bit_count = max(MIN_BLOOM_FILTER_BITS, int(bit_count))
        self.hash_count = max(1, int(hash_count))
        self.bits = int(bits)

    @classmethod
    def for_capacity(cls, item_count: int, bits_per_key: int = DEFAULT_BLOOM_BITS_PER_KEY) -> "BloomFilter":
        item_count = max(1, int(item_count))
        bit_count = max(MIN_BLOOM_FILTER_BITS, item_count * max(1, int(bits_per_key)))
        hash_count = max(1, round((bit_count / item_count) * math.log(2)))
        return cls(bit_count=bit_count, hash_count=hash_count)

    @classmethod
    def from_json(cls, payload: dict[str, object] | None) -> "BloomFilter | None":
        if not payload:
            return None
        return cls(
            bit_count=int(payload["bit_count"]),
            hash_count=int(payload["hash_count"]),
            bits=int(payload.get("bits", 0)),
        )

    def add(self, key: str) -> None:
        for position in self._positions(key):
            self.bits |= 1 << position

    def might_contain(self, key: str) -> bool:
        for position in self._positions(key):
            if not (self.bits & (1 << position)):
                return False
        return True

    def estimated_false_positive_rate(self, item_count: int) -> float:
        item_count = max(1, int(item_count))
        return (1 - math.exp((-self.hash_count * item_count) / self.bit_count)) ** self.hash_count

    def to_json(self) -> dict[str, int]:
        return {
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "bits": self.bits,
        }

    def _positions(self, key: str) -> list[int]:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        first = int.from_bytes(digest[:8], "big")
        second = int.from_bytes(digest[8:16], "big") or 1
        return [((first + index * second) % self.bit_count) for index in range(self.hash_count)]


class LSMTreeKV:
    def __init__(self, root: Path | str, flush_threshold: int = 8, bloom_bits_per_key: int = DEFAULT_BLOOM_BITS_PER_KEY) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.flush_threshold = max(1, int(flush_threshold))
        self.bloom_bits_per_key = max(1, int(bloom_bits_per_key))
        self.wal_path = self.root / "wal.jsonl"
        self.meta_path = self.root / "meta.json"
        self.tables_dir = self.root / "sstables"
        self.tables_dir.mkdir(exist_ok=True)
        self._seq = 0
        self.memtable: dict[str, Entry] = {}
        self._load()

    def _load(self) -> None:
        self._load_meta()
        self._replay_wal()

    def _load_meta(self) -> None:
        if self.meta_path.exists():
            payload = json.loads(self.meta_path.read_text())
            self._seq = int(payload.get("next_seq", 1)) - 1
        else:
            self._write_meta()

    def _write_meta(self) -> None:
        self.meta_path.write_text(json.dumps({"next_seq": self._seq + 1}, indent=2) + "\n")

    def _replay_wal(self) -> None:
        if not self.wal_path.exists():
            return
        with self.wal_path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entry = Entry.from_json(json.loads(line))
                self.memtable[entry.key] = entry
                self._seq = max(self._seq, entry.seq)
        self._write_meta()

    def _next_seq(self) -> int:
        self._seq += 1
        self._write_meta()
        return self._seq

    def _append_wal(self, entry: Entry) -> None:
        with self.wal_path.open("a") as handle:
            handle.write(json.dumps(entry.to_json(), sort_keys=True) + "\n")

    def _sstable_paths(self) -> list[Path]:
        return sorted(self.tables_dir.glob("sstable-*.json"), reverse=True)

    def _write_atomic_json(self, path: Path, payload: object) -> None:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(path)

    def _write_sstable(self, entries: Iterable[Entry]) -> Path:
        ordered = sorted(entries, key=lambda item: item.key)
        bloom_filter = BloomFilter.for_capacity(len(ordered), bits_per_key=self.bloom_bits_per_key)
        for entry in ordered:
            bloom_filter.add(entry.key)
        path = self.tables_dir / f"sstable-{self._next_seq():020d}.json"
        payload = {
            "count": len(ordered),
            "min_key": ordered[0].key if ordered else None,
            "max_key": ordered[-1].key if ordered else None,
            "bloom_filter": bloom_filter.to_json(),
            "entries": [entry.to_json() for entry in ordered],
        }
        self._write_atomic_json(path, payload)
        return path

    def _read_sstable_payload(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text())

    def _load_sstable(self, path: Path) -> dict[str, Entry]:
        payload = self._read_sstable_payload(path)
        return {item["key"]: Entry.from_json(item) for item in payload.get("entries", [])}

    def _sstable_might_contain_key(self, path: Path, key: str) -> bool:
        payload = self._read_sstable_payload(path)
        minimum = payload.get("min_key")
        maximum = payload.get("max_key")
        if minimum is not None and key < str(minimum):
            return False
        if maximum is not None and key > str(maximum):
            return False
        bloom_filter = BloomFilter.from_json(payload.get("bloom_filter"))
        if bloom_filter is None:
            return True
        return bloom_filter.might_contain(key)

    def set(self, key: str, value: str) -> Entry:
        self._validate_key(key)
        entry = Entry(key=key, value=value, seq=self._next_seq(), deleted=False)
        self._append_wal(entry)
        self.memtable[key] = entry
        self._maybe_flush()
        return entry

    def delete(self, key: str) -> tuple[Entry, bool]:
        self._validate_key(key)
        existed = self.get(key) is not None
        entry = Entry(key=key, value="", seq=self._next_seq(), deleted=True)
        self._append_wal(entry)
        self.memtable[key] = entry
        self._maybe_flush()
        return entry, existed

    def get(self, key: str) -> Entry | None:
        self._validate_key(key)
        if key in self.memtable:
            entry = self.memtable[key]
            return None if entry.deleted else entry
        for path in self._sstable_paths():
            if not self._sstable_might_contain_key(path, key):
                continue
            table = self._load_sstable(path)
            if key not in table:
                continue
            entry = table[key]
            return None if entry.deleted else entry
        return None

    def list_items(self) -> list[Entry]:
        merged: dict[str, Entry] = {}
        for path in reversed(self._sstable_paths()):
            merged.update(self._load_sstable(path))
        merged.update(self.memtable)
        return [entry for entry in sorted(merged.values(), key=lambda item: item.key) if not entry.deleted]

    def flush(self) -> Path | None:
        if not self.memtable:
            return None
        path = self._write_sstable(self.memtable.values())
        self.memtable = {}
        self.wal_path.write_text("")
        return path

    def compact(self) -> Path | None:
        items = self._merged_latest_entries()
        if not items:
            for path in self._sstable_paths():
                path.unlink()
            self.wal_path.write_text("")
            self.memtable = {}
            return None
        path = self._write_sstable(items.values())
        for old in self._sstable_paths():
            if old != path:
                old.unlink()
        self.memtable = {}
        self.wal_path.write_text("")
        return path

    def _merged_latest_entries(self) -> dict[str, Entry]:
        merged: dict[str, Entry] = {}
        for path in reversed(self._sstable_paths()):
            merged.update(self._load_sstable(path))
        merged.update(self.memtable)
        return {key: entry for key, entry in merged.items() if not entry.deleted}

    def stats(self) -> dict[str, int]:
        live_count = len(self.list_items())
        sstable_paths = self._sstable_paths()
        bloom_filter_count = 0
        bloom_filter_bits = 0
        for path in sstable_paths:
            bloom_filter = BloomFilter.from_json(self._read_sstable_payload(path).get("bloom_filter"))
            if bloom_filter is None:
                continue
            bloom_filter_count += 1
            bloom_filter_bits += bloom_filter.bit_count
        return {
            "live_keys": live_count,
            "memtable_entries": len(self.memtable),
            "sstable_count": len(sstable_paths),
            "wal_bytes": self.wal_path.stat().st_size if self.wal_path.exists() else 0,
            "sstable_bytes": sum(path.stat().st_size for path in sstable_paths),
            "bloom_filter_count": bloom_filter_count,
            "bloom_filter_bits": bloom_filter_bits,
            "next_seq": self._seq + 1,
        }

    def _maybe_flush(self) -> None:
        if len(self.memtable) >= self.flush_threshold:
            self.flush()

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or any(ch.isspace() for ch in key):
            raise ValueError("keys must be non-empty and contain no whitespace")


def parse_bits_per_key_options(raw: str) -> list[int]:
    values: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        value = int(chunk)
        if value < 1:
            raise ValueError("bits-per-key options must be positive integers")
        values.append(value)
    if not values:
        raise ValueError("at least one bits-per-key option is required")
    return sorted(dict.fromkeys(values))


def run_bloom_benchmark(key_count: int, miss_count: int, bits_per_key_options: Iterable[int]) -> dict[str, object]:
    key_count = max(1, int(key_count))
    miss_count = max(1, int(miss_count))
    options = [max(1, int(bits)) for bits in bits_per_key_options]
    inserted_keys = [f"key-{index:06d}" for index in range(key_count)]
    missing_keys = [f"missing-{index:06d}" for index in range(miss_count)]
    results: list[dict[str, object]] = []

    for bits_per_key in options:
        bloom_filter = BloomFilter.for_capacity(key_count, bits_per_key=bits_per_key)
        for key in inserted_keys:
            bloom_filter.add(key)
        false_positives = sum(1 for key in missing_keys if bloom_filter.might_contain(key))
        results.append(
            {
                "bits_per_key": bits_per_key,
                "hash_count": bloom_filter.hash_count,
                "filter_bits": bloom_filter.bit_count,
                "inserted_keys": key_count,
                "miss_lookups": miss_count,
                "observed_false_positives": false_positives,
                "observed_false_positive_rate": false_positives / miss_count,
                "estimated_false_positive_rate": bloom_filter.estimated_false_positive_rate(key_count),
            }
        )

    best = min(results, key=lambda item: float(item["observed_false_positive_rate"]))
    return {
        "key_count": key_count,
        "miss_lookups": miss_count,
        "results": results,
        "recommended_bits_per_key": best["bits_per_key"],
        "note": "Higher bits-per-key usually reduce false positives at the cost of more filter memory.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny LSM-tree inspired key-value store")
    parser.add_argument("--dir", required=True, help="storage directory")
    parser.add_argument("--flush-threshold", type=int, default=8, help="flush memtable after N distinct dirty keys")
    parser.add_argument(
        "--bloom-bits-per-key",
        type=int,
        default=DEFAULT_BLOOM_BITS_PER_KEY,
        help="Bloom filter density stored per SSTable",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="set a key")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get", help="get a key")
    get_parser.add_argument("key")

    delete_parser = subparsers.add_parser("delete", help="delete a key")
    delete_parser.add_argument("key")

    benchmark_parser = subparsers.add_parser("benchmark", help="compare Bloom filter false positives across densities")
    benchmark_parser.add_argument("--key-count", type=int, default=500, help="number of inserted keys to model")
    benchmark_parser.add_argument("--miss-count", type=int, default=1000, help="number of negative lookups to probe")
    benchmark_parser.add_argument(
        "--bits-per-key-options",
        default=",".join(str(value) for value in DEFAULT_BENCHMARK_BITS_PER_KEY),
        help="comma-separated Bloom filter densities to compare",
    )

    subparsers.add_parser("list", help="list live key/value pairs")
    subparsers.add_parser("stats", help="show store stats")
    subparsers.add_parser("flush", help="force a memtable flush")
    subparsers.add_parser("compact", help="merge SSTables into one table")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "benchmark":
        try:
            report = run_bloom_benchmark(
                key_count=args.key_count,
                miss_count=args.miss_count,
                bits_per_key_options=parse_bits_per_key_options(args.bits_per_key_options),
            )
        except ValueError as exc:
            print(json.dumps({"status": "error", "error": str(exc)}))
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    store = LSMTreeKV(
        args.dir,
        flush_threshold=args.flush_threshold,
        bloom_bits_per_key=args.bloom_bits_per_key,
    )

    try:
        if args.command == "set":
            entry = store.set(args.key, args.value)
            print(json.dumps({"status": "ok", "seq": entry.seq, "key": entry.key, "value": entry.value}))
            return 0
        if args.command == "get":
            entry = store.get(args.key)
            if entry is None:
                print(json.dumps({"status": "missing", "key": args.key}))
                return 1
            print(json.dumps({"status": "ok", "key": entry.key, "value": entry.value, "seq": entry.seq}))
            return 0
        if args.command == "delete":
            entry, existed = store.delete(args.key)
            print(json.dumps({"status": "ok", "key": entry.key, "seq": entry.seq, "deleted": True, "existed_before": existed}))
            return 0
        if args.command == "list":
            print(json.dumps([entry.to_json() for entry in store.list_items()], indent=2))
            return 0
        if args.command == "stats":
            print(json.dumps(store.stats(), indent=2, sort_keys=True))
            return 0
        if args.command == "flush":
            path = store.flush()
            print(json.dumps({"status": "ok", "path": None if path is None else str(path)}))
            return 0
        if args.command == "compact":
            path = store.compact()
            print(json.dumps({"status": "ok", "path": None if path is None else str(path)}))
            return 0
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
