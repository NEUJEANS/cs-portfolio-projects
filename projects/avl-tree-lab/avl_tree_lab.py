from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    key: int
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    height: int = 1


class AVLTree:
    def __init__(self, trace: bool = False) -> None:
        self.root: Optional[Node] = None
        self.trace = trace
        self.events: List[str] = []

    def _log(self, message: str) -> None:
        if self.trace:
            self.events.append(message)

    def insert(self, key: int) -> None:
        self.root = self._insert(self.root, key)

    def _insert(self, node: Optional[Node], key: int) -> Node:
        if node is None:
            self._log(f"insert leaf {key}")
            return Node(key=key)
        if key == node.key:
            raise ValueError(f"duplicate key: {key}")
        if key < node.key:
            node.left = self._insert(node.left, key)
        else:
            node.right = self._insert(node.right, key)
        return self._rebalance(node, context=f"insert {key}")

    def delete(self, key: int) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, node: Optional[Node], key: int) -> Optional[Node]:
        if node is None:
            raise KeyError(key)
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            self._log(f"delete key {key}")
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            successor = self._min_node(node.right)
            self._log(f"replace {key} with successor {successor.key}")
            node.key = successor.key
            node.right = self._delete(node.right, successor.key)
        return self._rebalance(node, context=f"delete {key}") if node else None

    def contains(self, key: int) -> bool:
        node = self.root
        while node is not None:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

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

    def height(self) -> int:
        return self._height(self.root)

    def rank(self, key: int) -> int:
        count = 0
        node = self.root
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
        current = index
        while node is not None:
            left_size = self._size(node.left)
            if current < left_size:
                node = node.left
            elif current == left_size:
                return node.key
            else:
                current -= left_size + 1
                node = node.right
        raise IndexError(index)

    def validate(self) -> dict:
        result = self._validate(self.root, lower=None, upper=None)
        return {
            "is_valid": result["is_valid"],
            "height": self.height(),
            "size": result["size"],
            "inorder": self.inorder(),
            "issues": result["issues"],
        }

    def _validate(self, node: Optional[Node], lower: Optional[int], upper: Optional[int]) -> dict:
        if node is None:
            return {"is_valid": True, "height": 0, "size": 0, "issues": []}
        issues: List[str] = []
        if lower is not None and node.key <= lower:
            issues.append(f"bst lower bound violated at {node.key}")
        if upper is not None and node.key >= upper:
            issues.append(f"bst upper bound violated at {node.key}")
        left = self._validate(node.left, lower, node.key)
        right = self._validate(node.right, node.key, upper)
        expected_height = 1 + max(left["height"], right["height"])
        if node.height != expected_height:
            issues.append(
                f"height mismatch at {node.key}: stored={node.height}, expected={expected_height}"
            )
        balance = left["height"] - right["height"]
        if abs(balance) > 1:
            issues.append(f"balance factor out of range at {node.key}: {balance}")
        issues.extend(left["issues"])
        issues.extend(right["issues"])
        return {
            "is_valid": not issues,
            "height": expected_height,
            "size": 1 + left["size"] + right["size"],
            "issues": issues,
        }

    def _rebalance(self, node: Node, context: str) -> Node:
        self._update(node)
        balance = self._balance(node)
        if balance > 1:
            if self._balance(node.left) < 0:
                self._log(f"{context}: left-right rotation at {node.key}")
                assert node.left is not None
                node.left = self._rotate_left(node.left)
            else:
                self._log(f"{context}: right rotation at {node.key}")
            return self._rotate_right(node)
        if balance < -1:
            if self._balance(node.right) > 0:
                self._log(f"{context}: right-left rotation at {node.key}")
                assert node.right is not None
                node.right = self._rotate_right(node.right)
            else:
                self._log(f"{context}: left rotation at {node.key}")
            return self._rotate_left(node)
        return node

    def _rotate_left(self, node: Node) -> Node:
        pivot = node.right
        assert pivot is not None
        node.right = pivot.left
        pivot.left = node
        self._update(node)
        self._update(pivot)
        return pivot

    def _rotate_right(self, node: Node) -> Node:
        pivot = node.left
        assert pivot is not None
        node.left = pivot.right
        pivot.right = node
        self._update(node)
        self._update(pivot)
        return pivot

    def _height(self, node: Optional[Node]) -> int:
        return node.height if node is not None else 0

    def _size(self, node: Optional[Node]) -> int:
        if node is None:
            return 0
        return 1 + self._size(node.left) + self._size(node.right)

    def _balance(self, node: Optional[Node]) -> int:
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _update(self, node: Node) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _min_node(self, node: Node) -> Node:
        current = node
        while current.left is not None:
            current = current.left
        return current


def build_tree(keys: List[int], trace: bool = False) -> AVLTree:
    tree = AVLTree(trace=trace)
    for key in keys:
        tree.insert(key)
    return tree


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_demo(args: argparse.Namespace) -> None:
    keys = [30, 20, 10, 25, 40, 50, 22, 27, 5]
    tree = build_tree(keys, trace=args.trace)
    _print_json(
        {
            "demo_keys": keys,
            "preorder": tree.preorder(),
            "inorder": tree.inorder(),
            "height": tree.height(),
            "validation": tree.validate(),
            "trace": tree.events,
        }
    )


def command_build(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys, trace=args.trace)
    _print_json(
        {
            "inorder": tree.inorder(),
            "preorder": tree.preorder(),
            "height": tree.height(),
            "validation": tree.validate(),
            "trace": tree.events,
        }
    )


def command_contains(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys)
    _print_json({"query": args.query, "contains": tree.contains(args.query)})


def command_delete(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys, trace=args.trace)
    tree.delete(args.query)
    _print_json(
        {
            "deleted": args.query,
            "inorder": tree.inorder(),
            "preorder": tree.preorder(),
            "height": tree.height(),
            "validation": tree.validate(),
            "trace": tree.events,
        }
    )


def command_rank(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys)
    _print_json({"query": args.query, "rank": tree.rank(args.query)})


def command_select(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys)
    _print_json({"index": args.index, "key": tree.select(args.index)})


def command_validate(args: argparse.Namespace) -> None:
    tree = build_tree(args.keys)
    _print_json(tree.validate())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AVL tree lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the bundled demo")
    demo.add_argument("--trace", action="store_true")
    demo.set_defaults(func=command_demo)

    build = subparsers.add_parser("build", help="build a tree from keys")
    build.add_argument("keys", nargs="+", type=int)
    build.add_argument("--trace", action="store_true")
    build.set_defaults(func=command_build)

    contains = subparsers.add_parser("contains", help="check membership")
    contains.add_argument("query", type=int)
    contains.add_argument("keys", nargs="+", type=int)
    contains.set_defaults(func=command_contains)

    delete = subparsers.add_parser("delete", help="delete a key and print the repaired tree")
    delete.add_argument("query", type=int)
    delete.add_argument("keys", nargs="+", type=int)
    delete.add_argument("--trace", action="store_true")
    delete.set_defaults(func=command_delete)

    rank = subparsers.add_parser("rank", help="count keys smaller than the query")
    rank.add_argument("query", type=int)
    rank.add_argument("keys", nargs="+", type=int)
    rank.set_defaults(func=command_rank)

    select = subparsers.add_parser("select", help="return the zero-based kth smallest key")
    select.add_argument("index", type=int)
    select.add_argument("keys", nargs="+", type=int)
    select.set_defaults(func=command_select)

    validate = subparsers.add_parser("validate", help="validate a built tree")
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
