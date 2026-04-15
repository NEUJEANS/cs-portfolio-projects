from __future__ import annotations

import argparse
import json
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

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
