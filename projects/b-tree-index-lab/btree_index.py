from __future__ import annotations

import argparse
import json
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence


@dataclass
class BTreeNode:
    leaf: bool = True
    keys: List[int] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    children: List["BTreeNode"] = field(default_factory=list)


class BTreeIndex:
    def __init__(self, minimum_degree: int = 2) -> None:
        if minimum_degree < 2:
            raise ValueError("minimum_degree must be at least 2")
        self.minimum_degree = minimum_degree
        self.root = BTreeNode()
        self.item_count = 0

    @property
    def max_keys(self) -> int:
        return 2 * self.minimum_degree - 1

    @property
    def min_keys(self) -> int:
        return self.minimum_degree - 1

    def search(self, key: int) -> str | None:
        return self._search(self.root, key)

    def _search(self, node: BTreeNode, key: int) -> str | None:
        index = bisect_left(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            return node.values[index]
        if node.leaf:
            return None
        return self._search(node.children[index], key)

    def insert(self, key: int, value: str) -> None:
        root = self.root
        if len(root.keys) == self.max_keys:
            new_root = BTreeNode(leaf=False, children=[root])
            self._split_child(new_root, 0)
            self.root = new_root
        inserted_new_key = self._insert_non_full(self.root, key, value)
        if inserted_new_key:
            self.item_count += 1

    def _insert_non_full(self, node: BTreeNode, key: int, value: str) -> bool:
        index = bisect_left(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            node.values[index] = value
            return False

        if node.leaf:
            node.keys.insert(index, key)
            node.values.insert(index, value)
            return True

        child = node.children[index]
        if len(child.keys) == self.max_keys:
            self._split_child(node, index)
            if key == node.keys[index]:
                node.values[index] = value
                return False
            if key > node.keys[index]:
                index += 1
        return self._insert_non_full(node.children[index], key, value)

    def _split_child(self, parent: BTreeNode, child_index: int) -> None:
        child = parent.children[child_index]
        middle = self.minimum_degree - 1
        promoted_key = child.keys[middle]
        promoted_value = child.values[middle]

        sibling = BTreeNode(
            leaf=child.leaf,
            keys=child.keys[middle + 1 :],
            values=child.values[middle + 1 :],
            children=child.children[middle + 1 :] if not child.leaf else [],
        )

        child.keys = child.keys[:middle]
        child.values = child.values[:middle]
        if not child.leaf:
            child.children = child.children[: middle + 1]

        parent.keys.insert(child_index, promoted_key)
        parent.values.insert(child_index, promoted_value)
        parent.children.insert(child_index + 1, sibling)

    def delete(self, key: int) -> bool:
        deleted = self._delete(self.root, key)
        if not deleted:
            return False

        self.item_count -= 1
        if not self.root.leaf and not self.root.keys:
            self.root = self.root.children[0]
        return True

    def _delete(self, node: BTreeNode, key: int) -> bool:
        index = bisect_left(node.keys, key)

        if index < len(node.keys) and node.keys[index] == key:
            if node.leaf:
                del node.keys[index]
                del node.values[index]
                return True
            return self._delete_from_internal(node, index)

        if node.leaf:
            return False

        child_index = index
        child = node.children[child_index]
        if len(child.keys) == self.min_keys:
            child_index = self._ensure_child_has_capacity(node, child_index)
            child = node.children[child_index]
        return self._delete(child, key)

    def _delete_from_internal(self, node: BTreeNode, index: int) -> bool:
        key = node.keys[index]
        left_child = node.children[index]
        right_child = node.children[index + 1]

        if len(left_child.keys) >= self.minimum_degree:
            predecessor_key, predecessor_value = self._get_predecessor(left_child)
            node.keys[index] = predecessor_key
            node.values[index] = predecessor_value
            return self._delete(left_child, predecessor_key)

        if len(right_child.keys) >= self.minimum_degree:
            successor_key, successor_value = self._get_successor(right_child)
            node.keys[index] = successor_key
            node.values[index] = successor_value
            return self._delete(right_child, successor_key)

        merged_child = self._merge_children(node, index)
        return self._delete(merged_child, key)

    def _get_predecessor(self, node: BTreeNode) -> tuple[int, str]:
        current = node
        while not current.leaf:
            current = current.children[-1]
        return current.keys[-1], current.values[-1]

    def _get_successor(self, node: BTreeNode) -> tuple[int, str]:
        current = node
        while not current.leaf:
            current = current.children[0]
        return current.keys[0], current.values[0]

    def _ensure_child_has_capacity(self, parent: BTreeNode, child_index: int) -> int:
        child = parent.children[child_index]
        if len(child.keys) >= self.minimum_degree:
            return child_index

        if child_index > 0 and len(parent.children[child_index - 1].keys) >= self.minimum_degree:
            self._borrow_from_left(parent, child_index)
            return child_index

        if child_index < len(parent.children) - 1 and len(parent.children[child_index + 1].keys) >= self.minimum_degree:
            self._borrow_from_right(parent, child_index)
            return child_index

        if child_index < len(parent.children) - 1:
            self._merge_children(parent, child_index)
            return child_index

        self._merge_children(parent, child_index - 1)
        return child_index - 1

    def _borrow_from_left(self, parent: BTreeNode, child_index: int) -> None:
        child = parent.children[child_index]
        left_sibling = parent.children[child_index - 1]

        child.keys.insert(0, parent.keys[child_index - 1])
        child.values.insert(0, parent.values[child_index - 1])
        if not child.leaf:
            child.children.insert(0, left_sibling.children.pop())

        parent.keys[child_index - 1] = left_sibling.keys.pop()
        parent.values[child_index - 1] = left_sibling.values.pop()

    def _borrow_from_right(self, parent: BTreeNode, child_index: int) -> None:
        child = parent.children[child_index]
        right_sibling = parent.children[child_index + 1]

        child.keys.append(parent.keys[child_index])
        child.values.append(parent.values[child_index])
        if not child.leaf:
            child.children.append(right_sibling.children.pop(0))

        parent.keys[child_index] = right_sibling.keys.pop(0)
        parent.values[child_index] = right_sibling.values.pop(0)

    def _merge_children(self, parent: BTreeNode, left_index: int) -> BTreeNode:
        left_child = parent.children[left_index]
        right_child = parent.children[left_index + 1]

        left_child.keys.append(parent.keys.pop(left_index))
        left_child.values.append(parent.values.pop(left_index))
        left_child.keys.extend(right_child.keys)
        left_child.values.extend(right_child.values)
        if not left_child.leaf:
            left_child.children.extend(right_child.children)

        del parent.children[left_index + 1]
        return left_child

    def items(self) -> List[dict[str, str | int]]:
        result: List[dict[str, str | int]] = []
        self._collect_items(self.root, result)
        return result

    def _collect_items(self, node: BTreeNode, result: List[dict[str, str | int]]) -> None:
        for index, key in enumerate(node.keys):
            if not node.leaf:
                self._collect_items(node.children[index], result)
            result.append({"key": key, "value": node.values[index]})
        if not node.leaf:
            self._collect_items(node.children[-1], result)

    def range_query(self, start: int | None = None, end: int | None = None) -> List[dict[str, str | int]]:
        if start is not None and end is not None and start > end:
            raise ValueError("start cannot be greater than end")
        return [
            item
            for item in self.items()
            if (start is None or item["key"] >= start) and (end is None or item["key"] <= end)
        ]

    def height(self) -> int:
        height = 1
        node = self.root
        while not node.leaf:
            height += 1
            node = node.children[0]
        return height

    def stats(self) -> dict[str, int]:
        return {
            "minimum_degree": self.minimum_degree,
            "items": self.item_count,
            "height": self.height(),
            "nodes": self._count_nodes(self.root),
            "root_keys": len(self.root.keys),
        }

    def _count_nodes(self, node: BTreeNode) -> int:
        return 1 + sum(self._count_nodes(child) for child in node.children)

    @classmethod
    def from_records(cls, records: Sequence[dict[str, object]], minimum_degree: int = 2) -> "BTreeIndex":
        tree = cls(minimum_degree=minimum_degree)
        for record in records:
            if "key" not in record or "value" not in record:
                raise ValueError("each record must include key and value")
            tree.insert(int(record["key"]), str(record["value"]))
        return tree



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="B-tree index lab")
    parser.add_argument("--dataset", type=Path, help="JSON file of [{\"key\": int, \"value\": str}] records")
    parser.add_argument("--degree", type=int, default=2, help="Minimum B-tree degree (default: 2)")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("command", nargs="*", help="search KEY | range START END | delete KEY | stats | dump")
    return parser


def _run_command(tree: BTreeIndex, command: Sequence[str]) -> dict[str, object]:
    if not command or command[0] == "dump":
        return {"items": tree.items(), "stats": tree.stats()}

    action = command[0]
    if action == "search":
        if len(command) != 2:
            raise ValueError("search requires exactly 1 key")
        key = int(command[1])
        return {"key": key, "value": tree.search(key)}
    if action == "range":
        if len(command) != 3:
            raise ValueError("range requires START END")
        start, end = int(command[1]), int(command[2])
        return {"items": tree.range_query(start, end), "stats": tree.stats()}
    if action == "delete":
        if len(command) != 2:
            raise ValueError("delete requires exactly 1 key")
        key = int(command[1])
        return {"key": key, "deleted": tree.delete(key), "items": tree.items(), "stats": tree.stats()}
    if action == "stats":
        return {"stats": tree.stats()}
    raise ValueError(f"unsupported command: {action}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    records = json.loads(args.dataset.read_text()) if args.dataset else []
    tree = BTreeIndex.from_records(records, minimum_degree=args.degree)
    result = _run_command(tree, args.command)
    if args.json or args.dataset:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
