from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, order=True)
class Interval:
    start: int
    end: int
    label: str | None = None

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"invalid interval [{self.start}, {self.end}]")

    def overlaps(self, other: "Interval") -> bool:
        return self.start <= other.end and other.start <= self.end

    def contains_point(self, point: int) -> bool:
        return self.start <= point <= self.end

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"start": self.start, "end": self.end}
        if self.label is not None:
            payload["label"] = self.label
        return payload


@dataclass
class Node:
    interval: Interval
    max_end: int
    left: Node | None = None
    right: Node | None = None


class IntervalTree:
    def __init__(self, intervals: Iterable[Interval] = ()) -> None:
        unique = sorted(set(intervals))
        self.root = self._build_balanced(unique)
        self.size = len(unique)

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[int, int, str | None]]) -> "IntervalTree":
        return cls(Interval(start, end, label) for start, end, label in pairs)

    def insert(self, interval: Interval) -> bool:
        inserted, self.root = self._insert(self.root, interval)
        if inserted:
            self.size += 1
        return inserted

    def overlaps_any(self, query: Interval) -> bool:
        return self.find_any_overlap(query) is not None

    def find_any_overlap(self, query: Interval) -> Interval | None:
        node = self.root
        while node is not None:
            if node.interval.overlaps(query):
                return node.interval
            if node.left is not None and node.left.max_end >= query.start:
                node = node.left
            else:
                node = node.right
        return None

    def find_overlaps(self, query: Interval) -> list[Interval]:
        results: list[Interval] = []
        self._collect_overlaps(self.root, query, results)
        return results

    def find_point(self, point: int) -> list[Interval]:
        return self.find_overlaps(Interval(point, point))

    def inorder(self) -> list[Interval]:
        items: list[Interval] = []

        def walk(node: Node | None) -> None:
            if node is None:
                return
            walk(node.left)
            items.append(node.interval)
            walk(node.right)

        walk(self.root)
        return items

    def height(self) -> int:
        def walk(node: Node | None) -> int:
            if node is None:
                return 0
            return 1 + max(walk(node.left), walk(node.right))

        return walk(self.root)

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []

        def walk(node: Node | None, lower: Interval | None, upper: Interval | None) -> int:
            if node is None:
                return float("-inf")
            if lower is not None and node.interval <= lower:
                errors.append(
                    f"BST ordering violated at {node.interval.to_dict()}: interval must be > lower bound {lower.to_dict()}"
                )
            if upper is not None and node.interval >= upper:
                errors.append(
                    f"BST ordering violated at {node.interval.to_dict()}: interval must be < upper bound {upper.to_dict()}"
                )
            left_max = walk(node.left, lower, node.interval)
            right_max = walk(node.right, node.interval, upper)
            expected_max = max(node.interval.end, left_max, right_max)
            if node.max_end != expected_max:
                errors.append(
                    f"max_end mismatch at {node.interval.to_dict()}: expected {expected_max}, got {node.max_end}"
                )
            return expected_max

        walk(self.root, None, None)
        return len(errors) == 0, errors

    def summary(self) -> dict[str, object]:
        valid, errors = self.validate()
        return {
            "size": self.size,
            "height": self.height(),
            "root": None if self.root is None else self.root.interval.to_dict(),
            "max_end": None if self.root is None else self.root.max_end,
            "inorder": [interval.to_dict() for interval in self.inorder()],
            "valid": valid,
            "errors": errors,
        }

    def _build_balanced(self, intervals: list[Interval]) -> Node | None:
        if not intervals:
            return None
        mid = len(intervals) // 2
        node = Node(interval=intervals[mid], max_end=intervals[mid].end)
        node.left = self._build_balanced(intervals[:mid])
        node.right = self._build_balanced(intervals[mid + 1 :])
        self._refresh(node)
        return node

    def _insert(self, node: Node | None, interval: Interval) -> tuple[bool, Node]:
        if node is None:
            return True, Node(interval=interval, max_end=interval.end)
        if interval == node.interval:
            return False, node
        if interval < node.interval:
            inserted, node.left = self._insert(node.left, interval)
        else:
            inserted, node.right = self._insert(node.right, interval)
        if inserted:
            self._refresh(node)
        return inserted, node

    def _collect_overlaps(self, node: Node | None, query: Interval, results: list[Interval]) -> None:
        if node is None:
            return
        if node.left is not None and node.left.max_end >= query.start:
            self._collect_overlaps(node.left, query, results)
        if node.interval.overlaps(query):
            results.append(node.interval)
        if node.right is not None and node.interval.start <= query.end:
            self._collect_overlaps(node.right, query, results)

    @staticmethod
    def _refresh(node: Node) -> None:
        node.max_end = max(
            node.interval.end,
            float("-inf") if node.left is None else node.left.max_end,
            float("-inf") if node.right is None else node.right.max_end,
        )


def parse_interval_spec(spec: str) -> Interval:
    body, _, label = spec.partition(":")
    start_text, sep, end_text = body.partition("-")
    if not sep:
        raise ValueError(f"interval '{spec}' must look like start-end or start-end:label")
    return Interval(int(start_text), int(end_text), label or None)


def load_intervals(args_specs: Iterable[str]) -> list[Interval]:
    return [parse_interval_spec(spec) for spec in args_specs]


def command_demo(_: argparse.Namespace) -> dict[str, object]:
    intervals = [
        Interval(0, 3, "warmup"),
        Interval(5, 8, "db-backup"),
        Interval(6, 10, "deploy"),
        Interval(8, 9, "qa"),
        Interval(15, 23, "analytics"),
        Interval(16, 21, "report"),
        Interval(17, 19, "alert-window"),
        Interval(19, 20, "maintenance"),
        Interval(25, 30, "etl"),
        Interval(26, 26, "ping"),
    ]
    tree = IntervalTree(intervals)
    query = Interval(7, 18, "query")
    point = 26
    return {
        "command": "demo",
        "query": query.to_dict(),
        "point": point,
        "any_overlap": None if tree.find_any_overlap(query) is None else tree.find_any_overlap(query).to_dict(),
        "all_overlaps": [interval.to_dict() for interval in tree.find_overlaps(query)],
        "point_hits": [interval.to_dict() for interval in tree.find_point(point)],
        **tree.summary(),
    }


def command_build(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    return {"command": "build", "input": args.intervals, **tree.summary()}


def command_overlap(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    query = parse_interval_spec(args.query)
    any_overlap = tree.find_any_overlap(query)
    return {
        "command": "overlap",
        "input": args.intervals,
        "query": query.to_dict(),
        "any_overlap": None if any_overlap is None else any_overlap.to_dict(),
        "all_overlaps": [interval.to_dict() for interval in tree.find_overlaps(query)],
        **tree.summary(),
    }


def command_point(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    return {
        "command": "point",
        "input": args.intervals,
        "point": args.point,
        "hits": [interval.to_dict() for interval in tree.find_point(args.point)],
        **tree.summary(),
    }


def command_insert(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    interval = parse_interval_spec(args.interval)
    inserted = tree.insert(interval)
    return {
        "command": "insert",
        "input": args.intervals,
        "interval": interval.to_dict(),
        "inserted": inserted,
        **tree.summary(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Interval tree lab for overlap and stabbing queries")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="run a bundled interval tree demo")
    demo_parser.set_defaults(handler=command_demo)

    build_parser = subparsers.add_parser("build", help="build a tree from interval specs like 5-8 or 5-8:deploy")
    build_parser.add_argument("intervals", nargs="+", help="interval specs")
    build_parser.set_defaults(handler=command_build)

    overlap_parser = subparsers.add_parser("overlap", help="find overlaps for a query interval")
    overlap_parser.add_argument("query", help="query interval spec")
    overlap_parser.add_argument("intervals", nargs="+", help="interval specs")
    overlap_parser.set_defaults(handler=command_overlap)

    point_parser = subparsers.add_parser("point", help="find which intervals contain a point")
    point_parser.add_argument("point", type=int, help="point to probe")
    point_parser.add_argument("intervals", nargs="+", help="interval specs")
    point_parser.set_defaults(handler=command_point)

    insert_parser = subparsers.add_parser("insert", help="insert one interval into a built tree")
    insert_parser.add_argument("interval", help="interval to insert")
    insert_parser.add_argument("intervals", nargs="+", help="interval specs")
    insert_parser.set_defaults(handler=command_insert)

    args = parser.parse_args()
    try:
        payload = args.handler(args)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
