from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Node:
    key: str | None
    value: Any = None
    forwards: list[Node | None] = field(default_factory=list)


class SkipList:
    def __init__(self, *, max_level: int = 8, probability: float = 0.5, seed: int | None = None) -> None:
        if max_level < 1:
            raise ValueError("max_level must be at least 1")
        if not 0 < probability < 1:
            raise ValueError("probability must be between 0 and 1")
        self.max_level = max_level
        self.probability = probability
        self.level = 1
        self.length = 0
        self.random = random.Random(seed)
        self.head = Node(None, None, [None] * max_level)

    def __len__(self) -> int:
        return self.length

    def _random_level(self) -> int:
        level = 1
        while level < self.max_level and self.random.random() < self.probability:
            level += 1
        return level

    def _locate_predecessors(self, key: str) -> list[Node]:
        update: list[Node] = [self.head] * self.max_level
        current = self.head
        for level in range(self.level - 1, -1, -1):
            while (next_node := current.forwards[level]) is not None and next_node.key < key:
                current = next_node
            update[level] = current
        return update

    def get(self, key: str, default: Any = None) -> Any:
        current = self.head
        for level in range(self.level - 1, -1, -1):
            while (next_node := current.forwards[level]) is not None and next_node.key < key:
                current = next_node
        candidate = current.forwards[0]
        if candidate is not None and candidate.key == key:
            return candidate.value
        return default

    def __contains__(self, key: str) -> bool:
        return self.get(key, default=...) is not ...

    def put(self, key: str, value: Any) -> bool:
        update = self._locate_predecessors(key)
        candidate = update[0].forwards[0]
        if candidate is not None and candidate.key == key:
            candidate.value = value
            return False

        node_level = self._random_level()
        if node_level > self.level:
            for level in range(self.level, node_level):
                update[level] = self.head
            self.level = node_level

        new_node = Node(key, value, [None] * node_level)
        for level in range(node_level):
            new_node.forwards[level] = update[level].forwards[level]
            update[level].forwards[level] = new_node
        self.length += 1
        return True

    def delete(self, key: str) -> bool:
        update = self._locate_predecessors(key)
        candidate = update[0].forwards[0]
        if candidate is None or candidate.key != key:
            return False

        for level in range(len(candidate.forwards)):
            if update[level].forwards[level] is candidate:
                update[level].forwards[level] = candidate.forwards[level]

        while self.level > 1 and self.head.forwards[self.level - 1] is None:
            self.level -= 1
        self.length -= 1
        return True

    def items(self) -> list[tuple[str, Any]]:
        items: list[tuple[str, Any]] = []
        current = self.head.forwards[0]
        while current is not None:
            items.append((current.key or "", current.value))
            current = current.forwards[0]
        return items

    def range_query(self, start: str | None = None, stop: str | None = None) -> list[tuple[str, Any]]:
        if start is not None and stop is not None and start > stop:
            raise ValueError("start must be <= stop")

        current = self.head
        if start is not None:
            for level in range(self.level - 1, -1, -1):
                while (next_node := current.forwards[level]) is not None and next_node.key < start:
                    current = next_node
            current = current.forwards[0]
        else:
            current = self.head.forwards[0]

        results: list[tuple[str, Any]] = []
        while current is not None and (stop is None or current.key <= stop):
            results.append((current.key or "", current.value))
            current = current.forwards[0]
        return results

    def stats(self) -> dict[str, Any]:
        level_counts = [0] * self.level
        current = self.head.forwards[0]
        while current is not None:
            level_counts[len(current.forwards) - 1] += 1
            current = current.forwards[0]
        return {
            "length": self.length,
            "active_levels": self.level,
            "max_level": self.max_level,
            "probability": self.probability,
            "nodes_per_height": {str(i + 1): count for i, count in enumerate(level_counts)},
        }


def build_skip_list(pairs: Iterable[tuple[str, Any]], *, max_level: int = 8, probability: float = 0.5, seed: int | None = None) -> SkipList:
    skip_list = SkipList(max_level=max_level, probability=probability, seed=seed)
    for key, value in pairs:
        skip_list.put(key, value)
    return skip_list


def load_pairs(path: Path) -> list[tuple[str, Any]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError("input file must be a JSON list")
    pairs: list[tuple[str, Any]] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict) or "key" not in entry or "value" not in entry:
            raise ValueError(f"entry #{index} must contain key and value")
        pairs.append((str(entry["key"]), entry["value"]))
    return pairs


def save_pairs(path: Path, items: list[tuple[str, Any]]) -> None:
    payload = [{"key": key, "value": value} for key, value in items]
    path.write_text(json.dumps(payload, indent=2) + "\n")


def parse_cli_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Skip-list key/value lab")
    parser.add_argument("data", type=Path, help="JSON file with [{'key': ..., 'value': ...}] entries")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-level", type=int, default=8)
    parser.add_argument("--probability", type=float, default=0.5)

    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("key")

    put_parser = subparsers.add_parser("put")
    put_parser.add_argument("key")
    put_parser.add_argument("value")
    put_parser.add_argument("--persist", action="store_true")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("key")
    delete_parser.add_argument("--persist", action="store_true")

    range_parser = subparsers.add_parser("range")
    range_parser.add_argument("--start")
    range_parser.add_argument("--stop")

    subparsers.add_parser("stats")
    subparsers.add_parser("dump")
    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    pairs = load_pairs(args.data) if args.data.exists() else []
    skip_list = build_skip_list(
        pairs,
        max_level=args.max_level,
        probability=args.probability,
        seed=args.seed,
    )

    if args.command == "get":
        value = skip_list.get(args.key)
        if value is None and args.key not in skip_list:
            raise SystemExit(f"key not found: {args.key}")
        print(json.dumps({"key": args.key, "value": value}, indent=2))
        return

    if args.command == "put":
        inserted = skip_list.put(args.key, parse_cli_value(args.value))
        if args.persist:
            save_pairs(args.data, skip_list.items())
        print(json.dumps({"inserted": inserted, "length": len(skip_list)}, indent=2))
        return

    if args.command == "delete":
        deleted = skip_list.delete(args.key)
        if deleted and args.persist:
            save_pairs(args.data, skip_list.items())
        print(json.dumps({"deleted": deleted, "length": len(skip_list)}, indent=2))
        return

    if args.command == "range":
        print(json.dumps([
            {"key": key, "value": value}
            for key, value in skip_list.range_query(args.start, args.stop)
        ], indent=2))
        return

    if args.command == "stats":
        print(json.dumps(skip_list.stats(), indent=2))
        return

    if args.command == "dump":
        print(json.dumps([
            {"key": key, "value": value}
            for key, value in skip_list.items()
        ], indent=2))
        return

    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
