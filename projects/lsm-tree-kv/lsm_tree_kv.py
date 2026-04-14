from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TOMBSTONE = "__TOMBSTONE__"


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


class LSMTreeKV:
    def __init__(self, root: Path | str, flush_threshold: int = 8) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.flush_threshold = max(1, int(flush_threshold))
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
        path = self.tables_dir / f"sstable-{self._next_seq():020d}.json"
        payload = {
            "count": len(ordered),
            "min_key": ordered[0].key if ordered else None,
            "max_key": ordered[-1].key if ordered else None,
            "entries": [entry.to_json() for entry in ordered],
        }
        self._write_atomic_json(path, payload)
        return path

    def _load_sstable(self, path: Path) -> dict[str, Entry]:
        payload = json.loads(path.read_text())
        return {item["key"]: Entry.from_json(item) for item in payload.get("entries", [])}

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
        tombstoned = False
        for path in self._sstable_paths():
            table = self._load_sstable(path)
            if key not in table:
                continue
            entry = table[key]
            if entry.deleted:
                tombstoned = True
                break
            return entry
        if tombstoned:
            return None
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
        return {
            "live_keys": live_count,
            "memtable_entries": len(self.memtable),
            "sstable_count": len(sstable_paths),
            "wal_bytes": self.wal_path.stat().st_size if self.wal_path.exists() else 0,
            "sstable_bytes": sum(path.stat().st_size for path in sstable_paths),
            "next_seq": self._seq + 1,
        }

    def _maybe_flush(self) -> None:
        if len(self.memtable) >= self.flush_threshold:
            self.flush()

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or any(ch.isspace() for ch in key):
            raise ValueError("keys must be non-empty and contain no whitespace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny LSM-tree inspired key-value store")
    parser.add_argument("--dir", required=True, help="storage directory")
    parser.add_argument("--flush-threshold", type=int, default=8, help="flush memtable after N distinct dirty keys")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="set a key")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get", help="get a key")
    get_parser.add_argument("key")

    delete_parser = subparsers.add_parser("delete", help="delete a key")
    delete_parser.add_argument("key")

    subparsers.add_parser("list", help="list live key/value pairs")
    subparsers.add_parser("stats", help="show store stats")
    subparsers.add_parser("flush", help="force a memtable flush")
    subparsers.add_parser("compact", help="merge SSTables into one table")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = LSMTreeKV(args.dir, flush_threshold=args.flush_threshold)

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
