from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class Record:
    seq: int
    op: str
    key: str
    value: str | None
    ts: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "op": self.op,
            "key": self.key,
            "value": self.value,
            "ts": self.ts,
        }


class WALKVStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.log_path = self.directory / "wal.log"
        self.snapshot_path = self.directory / "snapshot.json"
        self.state: dict[str, str] = {}
        self.history_by_key: dict[str, list[Record]] = {}
        self.next_seq = 1
        self.snapshot_seq = 0
        self._load()

    def set(self, key: str, value: str) -> Record:
        self._validate_key(key)
        record = self._append_record("set", key, value)
        self.state[key] = value
        self.history_by_key.setdefault(key, []).append(record)
        return record

    def delete(self, key: str) -> Record:
        self._validate_key(key)
        record = self._append_record("delete", key, None)
        self.state.pop(key, None)
        self.history_by_key.setdefault(key, []).append(record)
        return record

    def get(self, key: str) -> str | None:
        self._validate_key(key)
        return self.state.get(key)

    def items(self) -> dict[str, str]:
        return dict(sorted(self.state.items()))

    def history(self, key: str) -> list[dict[str, Any]]:
        self._validate_key(key)
        return [record.to_dict() for record in self.history_by_key.get(key, [])]

    def stats(self) -> dict[str, Any]:
        wal_records = sum(1 for _ in self._iter_log_records()) if self.log_path.exists() else 0
        return {
            "keys": len(self.state),
            "snapshot_seq": self.snapshot_seq,
            "next_seq": self.next_seq,
            "wal_records": wal_records,
            "wal_bytes": self.log_path.stat().st_size if self.log_path.exists() else 0,
            "snapshot_bytes": self.snapshot_path.stat().st_size if self.snapshot_path.exists() else 0,
        }

    def checkpoint(self) -> dict[str, Any]:
        snapshot = {
            "last_seq": self.next_seq - 1,
            "state": self.items(),
        }
        self._atomic_write(self.snapshot_path, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
        self._atomic_write(self.log_path, "")
        self.snapshot_seq = snapshot["last_seq"]
        self.history_by_key = {}
        return {
            "snapshot_path": str(self.snapshot_path),
            "last_seq": self.snapshot_seq,
            "keys": len(snapshot["state"]),
        }

    def _load(self) -> None:
        if self.snapshot_path.exists():
            snapshot = json.loads(self.snapshot_path.read_text())
            self.state = {str(key): str(value) for key, value in snapshot.get("state", {}).items()}
            self.snapshot_seq = int(snapshot.get("last_seq", 0))
            self.next_seq = self.snapshot_seq + 1
        if self.log_path.exists():
            for payload in self._iter_log_records():
                record = self._record_from_dict(payload)
                self._apply(record)
                self.next_seq = max(self.next_seq, record.seq + 1)

    def _apply(self, record: Record) -> None:
        if record.op == "set":
            assert record.value is not None
            self.state[record.key] = record.value
        elif record.op == "delete":
            self.state.pop(record.key, None)
        else:
            raise ValueError(f"unsupported op: {record.op}")
        self.history_by_key.setdefault(record.key, []).append(record)

    def _append_record(self, op: str, key: str, value: str | None) -> Record:
        record = Record(
            seq=self.next_seq,
            op=op,
            key=key,
            value=value,
            ts=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        self.next_seq += 1
        return record

    def _iter_log_records(self):
        with self.log_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid WAL record on line {line_number}") from exc

    @staticmethod
    def _record_from_dict(payload: dict[str, Any]) -> Record:
        op = str(payload["op"])
        if op not in {"set", "delete"}:
            raise ValueError(f"unsupported op: {op}")
        value = payload.get("value")
        if op == "set" and not isinstance(value, str):
            raise ValueError("set records require a string value")
        if op == "delete":
            value = None
        return Record(
            seq=int(payload["seq"]),
            op=op,
            key=str(payload["key"]),
            value=value,
            ts=str(payload["ts"]),
        )

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or any(ch.isspace() for ch in key):
            raise ValueError("key must be non-empty and contain no whitespace")

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WAL-backed key-value store lab")
    parser.add_argument("--dir", default="data", help="storage directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="set a key")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get", help="get a key")
    get_parser.add_argument("key")

    delete_parser = subparsers.add_parser("delete", help="delete a key")
    delete_parser.add_argument("key")

    list_parser = subparsers.add_parser("list", help="list current keys")
    list_parser.add_argument("--pretty", action="store_true")

    history_parser = subparsers.add_parser("history", help="show key history")
    history_parser.add_argument("key")

    subparsers.add_parser("stats", help="show store stats")
    subparsers.add_parser("checkpoint", help="compact state into a snapshot")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = WALKVStore(args.dir)

    if args.command == "set":
        result = {"record": store.set(args.key, args.value).to_dict(), "value": store.get(args.key)}
    elif args.command == "get":
        value = store.get(args.key)
        result = {"key": args.key, "found": value is not None, "value": value}
    elif args.command == "delete":
        existed = store.get(args.key) is not None
        result = {"record": store.delete(args.key).to_dict(), "existed": existed, "found": store.get(args.key) is not None}
    elif args.command == "list":
        result = store.items() if args.pretty else {"items": store.items()}
    elif args.command == "history":
        result = {"key": args.key, "history": store.history(args.key)}
    elif args.command == "stats":
        result = store.stats()
    else:
        result = store.checkpoint()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
