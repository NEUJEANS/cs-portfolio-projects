from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class NodeValue:
    total: int = 0
    minimum: int = 0
    maximum: int = 0

    def to_dict(self) -> dict:
        return {"sum": self.total, "min": self.minimum, "max": self.maximum}


class SegmentTree:
    """Segment tree with lazy propagation for range-add and range-set updates."""

    def __init__(self, values: Iterable[int]):
        self.values = list(values)
        if not self.values:
            raise ValueError("segment tree requires at least one value")
        size = 4 * len(self.values)
        self.sum_tree = [0] * size
        self.min_tree = [0] * size
        self.max_tree = [0] * size
        self.lazy_add = [0] * size
        self.lazy_set: List[Optional[int]] = [None] * size
        self._build(1, 0, len(self.values) - 1)

    def _build(self, index: int, left: int, right: int) -> None:
        if left == right:
            value = self.values[left]
            self.sum_tree[index] = value
            self.min_tree[index] = value
            self.max_tree[index] = value
            return
        mid = (left + right) // 2
        self._build(index * 2, left, mid)
        self._build(index * 2 + 1, mid + 1, right)
        self._pull(index)

    def _pull(self, index: int) -> None:
        left_child = index * 2
        right_child = left_child + 1
        self.sum_tree[index] = self.sum_tree[left_child] + self.sum_tree[right_child]
        self.min_tree[index] = min(self.min_tree[left_child], self.min_tree[right_child])
        self.max_tree[index] = max(self.max_tree[left_child], self.max_tree[right_child])

    def _apply_add(self, index: int, left: int, right: int, delta: int) -> None:
        self.sum_tree[index] += (right - left + 1) * delta
        self.min_tree[index] += delta
        self.max_tree[index] += delta
        if self.lazy_set[index] is not None:
            self.lazy_set[index] += delta
        else:
            self.lazy_add[index] += delta

    def _apply_set(self, index: int, left: int, right: int, value: int) -> None:
        self.sum_tree[index] = (right - left + 1) * value
        self.min_tree[index] = value
        self.max_tree[index] = value
        self.lazy_set[index] = value
        self.lazy_add[index] = 0

    def _push(self, index: int, left: int, right: int) -> None:
        if left == right:
            self.lazy_set[index] = None
            self.lazy_add[index] = 0
            return
        mid = (left + right) // 2
        left_child = index * 2
        right_child = left_child + 1
        pending_set = self.lazy_set[index]
        if pending_set is not None:
            self._apply_set(left_child, left, mid, pending_set)
            self._apply_set(right_child, mid + 1, right, pending_set)
            self.lazy_set[index] = None
        pending_add = self.lazy_add[index]
        if pending_add:
            self._apply_add(left_child, left, mid, pending_add)
            self._apply_add(right_child, mid + 1, right, pending_add)
            self.lazy_add[index] = 0

    def range_add(self, query_left: int, query_right: int, delta: int) -> None:
        self._validate_range(query_left, query_right)
        self._range_add(1, 0, len(self.values) - 1, query_left, query_right, delta)

    def _range_add(self, index: int, left: int, right: int, query_left: int, query_right: int, delta: int) -> None:
        if query_left <= left and right <= query_right:
            self._apply_add(index, left, right, delta)
            return
        self._push(index, left, right)
        mid = (left + right) // 2
        if query_left <= mid:
            self._range_add(index * 2, left, mid, query_left, query_right, delta)
        if query_right > mid:
            self._range_add(index * 2 + 1, mid + 1, right, query_left, query_right, delta)
        self._pull(index)

    def range_set(self, query_left: int, query_right: int, value: int) -> None:
        self._validate_range(query_left, query_right)
        self._range_set(1, 0, len(self.values) - 1, query_left, query_right, value)

    def _range_set(self, index: int, left: int, right: int, query_left: int, query_right: int, value: int) -> None:
        if query_left <= left and right <= query_right:
            self._apply_set(index, left, right, value)
            return
        self._push(index, left, right)
        mid = (left + right) // 2
        if query_left <= mid:
            self._range_set(index * 2, left, mid, query_left, query_right, value)
        if query_right > mid:
            self._range_set(index * 2 + 1, mid + 1, right, query_left, query_right, value)
        self._pull(index)

    def point_set(self, position: int, value: int) -> None:
        if position < 0 or position >= len(self.values):
            raise IndexError("position out of range")
        self.range_set(position, position, value)

    def range_query(self, query_left: int, query_right: int) -> NodeValue:
        self._validate_range(query_left, query_right)
        return self._range_query(1, 0, len(self.values) - 1, query_left, query_right)

    def _range_query(self, index: int, left: int, right: int, query_left: int, query_right: int) -> NodeValue:
        if query_left <= left and right <= query_right:
            return NodeValue(
                total=self.sum_tree[index],
                minimum=self.min_tree[index],
                maximum=self.max_tree[index],
            )
        self._push(index, left, right)
        mid = (left + right) // 2
        if query_right <= mid:
            return self._range_query(index * 2, left, mid, query_left, query_right)
        if query_left > mid:
            return self._range_query(index * 2 + 1, mid + 1, right, query_left, query_right)
        left_result = self._range_query(index * 2, left, mid, query_left, query_right)
        right_result = self._range_query(index * 2 + 1, mid + 1, right, query_left, query_right)
        return NodeValue(
            total=left_result.total + right_result.total,
            minimum=min(left_result.minimum, right_result.minimum),
            maximum=max(left_result.maximum, right_result.maximum),
        )

    def materialize(self) -> List[int]:
        return [self.range_query(index, index).total for index in range(len(self.values))]

    def explain_query(self, query_left: int, query_right: int) -> dict:
        materialized = self.materialize()
        result = self.range_query(query_left, query_right)
        return {
            "range": [query_left, query_right],
            "length": query_right - query_left + 1,
            "values": materialized[query_left : query_right + 1],
            "result": result.to_dict(),
        }

    def _validate_range(self, query_left: int, query_right: int) -> None:
        if query_left < 0 or query_right >= len(self.values):
            raise IndexError("query range out of bounds")
        if query_left > query_right:
            raise ValueError("left bound cannot exceed right bound")


def parse_numbers(raw: str) -> List[int]:
    values = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
    if not values:
        raise ValueError("provide at least one integer")
    return [int(value) for value in values]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Segment tree range-query lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("sample", help="run the bundled sample")
    sample_parser.add_argument("--json", action="store_true", help="print JSON output")

    query_parser = subparsers.add_parser("query", help="query a range")
    query_parser.add_argument("--numbers", required=True, help="comma-separated integers")
    query_parser.add_argument("--left", type=int, required=True)
    query_parser.add_argument("--right", type=int, required=True)

    update_parser = subparsers.add_parser("range-add", help="apply a range-add update and inspect state")
    update_parser.add_argument("--numbers", required=True, help="comma-separated integers")
    update_parser.add_argument("--left", type=int, required=True)
    update_parser.add_argument("--right", type=int, required=True)
    update_parser.add_argument("--delta", type=int, required=True)

    assign_parser = subparsers.add_parser("range-set", help="assign a value across a range")
    assign_parser.add_argument("--numbers", required=True, help="comma-separated integers")
    assign_parser.add_argument("--left", type=int, required=True)
    assign_parser.add_argument("--right", type=int, required=True)
    assign_parser.add_argument("--value", type=int, required=True)

    set_parser = subparsers.add_parser("point-set", help="set a single value")
    set_parser.add_argument("--numbers", required=True, help="comma-separated integers")
    set_parser.add_argument("--index", type=int, required=True)
    set_parser.add_argument("--value", type=int, required=True)

    return parser


def run_sample(as_json: bool = False) -> str:
    values = [2, 1, 3, 4, 5, 7, 9, 11]
    tree = SegmentTree(values)
    before = tree.explain_query(2, 6)
    tree.range_add(1, 4, 3)
    after_range_add = tree.explain_query(2, 6)
    tree.range_set(3, 5, 6)
    after_range_set = tree.explain_query(2, 6)
    payload = {
        "input": values,
        "before": before,
        "after_range_add": after_range_add,
        "after_range_set": after_range_set,
        "updated_values": tree.materialize(),
    }
    if as_json:
        return json.dumps(payload, indent=2)
    updated_values = tree.materialize()
    return (
        f"Input: {values}\n"
        f"Range [2, 6] before update: {before['result']}\n"
        f"Applied +3 to [1, 4]\n"
        f"Range [2, 6] after range-add: {after_range_add['result']}\n"
        f"Assigned 6 to [3, 5]\n"
        f"Range [2, 6] after range-set: {after_range_set['result']}\n"
        f"Updated values: {updated_values}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sample":
        print(run_sample(as_json=args.json))
        return 0

    values = parse_numbers(args.numbers)
    tree = SegmentTree(values)

    if args.command == "query":
        print(json.dumps(tree.explain_query(args.left, args.right), indent=2))
        return 0

    if args.command == "range-add":
        before = tree.explain_query(args.left, args.right)
        tree.range_add(args.left, args.right, args.delta)
        after = tree.explain_query(args.left, args.right)
        print(
            json.dumps(
                {
                    "before": before,
                    "delta": args.delta,
                    "after": after,
                    "updated_values": tree.materialize(),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "range-set":
        before = tree.explain_query(args.left, args.right)
        tree.range_set(args.left, args.right, args.value)
        after = tree.explain_query(args.left, args.right)
        print(
            json.dumps(
                {
                    "before": before,
                    "value": args.value,
                    "after": after,
                    "updated_values": tree.materialize(),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "point-set":
        tree.point_set(args.index, args.value)
        print(json.dumps({"updated_values": tree.materialize()}, indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
