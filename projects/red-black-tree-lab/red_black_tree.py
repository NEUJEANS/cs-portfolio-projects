from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable

RED = "red"
BLACK = "black"


@dataclass
class Node:
    key: int
    color: str = RED
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None
    subtree_size: int = 1


class RedBlackTree:
    def __init__(self) -> None:
        self.root: Node | None = None
        self.size = 0

    def insert(self, key: int) -> bool:
        parent: Node | None = None
        current = self.root
        path: list[Node] = []
        while current is not None:
            parent = current
            path.append(current)
            if key == current.key:
                return False
            current = current.left if key < current.key else current.right

        node = Node(key=key, color=RED, parent=parent)
        if parent is None:
            self.root = node
        elif key < parent.key:
            parent.left = node
        else:
            parent.right = node

        self.size += 1
        for ancestor in path:
            ancestor.subtree_size += 1
        self._fix_insert(node)
        return True

    def contains(self, key: int) -> bool:
        return self.find_node(key) is not None

    def find_node(self, key: int) -> Node | None:
        current = self.root
        while current is not None:
            if key == current.key:
                return current
            current = current.left if key < current.key else current.right
        return None

    def inorder(self) -> list[int]:
        result: list[int] = []

        def traverse(node: Node | None) -> None:
            if node is None:
                return
            traverse(node.left)
            result.append(node.key)
            traverse(node.right)

        traverse(self.root)
        return result

    def height(self) -> int:
        def visit(node: Node | None) -> int:
            if node is None:
                return 0
            return 1 + max(visit(node.left), visit(node.right))

        return visit(self.root)

    def rank(self, key: int) -> int:
        rank = 0
        current = self.root
        while current is not None:
            if key <= current.key:
                current = current.left
            else:
                rank += 1 + self._size(current.left)
                current = current.right
        return rank

    def select(self, index: int) -> int:
        if index < 0 or index >= self.size:
            raise IndexError(f"index {index} is out of range for tree size {self.size}")
        current = self.root
        remaining = index
        while current is not None:
            left_size = self._size(current.left)
            if remaining < left_size:
                current = current.left
            elif remaining == left_size:
                return current.key
            else:
                remaining -= left_size + 1
                current = current.right
        raise RuntimeError("select reached an unexpected empty path")

    def black_height(self) -> int:
        valid, black_height, _ = self.validate()
        if not valid:
            raise ValueError("tree is not a valid red-black tree")
        return black_height

    def validate(self) -> tuple[bool, int, list[str]]:
        errors: list[str] = []
        if self.root and self.root.color != BLACK:
            errors.append("root must be black")

        def walk(
            node: Node | None,
            lower: int | None,
            upper: int | None,
            expected_parent: Node | None,
        ) -> tuple[bool, int, int]:
            if node is None:
                return True, 1, 0
            if node.parent is not expected_parent:
                expected = None if expected_parent is None else expected_parent.key
                actual = None if node.parent is None else node.parent.key
                errors.append(f"parent pointer mismatch at {node.key}: expected {expected}, got {actual}")
            if lower is not None and node.key <= lower:
                errors.append(f"BST ordering violated at {node.key}: <= lower bound {lower}")
            if upper is not None and node.key >= upper:
                errors.append(f"BST ordering violated at {node.key}: >= upper bound {upper}")
            if node.color not in {RED, BLACK}:
                errors.append(f"invalid color on {node.key}: {node.color}")
            if node.color == RED:
                for child in (node.left, node.right):
                    if child is not None and child.color == RED:
                        errors.append(f"red node {node.key} has red child {child.key}")
            left_valid, left_black_height, left_size = walk(node.left, lower, node.key, node)
            right_valid, right_black_height, right_size = walk(node.right, node.key, upper, node)
            if left_black_height != right_black_height:
                errors.append(
                    f"black-height mismatch at {node.key}: left={left_black_height}, right={right_black_height}"
                )
            expected_subtree_size = 1 + left_size + right_size
            if node.subtree_size != expected_subtree_size:
                errors.append(
                    f"subtree_size mismatch at {node.key}: expected {expected_subtree_size}, got {node.subtree_size}"
                )
            current_black_height = left_black_height + (1 if node.color == BLACK else 0)
            return left_valid and right_valid, current_black_height, expected_subtree_size

        _, black_height, computed_size = walk(self.root, None, None, None)
        if computed_size != self.size:
            errors.append(f"tree size mismatch: expected {computed_size}, got {self.size}")
        return len(errors) == 0, black_height, errors

    def summary(self) -> dict[str, object]:
        valid, black_height, errors = self.validate()
        return {
            "size": self.size,
            "height": self.height(),
            "black_height": black_height,
            "root": None
            if self.root is None
            else {"key": self.root.key, "color": self.root.color, "subtree_size": self.root.subtree_size},
            "inorder": self.inorder(),
            "valid": valid,
            "errors": errors,
        }

    def _rotate_left(self, pivot: Node) -> None:
        child = pivot.right
        if child is None:
            raise ValueError("cannot left-rotate without a right child")
        pivot.right = child.left
        if child.left is not None:
            child.left.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot == pivot.parent.left:
            pivot.parent.left = child
        else:
            pivot.parent.right = child
        child.left = pivot
        pivot.parent = child
        self._refresh_size(pivot)
        self._refresh_size(child)

    def _rotate_right(self, pivot: Node) -> None:
        child = pivot.left
        if child is None:
            raise ValueError("cannot right-rotate without a left child")
        pivot.left = child.right
        if child.right is not None:
            child.right.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot == pivot.parent.right:
            pivot.parent.right = child
        else:
            pivot.parent.left = child
        child.right = pivot
        pivot.parent = child
        self._refresh_size(pivot)
        self._refresh_size(child)

    def _fix_insert(self, node: Node) -> None:
        while node.parent is not None and node.parent.color == RED:
            grandparent = node.parent.parent
            if grandparent is None:
                break
            if node.parent == grandparent.left:
                uncle = grandparent.right
                if uncle is not None and uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                    continue
                if node == node.parent.right:
                    node = node.parent
                    self._rotate_left(node)
                assert node.parent is not None
                node.parent.color = BLACK
                grandparent.color = RED
                self._rotate_right(grandparent)
            else:
                uncle = grandparent.left
                if uncle is not None and uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                    continue
                if node == node.parent.left:
                    node = node.parent
                    self._rotate_right(node)
                assert node.parent is not None
                node.parent.color = BLACK
                grandparent.color = RED
                self._rotate_left(grandparent)
        if self.root is not None:
            self.root.color = BLACK
        self._refresh_upwards(node)

    def _refresh_upwards(self, node: Node | None) -> None:
        while node is not None:
            self._refresh_size(node)
            node = node.parent

    @staticmethod
    def _size(node: Node | None) -> int:
        return 0 if node is None else node.subtree_size

    def _refresh_size(self, node: Node) -> None:
        node.subtree_size = 1 + self._size(node.left) + self._size(node.right)


def build_tree(values: Iterable[int]) -> RedBlackTree:
    tree = RedBlackTree()
    for value in values:
        tree.insert(value)
    return tree


def command_demo(_: argparse.Namespace) -> dict[str, object]:
    tree = build_tree([7, 3, 18, 10, 22, 8, 11, 26])
    payload = {"command": "demo", **tree.summary()}
    payload["contains"] = {"8": tree.contains(8), "15": tree.contains(15)}
    payload["rank"] = {"8": tree.rank(8), "15": tree.rank(15)}
    payload["select"] = {"0": tree.select(0), "3": tree.select(3)}
    return payload


def command_build(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values)
    return {"command": "build", "input": args.values, **tree.summary()}


def command_contains(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values)
    return {
        "command": "contains",
        "input": args.values,
        "query": args.query,
        "found": tree.contains(args.query),
        **tree.summary(),
    }


def command_rank(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values)
    return {
        "command": "rank",
        "input": args.values,
        "query": args.query,
        "rank": tree.rank(args.query),
        **tree.summary(),
    }


def command_select(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values)
    selected = tree.select(args.index)
    return {
        "command": "select",
        "input": args.values,
        "index": args.index,
        "selected": selected,
        **tree.summary(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Red-black tree insertion and validation lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="run a bundled insertion demo")
    demo_parser.set_defaults(handler=command_demo)

    build_parser = subparsers.add_parser("build", help="build a tree from integer values")
    build_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    build_parser.set_defaults(handler=command_build)

    contains_parser = subparsers.add_parser("contains", help="build a tree and query a key")
    contains_parser.add_argument("query", type=int, help="integer to search for")
    contains_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    contains_parser.set_defaults(handler=command_contains)

    rank_parser = subparsers.add_parser("rank", help="count how many inserted keys are smaller than the query")
    rank_parser.add_argument("query", type=int, help="integer to rank")
    rank_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    rank_parser.set_defaults(handler=command_rank)

    select_parser = subparsers.add_parser("select", help="return the zero-based kth smallest key")
    select_parser.add_argument("index", type=int, help="zero-based inorder index")
    select_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    select_parser.set_defaults(handler=command_select)

    args = parser.parse_args()
    try:
        payload = args.handler(args)
    except IndexError as error:
        parser.error(str(error))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
