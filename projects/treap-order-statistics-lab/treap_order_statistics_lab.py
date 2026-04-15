from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class Node:
    key: int
    priority: int
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    size: int = 1


@dataclass
class Treap:
    seed: int = 0
    trace: bool = False
    root: Optional[Node] = None
    events: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def _log(self, message: str) -> None:
        if self.trace:
            self.events.append(message)

    def _size(self, node: Optional[Node]) -> int:
        return node.size if node is not None else 0

    def _update(self, node: Optional[Node]) -> None:
        if node is not None:
            node.size = 1 + self._size(node.left) + self._size(node.right)

    def contains(self, key: int) -> bool:
        node = self.root
        while node is not None:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def _split(self, node: Optional[Node], key: int) -> tuple[Optional[Node], Optional[Node]]:
        if node is None:
            return None, None
        if key < node.key:
            left, node.left = self._split(node.left, key)
            self._update(node)
            return left, node
        node.right, right = self._split(node.right, key)
        self._update(node)
        return node, right

    def _merge(self, left: Optional[Node], right: Optional[Node]) -> Optional[Node]:
        if left is None:
            return right
        if right is None:
            return left
        if left.priority > right.priority:
            left.right = self._merge(left.right, right)
            self._update(left)
            return left
        right.left = self._merge(left, right.left)
        self._update(right)
        return right

    def insert(self, key: int) -> int:
        if self.contains(key):
            raise ValueError(f"duplicate key: {key}")
        priority = self._random.randint(1, 1_000_000_000)
        self._log(f"insert key={key} priority={priority}")
        self.root = self._insert(self.root, Node(key=key, priority=priority))
        return priority

    def _insert(self, node: Optional[Node], fresh: Node) -> Node:
        if node is None:
            return fresh
        if fresh.priority > node.priority:
            left, right = self._split(node, fresh.key)
            fresh.left = left
            fresh.right = right
            self._update(fresh)
            return fresh
        if fresh.key < node.key:
            node.left = self._insert(node.left, fresh)
        else:
            node.right = self._insert(node.right, fresh)
        self._update(node)
        return node

    def delete(self, key: int) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, node: Optional[Node], key: int) -> Optional[Node]:
        if node is None:
            raise KeyError(key)
        if key == node.key:
            self._log(f"delete key={key}")
            return self._merge(node.left, node.right)
        if key < node.key:
            node.left = self._delete(node.left, key)
        else:
            node.right = self._delete(node.right, key)
        self._update(node)
        return node

    def rank(self, key: int) -> int:
        node = self.root
        count = 0
        while node is not None:
            if key <= node.key:
                node = node.left
            else:
                count += 1 + self._size(node.left)
                node = node.right
        return count

    def select(self, index: int) -> int:
        if index < 0 or index >= self._size(self.root):
            raise IndexError(index)
        node = self.root
        remaining = index
        while node is not None:
            left_size = self._size(node.left)
            if remaining < left_size:
                node = node.left
            elif remaining == left_size:
                return node.key
            else:
                remaining -= left_size + 1
                node = node.right
        raise IndexError(index)

    def range_count(self, lower: int, upper: int) -> int:
        if lower > upper:
            raise ValueError("lower must be <= upper")
        return self.rank(upper + 1) - self.rank(lower)

    def inorder(self) -> List[int]:
        return self._inorder(self.root)

    def _inorder(self, node: Optional[Node]) -> List[int]:
        if node is None:
            return []
        return self._inorder(node.left) + [node.key] + self._inorder(node.right)

    def preorder(self) -> List[int]:
        return self._preorder(self.root)

    def _preorder(self, node: Optional[Node]) -> List[int]:
        if node is None:
            return []
        return [node.key] + self._preorder(node.left) + self._preorder(node.right)

    def validate(self) -> dict:
        result = self._validate(self.root, lower=None, upper=None)
        return {
            "is_valid": not result["issues"],
            "size": result["size"],
            "height": result["height"],
            "inorder": self.inorder(),
            "issues": result["issues"],
        }

    def _validate(self, node: Optional[Node], lower: Optional[int], upper: Optional[int]) -> dict:
        if node is None:
            return {"issues": [], "size": 0, "height": 0, "max_priority": None}
        issues: List[str] = []
        if lower is not None and node.key <= lower:
            issues.append(f"bst lower bound violated at {node.key}")
        if upper is not None and node.key >= upper:
            issues.append(f"bst upper bound violated at {node.key}")
        left = self._validate(node.left, lower, node.key)
        right = self._validate(node.right, node.key, upper)
        if left["max_priority"] is not None and left["max_priority"] > node.priority:
            issues.append(f"heap priority violated at {node.key} via left child")
        if right["max_priority"] is not None and right["max_priority"] > node.priority:
            issues.append(f"heap priority violated at {node.key} via right child")
        expected_size = 1 + left["size"] + right["size"]
        if node.size != expected_size:
            issues.append(
                f"size mismatch at {node.key}: stored={node.size}, expected={expected_size}"
            )
        issues.extend(left["issues"])
        issues.extend(right["issues"])
        return {
            "issues": issues,
            "size": expected_size,
            "height": 1 + max(left["height"], right["height"]),
            "max_priority": max(
                value
                for value in [node.priority, left["max_priority"], right["max_priority"]]
                if value is not None
            ),
        }


def build_treap(keys: Iterable[int], seed: int = 0, trace: bool = False) -> Treap:
    treap = Treap(seed=seed, trace=trace)
    for key in keys:
        treap.insert(key)
    return treap


def load_keys(path: Path) -> List[int]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list) or not all(isinstance(item, int) for item in payload):
        raise ValueError("sample file must be a JSON array of integers")
    return payload


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_demo(args: argparse.Namespace) -> None:
    keys = load_keys(Path(args.sample)) if args.sample else [40, 10, 60, 5, 20, 50, 70, 65, 15]
    treap = build_treap(keys, seed=args.seed, trace=args.trace)
    _print_json(
        {
            "keys": keys,
            "seed": args.seed,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "rank_50": treap.rank(50),
            "select_3": treap.select(3),
            "range_count_15_65": treap.range_count(15, 65),
            "trace": treap.events,
        }
    )


def command_build(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed, trace=args.trace)
    _print_json(
        {
            "seed": args.seed,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "trace": treap.events,
        }
    )


def command_delete(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed, trace=args.trace)
    treap.delete(args.query)
    _print_json(
        {
            "deleted": args.query,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "trace": treap.events,
        }
    )


def command_rank(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"query": args.query, "rank": treap.rank(args.query)})


def command_select(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"index": args.index, "key": treap.select(args.index)})


def command_range_count(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"lower": args.lower, "upper": args.upper, "count": treap.range_count(args.lower, args.upper)})


def command_validate(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json(treap.validate())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Treap order-statistics lab")
    parser.add_argument("--seed", type=int, default=0, help="seed for deterministic priorities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the bundled demo")
    demo.add_argument("--sample", help="optional JSON array of integer keys")
    demo.add_argument("--trace", action="store_true")
    demo.set_defaults(func=command_demo)

    build = subparsers.add_parser("build", help="build a treap from keys")
    build.add_argument("keys", nargs="+", type=int)
    build.add_argument("--trace", action="store_true")
    build.set_defaults(func=command_build)

    delete = subparsers.add_parser("delete", help="delete a key and print the repaired treap")
    delete.add_argument("query", type=int)
    delete.add_argument("keys", nargs="+", type=int)
    delete.add_argument("--trace", action="store_true")
    delete.set_defaults(func=command_delete)

    rank = subparsers.add_parser("rank", help="count keys smaller than a query")
    rank.add_argument("query", type=int)
    rank.add_argument("keys", nargs="+", type=int)
    rank.set_defaults(func=command_rank)

    select = subparsers.add_parser("select", help="return the zero-based kth smallest key")
    select.add_argument("index", type=int)
    select.add_argument("keys", nargs="+", type=int)
    select.set_defaults(func=command_select)

    range_count = subparsers.add_parser("range-count", help="count keys inside an inclusive range")
    range_count.add_argument("lower", type=int)
    range_count.add_argument("upper", type=int)
    range_count.add_argument("keys", nargs="+", type=int)
    range_count.set_defaults(func=command_range_count)

    validate = subparsers.add_parser("validate", help="validate a built treap")
    validate.add_argument("keys", nargs="+", type=int)
    validate.set_defaults(func=command_validate)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (KeyError, ValueError, IndexError) as exc:
        _print_json({"error": str(exc)})
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
