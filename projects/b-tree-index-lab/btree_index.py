from __future__ import annotations

import argparse
import json
import struct
import time
from bisect import bisect_left
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Sequence


FILE_MAGIC = b"BTRE"
FILE_VERSION = 1
HEADER_STRUCT = struct.Struct(">4sBHIHIII8x")
PAGE_HEADER_STRUCT = struct.Struct(">BHIH8x")
CHILD_POINTER_STRUCT = struct.Struct(">I")
EMPTY_CHILD_POINTER = 0xFFFFFFFF
DEFAULT_PAGE_SIZE = 512
DEFAULT_VALUE_BYTES = 32


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

    @property
    def max_children(self) -> int:
        return 2 * self.minimum_degree

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

    def floor_item(self, key: int) -> dict[str, str | int] | None:
        return self._extreme_bound_item(key, want_floor=True)

    def ceil_item(self, key: int) -> dict[str, str | int] | None:
        return self._extreme_bound_item(key, want_floor=False)

    def neighbors(self, key: int) -> dict[str, dict[str, str | int] | None]:
        return {
            "key": key,
            "floor": self.floor_item(key),
            "ceil": self.ceil_item(key),
        }

    def _extreme_bound_item(self, key: int, want_floor: bool) -> dict[str, str | int] | None:
        node = self.root
        candidate: dict[str, str | int] | None = None

        while True:
            index = bisect_left(node.keys, key)

            if index < len(node.keys) and node.keys[index] == key:
                return {"key": node.keys[index], "value": node.values[index]}

            if want_floor and index > 0:
                candidate = {"key": node.keys[index - 1], "value": node.values[index - 1]}
            elif not want_floor and index < len(node.keys):
                candidate = {"key": node.keys[index], "value": node.values[index]}

            if node.leaf:
                return candidate

            node = node.children[index]

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "minimum_degree": self.minimum_degree,
            "item_count": self.item_count,
            "root": self._node_to_dict(self.root),
        }

    def _node_to_dict(self, node: BTreeNode) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "leaf": node.leaf,
            "keys": list(node.keys),
            "values": list(node.values),
        }
        if not node.leaf:
            payload["children"] = [self._node_to_dict(child) for child in node.children]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BTreeIndex":
        if "minimum_degree" not in payload or "root" not in payload:
            raise ValueError("serialized tree must include minimum_degree and root")

        tree = cls(minimum_degree=int(payload["minimum_degree"]))
        tree.root = cls._node_from_dict(payload["root"])
        tree.item_count = int(payload.get("item_count", len(tree.items())))
        tree._validate_structure()
        if tree.item_count != len(tree.items()):
            raise ValueError("serialized item_count does not match stored keys")
        return tree

    @classmethod
    def _node_from_dict(cls, payload: dict[str, Any]) -> BTreeNode:
        leaf = bool(payload.get("leaf", True))
        keys = [int(key) for key in payload.get("keys", [])]
        values = [str(value) for value in payload.get("values", [])]
        if len(keys) != len(values):
            raise ValueError("serialized node must have matching key/value counts")
        children_payload = payload.get("children", [])
        if leaf and children_payload:
            raise ValueError("leaf nodes cannot contain children")
        children = [cls._node_from_dict(child) for child in children_payload]
        node = BTreeNode(leaf=leaf, keys=keys, values=values, children=children)
        if not leaf and len(children) != len(keys) + 1:
            raise ValueError("internal node must have len(children) == len(keys) + 1")
        return node

    def _validate_structure(self) -> None:
        items = self.items()
        keys = [item["key"] for item in items]
        if keys != sorted(keys):
            raise ValueError("serialized tree keys must be globally sorted")
        if len(keys) != len(set(keys)):
            raise ValueError("serialized tree keys must be unique")
        self._validate_node(self.root, is_root=True, lower_bound=None, upper_bound=None)

    def _validate_node(
        self,
        node: BTreeNode,
        *,
        is_root: bool,
        lower_bound: int | None,
        upper_bound: int | None,
    ) -> None:
        if node.keys != sorted(node.keys):
            raise ValueError("node keys must be sorted")
        if len(node.keys) > self.max_keys:
            raise ValueError("node exceeds maximum key capacity")
        if not is_root and len(node.keys) < self.min_keys:
            raise ValueError("node violates minimum key capacity")
        if lower_bound is not None and any(key <= lower_bound for key in node.keys):
            raise ValueError("node contains keys at or below its lower bound")
        if upper_bound is not None and any(key >= upper_bound for key in node.keys):
            raise ValueError("node contains keys at or above its upper bound")
        if node.leaf:
            if node.children:
                raise ValueError("leaf nodes cannot have children")
            return
        if len(node.children) != len(node.keys) + 1:
            raise ValueError("internal node must have exactly len(keys)+1 children")
        for index, child in enumerate(node.children):
            child_lower = lower_bound if index == 0 else node.keys[index - 1]
            child_upper = upper_bound if index == len(node.keys) else node.keys[index]
            self._validate_node(child, is_root=False, lower_bound=child_lower, upper_bound=child_upper)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        return path

    @classmethod
    def load(cls, path: Path) -> "BTreeIndex":
        return cls.from_dict(json.loads(path.read_text()))

    def page_layout(self, *, page_size: int = DEFAULT_PAGE_SIZE, value_bytes: int = DEFAULT_VALUE_BYTES) -> dict[str, int]:
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if value_bytes < 2:
            raise ValueError("value_bytes must be at least 2")
        required = (
            PAGE_HEADER_STRUCT.size
            + (self.max_keys * 8)
            + (self.max_keys * value_bytes)
            + (self.max_children * CHILD_POINTER_STRUCT.size)
        )
        if required > page_size:
            raise ValueError(
                f"page_size={page_size} is too small for minimum_degree={self.minimum_degree}; need at least {required} bytes"
            )
        return {
            "minimum_degree": self.minimum_degree,
            "page_size": page_size,
            "value_bytes": value_bytes,
            "max_keys": self.max_keys,
            "max_children": self.max_children,
            "header_bytes": HEADER_STRUCT.size,
            "page_header_bytes": PAGE_HEADER_STRUCT.size,
            "required_page_bytes": required,
            "padding_bytes": page_size - required,
        }

    def save_paged(
        self,
        path: Path,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        value_bytes: int = DEFAULT_VALUE_BYTES,
    ) -> Path:
        layout = self.page_layout(page_size=page_size, value_bytes=value_bytes)
        pages: list[tuple[int, BTreeNode]] = []
        page_ids: dict[int, int] = {}
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            marker = id(node)
            if marker in page_ids:
                continue
            page_id = len(pages)
            page_ids[marker] = page_id
            pages.append((page_id, node))
            queue.extend(node.children)

        blob = bytearray()
        blob.extend(
            HEADER_STRUCT.pack(
                FILE_MAGIC,
                FILE_VERSION,
                self.minimum_degree,
                page_size,
                value_bytes,
                page_ids[id(self.root)],
                len(pages),
                self.item_count,
            )
        )
        for page_id, node in pages:
            blob.extend(self._encode_page(node, page_id=page_id, page_size=page_size, value_bytes=value_bytes, page_ids=page_ids))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(blob))
        return path

    def _encode_page(
        self,
        node: BTreeNode,
        *,
        page_id: int,
        page_size: int,
        value_bytes: int,
        page_ids: dict[int, int],
    ) -> bytes:
        payload = bytearray(PAGE_HEADER_STRUCT.pack(1 if node.leaf else 0, len(node.keys), page_id, len(node.children)))
        for index in range(self.max_keys):
            key = node.keys[index] if index < len(node.keys) else 0
            payload.extend(struct.pack(">q", key))
        slot_payload_bytes = value_bytes - 2
        for index in range(self.max_keys):
            raw = node.values[index].encode("utf-8") if index < len(node.values) else b""
            if len(raw) > slot_payload_bytes:
                raise ValueError(
                    f"value '{node.values[index]}' exceeds fixed slot capacity of {slot_payload_bytes} UTF-8 bytes"
                )
            payload.extend(struct.pack(">H", len(raw)))
            payload.extend(raw)
            payload.extend(b"\x00" * (slot_payload_bytes - len(raw)))
        child_ids = [page_ids[id(child)] for child in node.children]
        for index in range(self.max_children):
            child_id = child_ids[index] if index < len(child_ids) else EMPTY_CHILD_POINTER
            payload.extend(CHILD_POINTER_STRUCT.pack(child_id))
        if len(payload) > page_size:
            raise ValueError("encoded page exceeded page_size after validation")
        payload.extend(b"\x00" * (page_size - len(payload)))
        return bytes(payload)

    @classmethod
    def load_paged(cls, path: Path) -> "BTreeIndex":
        raw = path.read_bytes()
        if len(raw) < HEADER_STRUCT.size:
            raise ValueError("paged tree file is too small to contain a header")
        magic, version, minimum_degree, page_size, value_bytes, root_page_id, page_count, item_count = HEADER_STRUCT.unpack(
            raw[: HEADER_STRUCT.size]
        )
        if magic != FILE_MAGIC:
            raise ValueError("paged tree file has an invalid magic header")
        if version != FILE_VERSION:
            raise ValueError(f"unsupported paged tree version: {version}")
        tree = cls(minimum_degree=minimum_degree)
        layout = tree.page_layout(page_size=page_size, value_bytes=value_bytes)
        expected_size = HEADER_STRUCT.size + (page_count * page_size)
        if len(raw) != expected_size:
            raise ValueError("paged tree file length does not match header metadata")
        if root_page_id >= page_count:
            raise ValueError("root page id is outside the page table")

        page_records: list[dict[str, Any]] = []
        offset = HEADER_STRUCT.size
        for _ in range(page_count):
            page_records.append(tree._decode_page(raw[offset : offset + page_size], value_bytes=value_bytes, layout=layout))
            offset += page_size

        nodes_by_page_id: dict[int, BTreeNode] = {}
        seen_page_ids: set[int] = set()
        for record in page_records:
            page_id = record["page_id"]
            if page_id in seen_page_ids:
                raise ValueError("paged tree file contains duplicate page ids")
            seen_page_ids.add(page_id)
            if page_id >= page_count:
                raise ValueError("page id is outside the page table")
            nodes_by_page_id[page_id] = BTreeNode(leaf=record["leaf"], keys=record["keys"], values=record["values"])

        for record in page_records:
            page_id = record["page_id"]
            node = nodes_by_page_id[page_id]
            child_ids = record["child_ids"]
            if node.leaf and child_ids:
                raise ValueError("leaf pages cannot contain child pointers")
            if not node.leaf and len(child_ids) != len(node.keys) + 1:
                raise ValueError("internal page must have len(children) == len(keys) + 1")
            try:
                node.children = [nodes_by_page_id[child_id] for child_id in child_ids]
            except KeyError as error:
                raise ValueError("paged tree file references a missing child page") from error

        if seen_page_ids != set(range(page_count)):
            raise ValueError("paged tree file must contain contiguous page ids starting at zero")

        tree.root = nodes_by_page_id[root_page_id]
        tree.item_count = item_count
        tree._validate_structure()
        if tree.item_count != len(tree.items()):
            raise ValueError("paged item_count does not match stored keys")
        return tree

    def _decode_page(self, page: bytes, *, value_bytes: int, layout: dict[str, int]) -> dict[str, Any]:
        leaf_flag, key_count, page_id, child_count = PAGE_HEADER_STRUCT.unpack(page[: PAGE_HEADER_STRUCT.size])
        if key_count > self.max_keys:
            raise ValueError("page key_count exceeds B-tree capacity")
        if child_count > self.max_children:
            raise ValueError("page child_count exceeds B-tree capacity")
        if leaf_flag and child_count != 0:
            raise ValueError("leaf page must not advertise children")
        if not leaf_flag and child_count == 0 and key_count > 0:
            raise ValueError("internal page must advertise child pointers")

        offset = PAGE_HEADER_STRUCT.size
        keys = []
        for index in range(self.max_keys):
            (key,) = struct.unpack(">q", page[offset : offset + 8])
            if index < key_count:
                keys.append(key)
            offset += 8

        values = []
        slot_payload_bytes = value_bytes - 2
        for index in range(self.max_keys):
            (length,) = struct.unpack(">H", page[offset : offset + 2])
            if length > slot_payload_bytes:
                raise ValueError("page contains an oversized value slot")
            offset += 2
            raw_value = page[offset : offset + slot_payload_bytes]
            if index < key_count:
                values.append(raw_value[:length].decode("utf-8"))
            offset += slot_payload_bytes

        child_ids = []
        for index in range(self.max_children):
            (child_id,) = CHILD_POINTER_STRUCT.unpack(page[offset : offset + CHILD_POINTER_STRUCT.size])
            if index < child_count:
                if child_id == EMPTY_CHILD_POINTER:
                    raise ValueError("active child pointer cannot use the empty sentinel")
                child_ids.append(child_id)
            offset += CHILD_POINTER_STRUCT.size

        if offset != layout["required_page_bytes"]:
            raise ValueError("page layout decoding drift detected")
        return {
            "leaf": bool(leaf_flag),
            "page_id": page_id,
            "keys": keys,
            "values": values,
            "child_ids": child_ids,
        }

    @staticmethod
    def _normalize_record(record: dict[str, object]) -> tuple[int, str]:
        if "key" not in record or "value" not in record:
            raise ValueError("each record must include key and value")
        return int(record["key"]), str(record["value"])

    def _append_sorted(self, key: int, value: str) -> None:
        root = self.root
        if len(root.keys) == self.max_keys:
            new_root = BTreeNode(leaf=False, children=[root])
            self._split_child(new_root, 0)
            self.root = new_root
        self._append_sorted_non_full(self.root, key, value)
        self.item_count += 1

    def _append_sorted_non_full(self, node: BTreeNode, key: int, value: str) -> None:
        if node.leaf:
            node.keys.append(key)
            node.values.append(value)
            return

        child_index = len(node.children) - 1
        child = node.children[child_index]
        if len(child.keys) == self.max_keys:
            self._split_child(node, child_index)
            child_index = len(node.children) - 1
        self._append_sorted_non_full(node.children[child_index], key, value)

    @classmethod
    def bulk_load_sorted(cls, records: Sequence[dict[str, object]], minimum_degree: int = 2) -> "BTreeIndex":
        tree = cls(minimum_degree=minimum_degree)
        previous_key: int | None = None
        for record in records:
            key, value = tree._normalize_record(record)
            if previous_key is not None and key <= previous_key:
                raise ValueError("bulk_load_sorted requires strictly increasing keys")
            tree._append_sorted(key, value)
            previous_key = key
        return tree

    @classmethod
    def from_records(
        cls,
        records: Sequence[dict[str, object]],
        minimum_degree: int = 2,
        *,
        presorted: bool = False,
    ) -> "BTreeIndex":
        if presorted:
            return cls.bulk_load_sorted(records, minimum_degree=minimum_degree)

        tree = cls(minimum_degree=minimum_degree)
        for record in records:
            key, value = tree._normalize_record(record)
            tree.insert(key, value)
        return tree

    @classmethod
    def benchmark_builds(
        cls,
        records: Sequence[dict[str, object]],
        minimum_degree: int = 2,
        *,
        repeats: int = 5,
    ) -> dict[str, object]:
        if repeats < 1:
            raise ValueError("repeats must be at least 1")

        normalized = []
        previous_key: int | None = None
        for record in records:
            key, value = cls._normalize_record(record)
            if previous_key is not None and key <= previous_key:
                raise ValueError("benchmark_builds requires strictly increasing keys")
            normalized.append({"key": key, "value": value})
            previous_key = key

        baseline_tree = cls.from_records(normalized, minimum_degree=minimum_degree)
        bulk_tree = cls.from_records(normalized, minimum_degree=minimum_degree, presorted=True)
        if baseline_tree.items() != bulk_tree.items():
            raise ValueError("bulk-load benchmark produced mismatched tree contents")

        baseline_runs_ns = []
        bulk_runs_ns = []
        for _ in range(repeats):
            started = time.perf_counter_ns()
            cls.from_records(normalized, minimum_degree=minimum_degree)
            baseline_runs_ns.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            cls.from_records(normalized, minimum_degree=minimum_degree, presorted=True)
            bulk_runs_ns.append(time.perf_counter_ns() - started)

        baseline_avg_ns = sum(baseline_runs_ns) / repeats
        bulk_avg_ns = sum(bulk_runs_ns) / repeats
        speedup = (baseline_avg_ns / bulk_avg_ns) if bulk_avg_ns else None
        return {
            "dataset_items": len(normalized),
            "minimum_degree": minimum_degree,
            "repeats": repeats,
            "baseline_insert": {
                "avg_ms": round(baseline_avg_ns / 1_000_000, 3),
                "runs_ms": [round(run / 1_000_000, 3) for run in baseline_runs_ns],
                "stats": baseline_tree.stats(),
            },
            "bulk_load": {
                "avg_ms": round(bulk_avg_ns / 1_000_000, 3),
                "runs_ms": [round(run / 1_000_000, 3) for run in bulk_runs_ns],
                "stats": bulk_tree.stats(),
            },
            "speedup_vs_insert": round(speedup, 3) if speedup is not None else None,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="B-tree index lab")
    parser.add_argument("--dataset", type=Path, help="JSON file of [{\"key\": int, \"value\": str}] records")
    parser.add_argument("--tree-file", type=Path, help="Serialized B-tree JSON generated by the save command")
    parser.add_argument("--page-file", type=Path, help="Binary fixed-size page file generated by the save-pages command")
    parser.add_argument("--degree", type=int, default=2, help="Minimum B-tree degree (default: 2)")
    parser.add_argument("--bulk-load", action="store_true", help="Treat dataset as strictly sorted and build via append-only bulk loading")
    parser.add_argument("--benchmark-repeats", type=int, default=5, help="Benchmark repetitions for the benchmark-build command (default: 5)")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help=f"Fixed page size in bytes for save-pages/page-layout (default: {DEFAULT_PAGE_SIZE})")
    parser.add_argument("--value-bytes", type=int, default=DEFAULT_VALUE_BYTES, help=f"Fixed bytes reserved per value, including a 2-byte length prefix (default: {DEFAULT_VALUE_BYTES})")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "command",
        nargs="*",
        help="search KEY | range START END | floor KEY | ceil KEY | neighbors KEY | delete KEY | save PATH | save-pages PATH | page-layout | snapshot | stats | benchmark-build | dump",
    )
    return parser



def _load_tree(args: argparse.Namespace) -> BTreeIndex:
    selected_sources = [args.dataset is not None, args.tree_file is not None, args.page_file is not None]
    if sum(selected_sources) > 1:
        raise ValueError("use exactly one of --dataset, --tree-file, or --page-file")
    if args.bulk_load and not args.dataset:
        raise ValueError("--bulk-load requires --dataset")
    if args.tree_file:
        return BTreeIndex.load(args.tree_file)
    if args.page_file:
        return BTreeIndex.load_paged(args.page_file)
    records = json.loads(args.dataset.read_text()) if args.dataset else []
    return BTreeIndex.from_records(records, minimum_degree=args.degree, presorted=args.bulk_load)



def _run_command(tree: BTreeIndex, command: Sequence[str], args: argparse.Namespace | None = None) -> dict[str, object]:
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
    if action == "floor":
        if len(command) != 2:
            raise ValueError("floor requires exactly 1 key")
        key = int(command[1])
        return {"key": key, "item": tree.floor_item(key)}
    if action == "ceil":
        if len(command) != 2:
            raise ValueError("ceil requires exactly 1 key")
        key = int(command[1])
        return {"key": key, "item": tree.ceil_item(key)}
    if action == "neighbors":
        if len(command) != 2:
            raise ValueError("neighbors requires exactly 1 key")
        key = int(command[1])
        return tree.neighbors(key)
    if action == "save":
        if len(command) != 2:
            raise ValueError("save requires exactly 1 output path")
        output_path = Path(command[1])
        tree.save(output_path)
        return {"saved": str(output_path), "stats": tree.stats()}
    if action == "save-pages":
        if len(command) != 2:
            raise ValueError("save-pages requires exactly 1 output path")
        if args is None:
            raise ValueError("save-pages requires parser args")
        output_path = Path(command[1])
        tree.save_paged(output_path, page_size=args.page_size, value_bytes=args.value_bytes)
        return {
            "saved": str(output_path),
            "encoding": tree.page_layout(page_size=args.page_size, value_bytes=args.value_bytes),
            "stats": tree.stats(),
        }
    if action == "page-layout":
        if args is None:
            raise ValueError("page-layout requires parser args")
        return {"layout": tree.page_layout(page_size=args.page_size, value_bytes=args.value_bytes), "stats": tree.stats()}
    if action == "snapshot":
        return {"tree": tree.to_dict(), "stats": tree.stats()}
    if action == "stats":
        return {"stats": tree.stats()}
    if action == "benchmark-build":
        repeats = args.benchmark_repeats if args is not None else 5
        return {"benchmark": BTreeIndex.benchmark_builds(tree.items(), minimum_degree=tree.minimum_degree, repeats=repeats)}
    raise ValueError(f"unsupported command: {action}")



def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    tree = _load_tree(args)
    result = _run_command(tree, args.command, args)
    if args.json or args.dataset or args.tree_file or args.page_file:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
