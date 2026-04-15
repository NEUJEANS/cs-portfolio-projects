from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Node:
    key: int
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None


class SplayTree:
    def __init__(self, values: Iterable[int] | None = None) -> None:
        self.root: Node | None = None
        self.size = 0
        self.rotation_count = 0
        self.splay_steps = 0
        self.comparison_count = 0
        if values is not None:
            for value in values:
                self.insert(value)

    def _rotate_left(self, pivot: Node) -> None:
        child = pivot.right
        if child is None:
            return
        pivot.right = child.left
        if child.left is not None:
            child.left.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot.parent.left is pivot:
            pivot.parent.left = child
        else:
            pivot.parent.right = child
        child.left = pivot
        pivot.parent = child
        self.rotation_count += 1

    def _rotate_right(self, pivot: Node) -> None:
        child = pivot.left
        if child is None:
            return
        pivot.left = child.right
        if child.right is not None:
            child.right.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot.parent.left is pivot:
            pivot.parent.left = child
        else:
            pivot.parent.right = child
        child.right = pivot
        pivot.parent = child
        self.rotation_count += 1

    def _splay(self, node: Node | None) -> None:
        while node is not None and node.parent is not None:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                if parent.left is node:
                    self._rotate_right(parent)
                else:
                    self._rotate_left(parent)
            elif grandparent.left is parent and parent.left is node:
                self._rotate_right(grandparent)
                self._rotate_right(parent)
            elif grandparent.right is parent and parent.right is node:
                self._rotate_left(grandparent)
                self._rotate_left(parent)
            elif grandparent.left is parent and parent.right is node:
                self._rotate_left(parent)
                self._rotate_right(grandparent)
            else:
                self._rotate_right(parent)
                self._rotate_left(grandparent)
            self.splay_steps += 1

    def insert(self, key: int) -> bool:
        if self.root is None:
            self.root = Node(key)
            self.size = 1
            return True
        current = self.root
        while current is not None:
            self.comparison_count += 1
            if key < current.key:
                if current.left is None:
                    current.left = Node(key=key, parent=current)
                    self.size += 1
                    self._splay(current.left)
                    return True
                current = current.left
            elif key > current.key:
                if current.right is None:
                    current.right = Node(key=key, parent=current)
                    self.size += 1
                    self._splay(current.right)
                    return True
                current = current.right
            else:
                self._splay(current)
                return False
        return False

    def find(self, key: int) -> bool:
        current = self.root
        last = None
        while current is not None:
            last = current
            self.comparison_count += 1
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                self._splay(current)
                return True
        self._splay(last)
        return False

    def delete(self, key: int) -> bool:
        if not self.find(key) or self.root is None or self.root.key != key:
            return False
        left = self.root.left
        right = self.root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None
        self.root = self._join(left, right)
        self.size -= 1
        return True

    def _join(self, left: Node | None, right: Node | None) -> Node | None:
        if left is None:
            return right
        self.root = left
        current = left
        while current.right is not None:
            current = current.right
        self._splay(current)
        assert self.root is current
        current.right = right
        if right is not None:
            right.parent = current
        return current

    def inorder(self) -> list[int]:
        items: list[int] = []

        def walk(node: Node | None) -> None:
            if node is None:
                return
            walk(node.left)
            items.append(node.key)
            walk(node.right)

        walk(self.root)
        return items

    def snapshot(self) -> dict:
        return {
            "values": self.inorder(),
            "root": self.root.key if self.root is not None else None,
            "size": self.size,
            "rotation_count": self.rotation_count,
            "splay_steps": self.splay_steps,
            "comparison_count": self.comparison_count,
        }

    @classmethod
    def from_snapshot(cls, payload: dict) -> "SplayTree":
        tree = cls(payload.get("values", []))
        tree.rotation_count = payload.get("rotation_count", tree.rotation_count)
        tree.splay_steps = payload.get("splay_steps", tree.splay_steps)
        tree.comparison_count = payload.get("comparison_count", tree.comparison_count)
        root_key = payload.get("root")
        if root_key is not None:
            tree.find(root_key)
        return tree

    def access_sequence(self, keys: Iterable[int]) -> dict:
        sequence = list(keys)
        before_root = self.root.key if self.root is not None else None
        rotations_before = self.rotation_count
        comparisons_before = self.comparison_count
        hits = 0
        misses = 0
        for key in sequence:
            if self.find(key):
                hits += 1
            else:
                misses += 1
        return {
            "requested_keys": sequence,
            "hits": hits,
            "misses": misses,
            "root_before": before_root,
            "root_after": self.root.key if self.root is not None else None,
            "rotations_used": self.rotation_count - rotations_before,
            "comparisons_used": self.comparison_count - comparisons_before,
            "size": self.size,
        }


def parse_values(path: Path) -> list[int]:
    values = []
    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            values.append(int(stripped))
        except ValueError as exc:
            raise ValueError(f"invalid integer on line {line_number}: {stripped!r}") from exc
    return values


def load_tree(path: Path) -> SplayTree:
    return SplayTree.from_snapshot(json.loads(path.read_text()))


def save_tree(path: Path, tree: SplayTree) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree.snapshot(), indent=2) + "\n")


def load_red_black_tree_class() -> type:
    module_path = Path(__file__).resolve().parents[1] / "red-black-tree-lab" / "red_black_tree.py"
    spec = importlib.util.spec_from_file_location("red_black_tree_lab_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load red-black tree module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.RedBlackTree


def red_black_search_depth(tree: object, key: int) -> tuple[bool, int]:
    current = tree.root
    comparisons = 0
    while current is not None:
        comparisons += 1
        if key < current.key:
            current = current.left
        elif key > current.key:
            current = current.right
        else:
            return True, comparisons
    return False, comparisons


def make_benchmark_values(size: int, seed: int) -> list[int]:
    values = list(range(1, size + 1))
    random.Random(seed).shuffle(values)
    return values


def make_hot_queries(values: list[int], *, query_count: int, hot_set_size: int, seed: int) -> tuple[list[int], list[int]]:
    rng = random.Random(seed)
    hot_keys = sorted(values[:hot_set_size])
    queries = [rng.choice(hot_keys) for _ in range(query_count)]
    return hot_keys, queries


def make_random_queries(values: list[int], *, query_count: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.choice(values) for _ in range(query_count)]


def run_comparison_workload(values: list[int], queries: list[int]) -> dict[str, object]:
    RedBlackTree = load_red_black_tree_class()

    splay_tree = SplayTree(values)
    rb_tree = RedBlackTree()
    for value in values:
        rb_tree.insert(value)

    splay_before_rotations = splay_tree.rotation_count
    splay_before_comparisons = splay_tree.comparison_count
    splay_hits = 0
    for key in queries:
        if splay_tree.find(key):
            splay_hits += 1

    rb_hits = 0
    rb_comparisons = 0
    for key in queries:
        found, comparisons = red_black_search_depth(rb_tree, key)
        rb_comparisons += comparisons
        if found:
            rb_hits += 1

    query_count = len(queries)
    return {
        "queries": query_count,
        "splay": {
            "hits": splay_hits,
            "comparisons_used": splay_tree.comparison_count - splay_before_comparisons,
            "rotations_used": splay_tree.rotation_count - splay_before_rotations,
            "comparisons_per_query": round((splay_tree.comparison_count - splay_before_comparisons) / query_count, 3),
            "rotations_per_query": round((splay_tree.rotation_count - splay_before_rotations) / query_count, 3),
            "root_after": None if splay_tree.root is None else splay_tree.root.key,
        },
        "red_black": {
            "hits": rb_hits,
            "comparisons_used": rb_comparisons,
            "comparisons_per_query": round(rb_comparisons / query_count, 3),
            "height": rb_tree.height(),
            "root": None if rb_tree.root is None else rb_tree.root.key,
        },
    }


def benchmark_trees(*, size: int, hot_set_size: int, hot_queries: int, random_queries: int, seed: int) -> dict[str, object]:
    if size <= 0:
        raise ValueError("size must be positive")
    if hot_set_size <= 0 or hot_set_size > size:
        raise ValueError("hot-set-size must be between 1 and size")
    if hot_queries <= 0 or random_queries <= 0:
        raise ValueError("query counts must be positive")

    values = make_benchmark_values(size, seed)
    hot_keys, hot_workload = make_hot_queries(values, query_count=hot_queries, hot_set_size=hot_set_size, seed=seed + 1)
    random_workload = make_random_queries(values, query_count=random_queries, seed=seed + 2)

    hot_result = run_comparison_workload(values, hot_workload)
    random_result = run_comparison_workload(values, random_workload)

    return {
        "size": size,
        "seed": seed,
        "hot_set_size": hot_set_size,
        "hot_keys": hot_keys,
        "build_preview": values[: min(12, len(values))],
        "workloads": {
            "hotset": hot_result,
            "uniform_random": random_result,
        },
        "takeaway": {
            "hotset_comparison_gap": hot_result["red_black"]["comparisons_used"] - hot_result["splay"]["comparisons_used"],
            "uniform_random_comparison_gap": random_result["red_black"]["comparisons_used"] - random_result["splay"]["comparisons_used"],
            "interpretation": (
                "positive gap means the splay tree used fewer key comparisons than the red-black tree on that workload"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Splay tree lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a snapshot from newline-delimited integers")
    build_parser.add_argument("--input", required=True, type=Path)
    build_parser.add_argument("--output", required=True, type=Path)

    access_parser = subparsers.add_parser("access", help="run an access sequence against a snapshot")
    access_parser.add_argument("--snapshot", required=True, type=Path)
    access_parser.add_argument("--output", type=Path)
    access_parser.add_argument("keys", nargs="+", type=int)

    insert_parser = subparsers.add_parser("insert", help="insert a key into a snapshot")
    insert_parser.add_argument("--snapshot", required=True, type=Path)
    insert_parser.add_argument("--output", required=True, type=Path)
    insert_parser.add_argument("key", type=int)

    delete_parser = subparsers.add_parser("delete", help="delete a key from a snapshot")
    delete_parser.add_argument("--snapshot", required=True, type=Path)
    delete_parser.add_argument("--output", required=True, type=Path)
    delete_parser.add_argument("key", type=int)

    show_parser = subparsers.add_parser("show", help="show current snapshot summary")
    show_parser.add_argument("--snapshot", required=True, type=Path)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare skewed and random access workloads against the red-black-tree-lab baseline",
    )
    benchmark_parser.add_argument("--size", type=int, default=255, help="number of keys to build into both trees")
    benchmark_parser.add_argument("--hot-set-size", type=int, default=8, help="number of hot keys for the skewed workload")
    benchmark_parser.add_argument("--hot-queries", type=int, default=256, help="number of skewed hot-set queries")
    benchmark_parser.add_argument(
        "--random-queries", type=int, default=256, help="number of uniformly random successful queries"
    )
    benchmark_parser.add_argument("--seed", type=int, default=42, help="deterministic seed for build order and queries")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "build":
        tree = SplayTree(parse_values(args.input))
        save_tree(args.output, tree)
        print(json.dumps(tree.snapshot(), indent=2))
        return 0

    if args.command == "access":
        tree = load_tree(args.snapshot)
        summary = tree.access_sequence(args.keys)
        if args.output is not None:
            save_tree(args.output, tree)
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "insert":
        tree = load_tree(args.snapshot)
        inserted = tree.insert(args.key)
        save_tree(args.output, tree)
        print(json.dumps({"inserted": inserted, **tree.snapshot()}, indent=2))
        return 0

    if args.command == "delete":
        tree = load_tree(args.snapshot)
        deleted = tree.delete(args.key)
        save_tree(args.output, tree)
        print(json.dumps({"deleted": deleted, **tree.snapshot()}, indent=2))
        return 0

    if args.command == "show":
        tree = load_tree(args.snapshot)
        print(json.dumps(tree.snapshot(), indent=2))
        return 0

    if args.command == "benchmark":
        payload = benchmark_trees(
            size=args.size,
            hot_set_size=args.hot_set_size,
            hot_queries=args.hot_queries,
            random_queries=args.random_queries,
            seed=args.seed,
        )
        print(json.dumps(payload, indent=2))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
