from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


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
        points.sort(key=lambda point: (point.x, point.y, point.label or "") if axis == 0 else (point.y, point.x, point.label or ""))
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
        return sorted(results, key=lambda point: (point.x, point.y, point.label or ""))

    def nearest_neighbor(self, target_x: float, target_y: float) -> Point:
        if self.root is None:
            raise ValueError("cannot query an empty tree")

        best_point = self.root.point
        best_distance = squared_distance(best_point, target_x, target_y)

        def visit(node: Optional[KDNode]) -> None:
            nonlocal best_point, best_distance
            if node is None:
                return
            point = node.point
            distance = squared_distance(point, target_x, target_y)
            if distance < best_distance or (
                math.isclose(distance, best_distance)
                and (point.x, point.y, point.label or "") < (best_point.x, best_point.y, best_point.label or "")
            ):
                best_point = point
                best_distance = distance

            axis_value = target_x if node.axis == 0 else target_y
            split_value = point.x if node.axis == 0 else point.y
            first, second = (node.left, node.right) if axis_value <= split_value else (node.right, node.left)
            visit(first)
            if (axis_value - split_value) ** 2 <= best_distance:
                visit(second)

        visit(self.root)
        return best_point


def squared_distance(point: Point, target_x: float, target_y: float) -> float:
    return (point.x - target_x) ** 2 + (point.y - target_y) ** 2


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

    range_parser = subparsers.add_parser("range", help="Find points inside a rectangle")
    range_parser.add_argument("min_x", type=float)
    range_parser.add_argument("min_y", type=float)
    range_parser.add_argument("max_x", type=float)
    range_parser.add_argument("max_y", type=float)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    points = load_points(args.data)
    tree = KDTree(points)

    if args.command == "nearest":
        point = tree.nearest_neighbor(args.x, args.y)
        print(json.dumps({"query": {"x": args.x, "y": args.y}, "nearest": point.as_dict()}, indent=2))
        return 0

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
