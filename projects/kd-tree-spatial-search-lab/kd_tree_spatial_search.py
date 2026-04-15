from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    label: str | None = None

    def as_dict(self) -> dict:
        data = {"x": self.x, "y": self.y}
        if self.label is not None:
            data["label"] = self.label
        return data


@dataclass
class KDNode:
    point: Point
    axis: int
    left: Optional["KDNode"] = None
    right: Optional["KDNode"] = None


class KDTree:
    def __init__(self, points: Iterable[Point]):
        materialized = list(points)
        self.root = self._build(materialized, depth=0)
        self.size = len(materialized)

    def _build(self, points: List[Point], depth: int) -> Optional[KDNode]:
        if not points:
            return None
        axis = depth % 2
        points.sort(key=sort_key_for_axis(axis))
        median = len(points) // 2
        return KDNode(
            point=points[median],
            axis=axis,
            left=self._build(points[:median], depth + 1),
            right=self._build(points[median + 1 :], depth + 1),
        )

    def range_query(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[Point]:
        if min_x > max_x or min_y > max_y:
            raise ValueError("invalid rectangle bounds")
        results: List[Point] = []

        def visit(node: Optional[KDNode]) -> None:
            if node is None:
                return
            point = node.point
            if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                results.append(point)
            split_value = point.x if node.axis == 0 else point.y
            low = min_x if node.axis == 0 else min_y
            high = max_x if node.axis == 0 else max_y
            if low <= split_value:
                visit(node.left)
            if split_value <= high:
                visit(node.right)

        visit(self.root)
        return sorted(results, key=point_sort_key)

    def nearest_neighbor(self, target_x: float, target_y: float) -> Point:
        return self.k_nearest_neighbors(target_x, target_y, k=1)[0]

    def k_nearest_neighbors(self, target_x: float, target_y: float, k: int) -> List[Point]:
        if self.root is None:
            raise ValueError("cannot query an empty tree")
        if k <= 0:
            raise ValueError("k must be positive")

        limit = min(k, self.size)
        best_heap: list[tuple[float, tuple[float, float, tuple[int, ...]], int, Point]] = []
        sequence = itertools.count()

        def push_candidate(point: Point) -> None:
            key = point_sort_key(point)
            entry = (-squared_distance(point, target_x, target_y), invert_sort_key(key), next(sequence), point)
            if len(best_heap) < limit:
                heapq.heappush(best_heap, entry)
                return
            if entry > best_heap[0]:
                heapq.heapreplace(best_heap, entry)

        def axis_gap_within_best(node: KDNode) -> bool:
            if len(best_heap) < limit:
                return True
            axis_value = target_x if node.axis == 0 else target_y
            split_value = node.point.x if node.axis == 0 else node.point.y
            worst_distance = -best_heap[0][0]
            return (axis_value - split_value) ** 2 <= worst_distance

        def visit(node: Optional[KDNode]) -> None:
            if node is None:
                return
            push_candidate(node.point)
            axis_value = target_x if node.axis == 0 else target_y
            split_value = node.point.x if node.axis == 0 else node.point.y
            first, second = (node.left, node.right) if axis_value <= split_value else (node.right, node.left)
            visit(first)
            if axis_gap_within_best(node):
                visit(second)

        visit(self.root)
        return [entry[3] for entry in sorted(best_heap, key=lambda item: (-item[0], point_sort_key(item[3])))]


def point_sort_key(point: Point) -> tuple[float, float, str]:
    return (point.x, point.y, point.label or "")


def sort_key_for_axis(axis: int):
    if axis == 0:
        return lambda point: point_sort_key(point)
    return lambda point: (point.y, point.x, point.label or "")


def invert_sort_key(key: tuple[float, float, str]) -> tuple[float, float, tuple[int, ...]]:
    return (-key[0], -key[1], tuple(-ord(char) for char in key[2]))


def squared_distance(point: Point, target_x: float, target_y: float) -> float:
    return (point.x - target_x) ** 2 + (point.y - target_y) ** 2


def brute_force_k_nearest(points: Iterable[Point], target_x: float, target_y: float, k: int) -> List[Point]:
    materialized = list(points)
    if not materialized:
        raise ValueError("cannot query an empty point set")
    if k <= 0:
        raise ValueError("k must be positive")
    ranked = sorted(materialized, key=lambda point: (squared_distance(point, target_x, target_y), point_sort_key(point)))
    return ranked[: min(k, len(ranked))]


def benchmark_nearest_search(points: Iterable[Point], query_count: int, k: int = 1, seed: int = 42) -> dict:
    materialized = list(points)
    if not materialized:
        raise ValueError("cannot benchmark an empty point set")
    if query_count <= 0:
        raise ValueError("query_count must be positive")
    if k <= 0:
        raise ValueError("k must be positive")

    min_x = min(point.x for point in materialized)
    max_x = max(point.x for point in materialized)
    min_y = min(point.y for point in materialized)
    max_y = max(point.y for point in materialized)
    rng = random.Random(seed)
    queries = [(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y)) for _ in range(query_count)]

    tree = KDTree(materialized)

    kd_start = time.perf_counter()
    kd_results = [tree.k_nearest_neighbors(x, y, k=k) for x, y in queries]
    kd_seconds = time.perf_counter() - kd_start

    brute_start = time.perf_counter()
    brute_results = [brute_force_k_nearest(materialized, x, y, k=k) for x, y in queries]
    brute_seconds = time.perf_counter() - brute_start

    if kd_results != brute_results:
        raise AssertionError("kd-tree and brute-force results diverged during benchmark")

    return {
        "query_count": query_count,
        "k": min(k, len(materialized)),
        "seed": seed,
        "bounds": {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y},
        "kd_tree_seconds": round(kd_seconds, 6),
        "brute_force_seconds": round(brute_seconds, 6),
        "speedup": None if kd_seconds == 0 else round(brute_seconds / kd_seconds, 3),
    }


def load_points(path: Path) -> List[Point]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("point file must contain a JSON list")
    points: List[Point] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or "x" not in item or "y" not in item:
            raise ValueError(f"invalid point at index {index}")
        label = item.get("label")
        points.append(Point(float(item["x"]), float(item["y"]), None if label is None else str(label)))
    return points


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KD-tree spatial search lab")
    parser.add_argument("data", type=Path, help="Path to a JSON file containing points")
    subparsers = parser.add_subparsers(dest="command", required=True)

    nearest = subparsers.add_parser("nearest", help="Find the nearest point")
    nearest.add_argument("x", type=float)
    nearest.add_argument("y", type=float)

    knearest = subparsers.add_parser("knearest", help="Find the k nearest points")
    knearest.add_argument("x", type=float)
    knearest.add_argument("y", type=float)
    knearest.add_argument("k", type=int)

    range_parser = subparsers.add_parser("range", help="Find points inside a rectangle")
    range_parser.add_argument("min_x", type=float)
    range_parser.add_argument("min_y", type=float)
    range_parser.add_argument("max_x", type=float)
    range_parser.add_argument("max_y", type=float)

    benchmark = subparsers.add_parser("benchmark", help="Compare KD-tree nearest-neighbor queries against brute force")
    benchmark.add_argument("--queries", type=int, default=1000, help="Number of random queries to run")
    benchmark.add_argument("--k", type=int, default=1, help="How many nearest neighbors to compare")
    benchmark.add_argument("--seed", type=int, default=42, help="Random seed for reproducible query generation")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    points = load_points(args.data)

    if args.command == "nearest":
        tree = KDTree(points)
        point = tree.nearest_neighbor(args.x, args.y)
        print(json.dumps({"query": {"x": args.x, "y": args.y}, "nearest": point.as_dict()}, indent=2))
        return 0

    if args.command == "knearest":
        tree = KDTree(points)
        matches = tree.k_nearest_neighbors(args.x, args.y, args.k)
        print(
            json.dumps(
                {"query": {"x": args.x, "y": args.y, "k": args.k}, "count": len(matches), "matches": [point.as_dict() for point in matches]},
                indent=2,
            )
        )
        return 0

    if args.command == "benchmark":
        print(json.dumps(benchmark_nearest_search(points, query_count=args.queries, k=args.k, seed=args.seed), indent=2))
        return 0

    tree = KDTree(points)
    matches = tree.range_query(args.min_x, args.min_y, args.max_x, args.max_y)
    print(
        json.dumps(
            {
                "query": {"min_x": args.min_x, "min_y": args.min_y, "max_x": args.max_x, "max_y": args.max_y},
                "count": len(matches),
                "matches": [point.as_dict() for point in matches],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
