from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import random
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

RED = "red"
BLACK = "black"
_AVL_MODULE: object | None = None


@dataclass
class Node:
    key: int
    color: str = RED
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None
    subtree_size: int = 1


class RedBlackTree:
    def __init__(self, *, trace_enabled: bool = False) -> None:
        self.root: Node | None = None
        self.size = 0
        self.trace_enabled = trace_enabled
        self.trace: list[dict[str, object]] = []

    def enable_trace(self) -> None:
        self.trace_enabled = True

    def insert(self, key: int) -> bool:
        parent: Node | None = None
        current = self.root
        path: list[Node] = []
        while current is not None:
            parent = current
            path.append(current)
            if key == current.key:
                self._log("insert_duplicate_rejected", key=key)
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
        self._log(
            "inserted",
            key=key,
            parent=None if parent is None else parent.key,
            direction=(None if parent is None else ("left" if key < parent.key else "right")),
        )
        self._fix_insert(node)
        return True

    def delete(self, key: int) -> bool:
        target = self.find_node(key)
        if target is None:
            self._log("delete_missing", key=key)
            return False
        self._log("delete_start", key=key)
        self._delete_node(target)
        self._log("delete_complete", key=key)
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

    def summary(self, *, include_trace: bool = False) -> dict[str, object]:
        valid, black_height, errors = self.validate()
        payload: dict[str, object] = {
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
        if include_trace:
            payload["trace"] = self.trace
        return payload

    def to_dot(self, *, include_nil: bool = True) -> str:
        lines = [
            "digraph RedBlackTree {",
            '  graph [rankdir=TB, nodesep=0.35, ranksep=0.45];',
            '  node [shape=circle, style=filled, fontname="Helvetica", fontcolor=white, penwidth=1.2];',
            '  edge [arrowsize=0.7];',
        ]
        if self.root is None:
            lines.append('  empty [label="∅", shape=plaintext, fontcolor=black];')
            lines.append("}")
            return "\n".join(lines)

        nil_counter = 0

        def visit(node: Node, path: str) -> None:
            nonlocal nil_counter
            node_id = self._dot_node_id(path)
            fill = "#d73a49" if node.color == RED else "#24292f"
            lines.append(
                f'  {node_id} [label="{node.key}\\nsize={node.subtree_size}", fillcolor="{fill}", tooltip="{node.color}"];'
            )
            for side, child in (("L", node.left), ("R", node.right)):
                child_path = f"{path}{side}"
                if child is None:
                    if not include_nil:
                        continue
                    nil_counter += 1
                    nil_id = f'nil_{nil_counter}_{child_path.lower()}'
                    lines.append(
                        f'  {nil_id} [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#24292f"];'
                    )
                    lines.append(f'  {node_id} -> {nil_id} [label="{side}", color="#6a737d"];')
                else:
                    child_id = self._dot_node_id(child_path)
                    lines.append(f'  {node_id} -> {child_id} [label="{side}", color="#6a737d"];')
                    visit(child, child_path)

        visit(self.root, "root")
        lines.append("}")
        return "\n".join(lines)

    def _delete_node(self, target: Node) -> None:
        removed_color = target.color
        replacement: Node | None
        replacement_parent: Node | None
        replacement_was_left = False

        if target.left is None:
            replacement = target.right
            replacement_parent = target.parent
            replacement_was_left = replacement_parent is not None and target == replacement_parent.left
            self._transplant(target, target.right)
            refresh_points = [replacement_parent]
            self._log("delete_case_single_or_empty_child", target=target.key, replacement=self._node_key(replacement))
        elif target.right is None:
            replacement = target.left
            replacement_parent = target.parent
            replacement_was_left = replacement_parent is not None and target == replacement_parent.left
            self._transplant(target, target.left)
            refresh_points = [replacement_parent]
            self._log("delete_case_single_or_empty_child", target=target.key, replacement=self._node_key(replacement))
        else:
            successor = self._minimum(target.right)
            removed_color = successor.color
            replacement = successor.right
            self._log("delete_case_two_children", target=target.key, successor=successor.key)
            if successor.parent == target:
                replacement_parent = successor
                replacement_was_left = False
            else:
                replacement_parent = successor.parent
                replacement_was_left = replacement_parent is not None and successor == replacement_parent.left
                self._transplant(successor, successor.right)
                successor.right = target.right
                assert successor.right is not None
                successor.right.parent = successor
            self._transplant(target, successor)
            successor.left = target.left
            assert successor.left is not None
            successor.left.parent = successor
            successor.color = target.color
            self._refresh_size(successor)
            refresh_points = [replacement_parent, successor]

        self.size -= 1
        for node in refresh_points:
            self._refresh_upwards(node)
        if removed_color == BLACK:
            self._fix_delete(replacement, replacement_parent, replacement_was_left)
        if self.root is not None:
            self.root.color = BLACK

    def _rotate_left(self, pivot: Node) -> None:
        child = pivot.right
        if child is None:
            raise ValueError("cannot left-rotate without a right child")
        self._log("rotate_left", pivot=pivot.key, child=child.key)
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
        self._log("rotate_right", pivot=pivot.key, child=child.key)
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
                    self._log(
                        "insert_fixup_recolor",
                        node=node.key,
                        parent=node.parent.key,
                        uncle=uncle.key,
                        grandparent=grandparent.key,
                    )
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                    continue
                if node == node.parent.right:
                    self._log("insert_fixup_triangle", node=node.key, parent=node.parent.key, grandparent=grandparent.key)
                    node = node.parent
                    self._rotate_left(node)
                assert node.parent is not None
                self._log("insert_fixup_line", node=node.key, parent=node.parent.key, grandparent=grandparent.key)
                node.parent.color = BLACK
                grandparent.color = RED
                self._rotate_right(grandparent)
            else:
                uncle = grandparent.left
                if uncle is not None and uncle.color == RED:
                    self._log(
                        "insert_fixup_recolor",
                        node=node.key,
                        parent=node.parent.key,
                        uncle=uncle.key,
                        grandparent=grandparent.key,
                    )
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                    continue
                if node == node.parent.left:
                    self._log("insert_fixup_triangle", node=node.key, parent=node.parent.key, grandparent=grandparent.key)
                    node = node.parent
                    self._rotate_right(node)
                assert node.parent is not None
                self._log("insert_fixup_line", node=node.key, parent=node.parent.key, grandparent=grandparent.key)
                node.parent.color = BLACK
                grandparent.color = RED
                self._rotate_left(grandparent)
        if self.root is not None:
            self.root.color = BLACK
        self._refresh_upwards(node)

    def _fix_delete(self, node: Node | None, parent: Node | None, node_was_left: bool) -> None:
        current = node
        current_parent = parent
        current_was_left = node_was_left

        while current != self.root and self._color_of(current) == BLACK:
            if current_parent is None:
                break
            is_left_child = current == current_parent.left if current is not None else current_was_left
            if is_left_child:
                sibling = current_parent.right
                if self._color_of(sibling) == RED:
                    assert sibling is not None
                    self._log("delete_fixup_sibling_red", parent=current_parent.key, sibling=sibling.key, side="left")
                    sibling.color = BLACK
                    current_parent.color = RED
                    self._rotate_left(current_parent)
                    sibling = current_parent.right
                if self._color_of(self._left_of(sibling)) == BLACK and self._color_of(self._right_of(sibling)) == BLACK:
                    self._log(
                        "delete_fixup_sibling_black_with_black_children",
                        parent=current_parent.key,
                        sibling=self._node_key(sibling),
                        side="left",
                    )
                    if sibling is not None:
                        sibling.color = RED
                    current = current_parent
                    current_parent = current.parent
                    current_was_left = current_parent is not None and current == current_parent.left
                else:
                    if self._color_of(self._right_of(sibling)) == BLACK:
                        self._log(
                            "delete_fixup_inner_red_outer_black",
                            parent=current_parent.key,
                            sibling=self._node_key(sibling),
                            side="left",
                        )
                        if sibling is not None and sibling.left is not None:
                            sibling.left.color = BLACK
                        if sibling is not None:
                            sibling.color = RED
                            self._rotate_right(sibling)
                        sibling = current_parent.right
                    assert sibling is not None
                    self._log("delete_fixup_outer_red", parent=current_parent.key, sibling=sibling.key, side="left")
                    sibling.color = current_parent.color
                    current_parent.color = BLACK
                    if sibling.right is not None:
                        sibling.right.color = BLACK
                    self._rotate_left(current_parent)
                    current = self.root
                    current_parent = None
            else:
                sibling = current_parent.left
                if self._color_of(sibling) == RED:
                    assert sibling is not None
                    self._log("delete_fixup_sibling_red", parent=current_parent.key, sibling=sibling.key, side="right")
                    sibling.color = BLACK
                    current_parent.color = RED
                    self._rotate_right(current_parent)
                    sibling = current_parent.left
                if self._color_of(self._left_of(sibling)) == BLACK and self._color_of(self._right_of(sibling)) == BLACK:
                    self._log(
                        "delete_fixup_sibling_black_with_black_children",
                        parent=current_parent.key,
                        sibling=self._node_key(sibling),
                        side="right",
                    )
                    if sibling is not None:
                        sibling.color = RED
                    current = current_parent
                    current_parent = current.parent
                    current_was_left = current_parent is not None and current == current_parent.left
                else:
                    if self._color_of(self._left_of(sibling)) == BLACK:
                        self._log(
                            "delete_fixup_inner_red_outer_black",
                            parent=current_parent.key,
                            sibling=self._node_key(sibling),
                            side="right",
                        )
                        if sibling is not None and sibling.right is not None:
                            sibling.right.color = BLACK
                        if sibling is not None:
                            sibling.color = RED
                            self._rotate_left(sibling)
                        sibling = current_parent.left
                    assert sibling is not None
                    self._log("delete_fixup_outer_red", parent=current_parent.key, sibling=sibling.key, side="right")
                    sibling.color = current_parent.color
                    current_parent.color = BLACK
                    if sibling.left is not None:
                        sibling.left.color = BLACK
                    self._rotate_right(current_parent)
                    current = self.root
                    current_parent = None
        if current is not None:
            current.color = BLACK
        self._refresh_upwards(current if current is not None else current_parent)

    def _refresh_upwards(self, node: Node | None) -> None:
        while node is not None:
            self._refresh_size(node)
            node = node.parent

    @staticmethod
    def _color_of(node: Node | None) -> str:
        return BLACK if node is None else node.color

    @staticmethod
    def _left_of(node: Node | None) -> Node | None:
        return None if node is None else node.left

    @staticmethod
    def _right_of(node: Node | None) -> Node | None:
        return None if node is None else node.right

    @staticmethod
    def _size(node: Node | None) -> int:
        return 0 if node is None else node.subtree_size

    def _refresh_size(self, node: Node) -> None:
        node.subtree_size = 1 + self._size(node.left) + self._size(node.right)

    @staticmethod
    def _minimum(node: Node) -> Node:
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _transplant(self, target: Node, replacement: Node | None) -> None:
        if target.parent is None:
            self.root = replacement
        elif target == target.parent.left:
            target.parent.left = replacement
        else:
            target.parent.right = replacement
        if replacement is not None:
            replacement.parent = target.parent

    def _log(self, event: str, **data: object) -> None:
        if not self.trace_enabled:
            return
        self.trace.append({"event": event, **data})

    @staticmethod
    def _node_key(node: Node | None) -> int | None:
        return None if node is None else node.key

    @staticmethod
    def _dot_node_id(path: str) -> str:
        return f"node_{path.lower()}"


def build_tree(values: Iterable[int], *, trace_enabled: bool = False) -> RedBlackTree:
    tree = RedBlackTree(trace_enabled=trace_enabled)
    for value in values:
        tree.insert(value)
    return tree


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_avl_module() -> object:
    global _AVL_MODULE
    if _AVL_MODULE is not None:
        return _AVL_MODULE
    module_path = _project_root() / "projects" / "avl-tree-lab" / "avl_tree_lab.py"
    spec = importlib.util.spec_from_file_location("avl_tree_lab_for_red_black_benchmark", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load AVL tree module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    _AVL_MODULE = module
    return module


def _rotation_count_from_red_black_trace(trace: list[dict[str, object]]) -> int:
    return sum(1 for event in trace if event["event"] in {"rotate_left", "rotate_right"})


def _rotation_count_from_avl_trace(events: list[str]) -> int:
    return sum(1 for event in events if "rotation" in event)


def _benchmark_sequence(sequence: list[int]) -> dict[str, object]:
    rb_tree = build_tree(sequence, trace_enabled=True)
    rb_valid, _, rb_errors = rb_tree.validate()
    if not rb_valid:
        raise ValueError(f"red-black tree benchmark built an invalid tree: {rb_errors}")

    avl_module = _load_avl_module()
    avl_tree = avl_module.build_tree(sequence, trace=True)
    avl_validation = avl_tree.validate()
    if not avl_validation["is_valid"]:
        raise ValueError(f"AVL tree benchmark built an invalid tree: {avl_validation['issues']}")

    return {
        "input_size": len(sequence),
        "red_black": {
            "height": rb_tree.height(),
            "rotation_count": _rotation_count_from_red_black_trace(rb_tree.trace),
            "black_height": rb_tree.black_height(),
        },
        "avl": {
            "height": avl_tree.height(),
            "rotation_count": _rotation_count_from_avl_trace(avl_tree.events),
        },
    }


def _benchmark_rows(cases: dict[str, dict[str, object]]) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for case_name, case in cases.items():
        red_black = case["red_black"]
        avl = case["avl"]
        rows.append(
            {
                "case": case_name,
                "input_size": int(case["input_size"]),
                "red_black_height": int(red_black["height"]),
                "red_black_black_height": int(red_black["black_height"]),
                "red_black_rotation_count": int(red_black["rotation_count"]),
                "avl_height": int(avl["height"]),
                "avl_rotation_count": int(avl["rotation_count"]),
                "height_gap_avl_minus_red_black": int(avl["height"]) - int(red_black["height"]),
                "rotation_gap_avl_minus_red_black": int(avl["rotation_count"]) - int(red_black["rotation_count"]),
            }
        )
    return rows


def _benchmark_csv(rows: list[dict[str, int | str]]) -> str:
    if not rows:
        raise ValueError("benchmark rows cannot be empty")
    fieldnames = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _benchmark_series(counts: list[int], start: int, seed: int) -> dict[str, object]:
    if not counts:
        raise ValueError("benchmark series requires at least one count")
    if any(count <= 0 for count in counts):
        raise ValueError("benchmark series counts must be positive")

    runs: list[dict[str, object]] = []
    rows: list[dict[str, int | str]] = []
    for count in counts:
        ascending = list(range(start, start + count))
        descending = list(reversed(ascending))
        rng = random.Random(seed)
        shuffled = ascending.copy()
        rng.shuffle(shuffled)

        cases = {
            "ascending": _benchmark_sequence(ascending),
            "descending": _benchmark_sequence(descending),
            "shuffled": _benchmark_sequence(shuffled),
        }
        case_rows = _benchmark_rows(cases)
        for row in case_rows:
            rows.append({"series_count": count, **row})

        summary = {
            "count": count,
            "red_black_height_mean": statistics.fmean(case["red_black"]["height"] for case in cases.values()),
            "avl_height_mean": statistics.fmean(case["avl"]["height"] for case in cases.values()),
            "red_black_rotation_mean": statistics.fmean(case["red_black"]["rotation_count"] for case in cases.values()),
            "avl_rotation_mean": statistics.fmean(case["avl"]["rotation_count"] for case in cases.values()),
        }
        summary["height_gap_avl_minus_red_black"] = summary["avl_height_mean"] - summary["red_black_height_mean"]
        summary["rotation_gap_avl_minus_red_black"] = (
            summary["avl_rotation_mean"] - summary["red_black_rotation_mean"]
        )
        runs.append({"count": count, "cases": cases, "summary": summary})

    trend_rows = [run["summary"] for run in runs]
    aggregate = {
        "count_min": min(counts),
        "count_max": max(counts),
        "run_count": len(runs),
        "red_black_height_mean": statistics.fmean(row["red_black_height_mean"] for row in trend_rows),
        "avl_height_mean": statistics.fmean(row["avl_height_mean"] for row in trend_rows),
        "red_black_rotation_mean": statistics.fmean(row["red_black_rotation_mean"] for row in trend_rows),
        "avl_rotation_mean": statistics.fmean(row["avl_rotation_mean"] for row in trend_rows),
    }
    aggregate["height_gap_avl_minus_red_black"] = aggregate["avl_height_mean"] - aggregate["red_black_height_mean"]
    aggregate["rotation_gap_avl_minus_red_black"] = (
        aggregate["avl_rotation_mean"] - aggregate["red_black_rotation_mean"]
    )
    return {"runs": runs, "rows": rows, "aggregate": aggregate}


def _describe_trace_event(event: dict[str, object], index: int) -> str:
    name = str(event["event"])
    if name == "inserted":
        direction = event.get("direction")
        parent = event.get("parent")
        if parent is None:
            return f"{index}. Inserted `{event['key']}` as the root node."
        return f"{index}. Inserted `{event['key']}` as the {direction} child of `{parent}`."
    if name == "insert_duplicate_rejected":
        return f"{index}. Rejected duplicate key `{event['key']}` without changing the tree."
    if name == "insert_fixup_line":
        return (
            f"{index}. Insert fix-up detected a red-red violation for node `{event['node']}` "
            f"with parent `{event['parent']}` and grandparent `{event['grandparent']}`."
        )
    if name == "insert_fixup_triangle":
        return (
            f"{index}. Insert fix-up hit the triangle case at node `{event['node']}` and rotated toward "
            f"parent `{event['parent']}` before the line case."
        )
    if name == "insert_fixup_recolor":
        return (
            f"{index}. Insert fix-up recolored parent `{event['parent']}`, uncle `{event['uncle']}`, "
            f"and grandparent `{event['grandparent']}` to push the violation upward."
        )
    if name == "rotate_left":
        return f"{index}. Rotated left around pivot `{event['pivot']}` so child `{event['child']}` moved up."
    if name == "rotate_right":
        return f"{index}. Rotated right around pivot `{event['pivot']}` so child `{event['child']}` moved up."
    if name == "delete_start":
        return f"{index}. Started deletion for key `{event['key']}`."
    if name == "delete_missing":
        return f"{index}. Delete request for `{event['key']}` was ignored because the key was not present."
    if name == "delete_case_two_children":
        return (
            f"{index}. Node `{event['target']}` had two children, so the algorithm swapped in inorder successor "
            f"`{event['successor']}` before repairing colors."
        )
    if name == "delete_case_black_repair":
        return (
            f"{index}. Removing a black node created a double-black repair path near parent `{event['parent']}`."
        )
    if name == "delete_case_sibling_red":
        return (
            f"{index}. Delete repair found a red sibling `{event['sibling']}` and rotated to convert the case "
            f"into a black-sibling scenario."
        )
    if name == "delete_case_sibling_black_children_black":
        return (
            f"{index}. Delete repair recolored black sibling `{event['sibling']}` because both of its children were black."
        )
    if name == "delete_case_inner_red":
        return (
            f"{index}. Delete repair hit an inner-red nephew case at sibling `{event['sibling']}` and used a preparatory rotation."
        )
    if name == "delete_case_outer_red":
        return (
            f"{index}. Delete repair resolved the double-black issue with an outer-red nephew case at sibling `{event['sibling']}`."
        )
    if name == "delete_complete":
        return f"{index}. Finished deletion for key `{event['key']}`."
    details = ", ".join(f"{key}={value}" for key, value in sorted(event.items()) if key != "event")
    suffix = f" ({details})" if details else ""
    return f"{index}. `{name}`{suffix}."


def command_demo(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree([7, 3, 18, 10, 22, 8, 11, 26], trace_enabled=args.trace)
    payload = {"command": "demo", **tree.summary(include_trace=args.trace)}
    payload["contains"] = {"8": tree.contains(8), "15": tree.contains(15)}
    payload["rank"] = {"8": tree.rank(8), "15": tree.rank(15)}
    payload["select"] = {"0": tree.select(0), "3": tree.select(3)}
    return payload


def command_build(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    return {"command": "build", "input": args.values, **tree.summary(include_trace=args.trace)}


def command_contains(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    return {
        "command": "contains",
        "input": args.values,
        "query": args.query,
        "found": tree.contains(args.query),
        **tree.summary(include_trace=args.trace),
    }


def command_rank(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    return {
        "command": "rank",
        "input": args.values,
        "query": args.query,
        "rank": tree.rank(args.query),
        **tree.summary(include_trace=args.trace),
    }


def command_select(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    selected = tree.select(args.index)
    return {
        "command": "select",
        "input": args.values,
        "index": args.index,
        "selected": selected,
        **tree.summary(include_trace=args.trace),
    }


def command_delete(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    if args.trace:
        tree.trace.clear()
    deleted = tree.delete(args.query)
    return {
        "command": "delete",
        "input": args.values,
        "query": args.query,
        "deleted": deleted,
        **tree.summary(include_trace=args.trace),
    }


def command_dot(args: argparse.Namespace) -> dict[str, object]:
    tree = build_tree(args.values, trace_enabled=args.trace)
    return {
        "command": "dot",
        "input": args.values,
        "include_nil": args.include_nil,
        "dot": tree.to_dot(include_nil=args.include_nil),
        **tree.summary(include_trace=args.trace),
    }


def command_explain_trace(args: argparse.Namespace) -> dict[str, object]:
    deleted = None
    if args.operation == "build":
        tree = RedBlackTree(trace_enabled=True)
        initial_dot = tree.to_dot(include_nil=True)
        for value in args.values:
            tree.insert(value)
    else:
        tree = build_tree(args.values, trace_enabled=True)
        initial_dot = tree.to_dot(include_nil=True)
        tree.trace.clear()
        deleted = tree.delete(args.query)

    summary = tree.summary(include_trace=True)
    final_dot = tree.to_dot(include_nil=True)
    heading = f"# Red-Black Tree Trace Walkthrough ({args.operation})"
    overview = [
        heading,
        "",
        f"- input: `{summary['inorder'] if args.operation == 'delete' and deleted is False else args.values}`",
        f"- size: `{summary['size']}`",
        f"- height: `{summary['height']}`",
        f"- black height: `{summary['black_height']}`",
        f"- valid: `{summary['valid']}`",
    ]
    if args.operation == "delete":
        overview.insert(2, f"- delete query: `{args.query}`")
        overview.insert(3, f"- deleted: `{deleted}`")
    overview.extend(
        [
            "",
            "## Tree snapshots",
            "",
            "### Initial DOT",
            "",
            "```dot",
            initial_dot,
            "```",
            "",
            "### Final DOT",
            "",
            "```dot",
            final_dot,
            "```",
            "",
            "## Event-by-event explanation",
            "",
        ]
    )

    trace_lines = [
        _describe_trace_event(event, index)
        for index, event in enumerate(summary.get("trace", []), start=1)
    ]
    if not trace_lines:
        trace_lines = ["1. No balancing events fired; the operation completed without rotations or repair cases."]

    closing = [
        "",
        "## Final state",
        "",
        f"- root: `{summary['root']}`",
        f"- inorder traversal: `{summary['inorder']}`",
        f"- validation errors: `{summary['errors']}`",
    ]
    markdown = "\n".join(overview + trace_lines + closing) + "\n"

    payload = {
        "command": "explain-trace",
        "operation": args.operation,
        "input": args.values,
        "initial_dot": initial_dot,
        "final_dot": final_dot,
        "markdown": markdown,
        **summary,
    }
    if args.operation == "delete":
        payload["query"] = args.query
        payload["deleted"] = deleted
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        payload["output"] = str(output_path)
    return payload


def command_benchmark(args: argparse.Namespace) -> dict[str, object]:
    if args.count <= 0:
        raise ValueError("benchmark count must be positive")
    series = _benchmark_series([args.count], start=args.start, seed=args.seed)
    run = series["runs"][0]
    payload = {
        "command": "benchmark",
        "count": args.count,
        "seed": args.seed,
        "start": args.start,
        "cases": run["cases"],
        "summary": run["summary"],
    }
    if args.csv or args.csv_file:
        csv_text = _benchmark_csv(_benchmark_rows(run["cases"]))
        payload["csv"] = csv_text
        if args.csv_file:
            csv_path = Path(args.csv_file)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_path.write_text(csv_text, encoding="utf-8")
            payload["csv_file"] = str(csv_path)
    return payload


def command_benchmark_series(args: argparse.Namespace) -> dict[str, object]:
    series = _benchmark_series(args.counts, start=args.start, seed=args.seed)
    payload = {
        "command": "benchmark-series",
        "counts": args.counts,
        "seed": args.seed,
        "start": args.start,
        "runs": series["runs"],
        "aggregate": series["aggregate"],
    }
    if args.csv or args.csv_file:
        csv_text = _benchmark_csv(series["rows"])
        payload["csv"] = csv_text
        if args.csv_file:
            csv_path = Path(args.csv_file)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_path.write_text(csv_text, encoding="utf-8")
            payload["csv_file"] = str(csv_path)
    return payload


def add_trace_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--trace", action="store_true", help="include rotation and fix-up events in the JSON output")


def main() -> None:
    parser = argparse.ArgumentParser(description="Red-black tree insertion, deletion, and validation lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="run a bundled insertion demo")
    add_trace_flag(demo_parser)
    demo_parser.set_defaults(handler=command_demo)

    build_parser = subparsers.add_parser("build", help="build a tree from integer values")
    add_trace_flag(build_parser)
    build_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    build_parser.set_defaults(handler=command_build)

    contains_parser = subparsers.add_parser("contains", help="build a tree and query a key")
    add_trace_flag(contains_parser)
    contains_parser.add_argument("query", type=int, help="integer to search for")
    contains_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    contains_parser.set_defaults(handler=command_contains)

    rank_parser = subparsers.add_parser("rank", help="count how many inserted keys are smaller than the query")
    add_trace_flag(rank_parser)
    rank_parser.add_argument("query", type=int, help="integer to rank")
    rank_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    rank_parser.set_defaults(handler=command_rank)

    select_parser = subparsers.add_parser("select", help="return the zero-based kth smallest key")
    add_trace_flag(select_parser)
    select_parser.add_argument("index", type=int, help="zero-based inorder index")
    select_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    select_parser.set_defaults(handler=command_select)

    delete_parser = subparsers.add_parser("delete", help="build a tree, delete a key, and validate the result")
    add_trace_flag(delete_parser)
    delete_parser.add_argument("query", type=int, help="integer to delete")
    delete_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    delete_parser.set_defaults(handler=command_delete)

    dot_parser = subparsers.add_parser("dot", help="build a tree and emit Graphviz DOT for visualization")
    add_trace_flag(dot_parser)
    dot_parser.add_argument("--no-nil", dest="include_nil", action="store_false", help="omit NIL leaf nodes from DOT output")
    dot_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    dot_parser.set_defaults(handler=command_dot, include_nil=True)

    explain_trace_parser = subparsers.add_parser(
        "explain-trace",
        help="build or mutate a tree and turn the trace stream into a Markdown walkthrough",
    )
    explain_trace_parser.add_argument("operation", choices=("build", "delete"), help="which workflow to narrate")
    explain_trace_parser.add_argument("values", nargs="+", type=int, help="integers to insert")
    explain_trace_parser.add_argument("--query", type=int, help="key to delete when operation=delete")
    explain_trace_parser.add_argument("--output", help="optional Markdown file path for the walkthrough")
    explain_trace_parser.set_defaults(handler=command_explain_trace)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare red-black and AVL insertion outcomes across ascending, descending, and shuffled inputs",
    )
    benchmark_parser.add_argument("--count", type=int, default=31, help="number of sequential integers to insert")
    benchmark_parser.add_argument("--start", type=int, default=1, help="starting integer for the benchmark range")
    benchmark_parser.add_argument("--seed", type=int, default=7, help="random seed for the shuffled benchmark case")
    benchmark_parser.add_argument("--csv", action="store_true", help="include a chart-ready CSV string in the JSON output")
    benchmark_parser.add_argument(
        "--csv-file",
        help="write the benchmark cases to a CSV file for spreadsheet/chart tooling",
    )
    benchmark_parser.set_defaults(handler=command_benchmark)

    benchmark_series_parser = subparsers.add_parser(
        "benchmark-series",
        help="compare red-black and AVL trees across multiple input sizes and insertion orders",
    )
    benchmark_series_parser.add_argument(
        "counts",
        nargs="+",
        type=int,
        help="one or more input sizes to benchmark in ascending/descending/shuffled form",
    )
    benchmark_series_parser.add_argument("--start", type=int, default=1, help="starting integer for the benchmark range")
    benchmark_series_parser.add_argument("--seed", type=int, default=7, help="random seed for the shuffled benchmark case")
    benchmark_series_parser.add_argument(
        "--csv",
        action="store_true",
        help="include a chart-ready CSV string in the JSON output",
    )
    benchmark_series_parser.add_argument(
        "--csv-file",
        help="write the benchmark series rows to a CSV file for spreadsheet/chart tooling",
    )
    benchmark_series_parser.set_defaults(handler=command_benchmark_series)

    args = parser.parse_args()
    if args.command == "explain-trace" and args.operation == "delete" and args.query is None:
        parser.error("explain-trace delete requires --query KEY")
    try:
        payload = args.handler(args)
    except IndexError as error:
        parser.error(str(error))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
