from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    label: str | None = None

    def to_dict(self) -> dict:
        data = {"x": self.x, "y": self.y}
        if self.label is not None:
            data["label"] = self.label
        return data


@dataclass(frozen=True)
class Rectangle:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("rectangle bounds must satisfy min <= max")

    def contains_point(self, point: Point) -> bool:
        return (
            self.min_x <= point.x <= self.max_x
            and self.min_y <= point.y <= self.max_y
        )

    def intersects(self, other: "Rectangle") -> bool:
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def distance_to_point(self, point: Point) -> float:
        dx = 0.0
        if point.x < self.min_x:
            dx = self.min_x - point.x
        elif point.x > self.max_x:
            dx = point.x - self.max_x

        dy = 0.0
        if point.y < self.min_y:
            dy = self.min_y - point.y
        elif point.y > self.max_y:
            dy = point.y - self.max_y

        return math.hypot(dx, dy)


class Quadtree:
    def __init__(
        self,
        boundary: Rectangle,
        *,
        capacity: int = 4,
        max_depth: int = 8,
        depth: int = 0,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.depth = depth
        self.points: list[Point] = []
        self.children: list[Quadtree] | None = None

    def insert(self, point: Point) -> bool:
        if not self.boundary.contains_point(point):
            return False

        if self.children is None:
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append(point)
                return True
            self._subdivide()

        assert self.children is not None
        for child in self.children:
            if child.insert(point):
                return True

        raise RuntimeError("point inside boundary but could not be inserted into any child")

    def point_count(self) -> int:
        total = len(self.points)
        if self.children:
            total += sum(child.point_count() for child in self.children)
        return total

    def node_count(self) -> int:
        total = 1
        if self.children:
            total += sum(child.node_count() for child in self.children)
        return total

    def max_observed_depth(self) -> int:
        if not self.children:
            return self.depth
        return max(child.max_observed_depth() for child in self.children)

    def range_query(self, area: Rectangle) -> list[Point]:
        matches: list[Point] = []
        self._range_query(area, matches)
        return matches

    def nearest_neighbor(self, target: Point) -> Optional[Point]:
        best_ref: list[tuple[float, Point] | None] = [None]
        self._nearest_neighbor(target, best_ref=best_ref)
        final = best_ref[0]
        return None if final is None else final[1]

    def _nearest_neighbor(
        self,
        target: Point,
        *,
        best_ref: list[tuple[float, Point] | None],
    ) -> None:
        best = best_ref[0]
        if best is not None and self.boundary.distance_to_point(target) > best[0]:
            return

        for point in self.points:
            distance = euclidean_distance(point, target)
            if best is None or distance < best[0]:
                best = (distance, point)
                best_ref[0] = best

        if not self.children:
            return

        ordered_children = sorted(
            self.children,
            key=lambda child: child.boundary.distance_to_point(target),
        )
        for child in ordered_children:
            child._nearest_neighbor(target, best_ref=best_ref)

    def _range_query(self, area: Rectangle, matches: list[Point]) -> None:
        if not self.boundary.intersects(area):
            return

        matches.extend(point for point in self.points if area.contains_point(point))

        if self.children is None:
            return

        for child in self.children:
            child._range_query(area, matches)

    def _subdivide(self) -> None:
        mid_x = (self.boundary.min_x + self.boundary.max_x) / 2
        mid_y = (self.boundary.min_y + self.boundary.max_y) / 2

        self.children = [
            Quadtree(Rectangle(self.boundary.min_x, mid_y, mid_x, self.boundary.max_y), capacity=self.capacity, max_depth=self.max_depth, depth=self.depth + 1),  # nw
            Quadtree(Rectangle(mid_x, mid_y, self.boundary.max_x, self.boundary.max_y), capacity=self.capacity, max_depth=self.max_depth, depth=self.depth + 1),  # ne
            Quadtree(Rectangle(self.boundary.min_x, self.boundary.min_y, mid_x, mid_y), capacity=self.capacity, max_depth=self.max_depth, depth=self.depth + 1),  # sw
            Quadtree(Rectangle(mid_x, self.boundary.min_y, self.boundary.max_x, mid_y), capacity=self.capacity, max_depth=self.max_depth, depth=self.depth + 1),  # se
        ]
        existing_points = self.points
        self.points = []
        for point in existing_points:
            inserted = False
            for child in self.children:
                if child.insert(point):
                    inserted = True
                    break
            if not inserted:
                raise RuntimeError("existing point could not be redistributed after subdivision")


def euclidean_distance(left: Point, right: Point) -> float:
    return math.hypot(left.x - right.x, left.y - right.y)


def build_quadtree(
    points: Iterable[Point],
    boundary: Rectangle,
    *,
    capacity: int = 4,
    max_depth: int = 8,
) -> Quadtree:
    tree = Quadtree(boundary, capacity=capacity, max_depth=max_depth)
    for point in points:
        if not tree.insert(point):
            raise ValueError(f"point outside boundary: {point}")
    return tree


def load_points(path: Path) -> list[Point]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError("points file must be a JSON list")

    points: list[Point] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"point #{index} must be an object")
        try:
            x = float(item["x"])
            y = float(item["y"])
        except KeyError as exc:
            raise ValueError(f"point #{index} missing coordinate: {exc.args[0]}") from exc
        label_value = item.get("label")
        label = None if label_value is None else str(label_value)
        points.append(Point(x=x, y=y, label=label))
    return points


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Point-region quadtree demo")
    parser.add_argument("points", type=Path, help="path to JSON list of points")
    parser.add_argument("--boundary", nargs=4, type=float, metavar=("MIN_X", "MIN_Y", "MAX_X", "MAX_Y"), required=True)
    parser.add_argument("--capacity", type=int, default=4)
    parser.add_argument("--max-depth", type=int, default=8)

    subparsers = parser.add_subparsers(dest="command", required=True)

    range_parser = subparsers.add_parser("range", help="run a rectangle range query")
    range_parser.add_argument("--area", nargs=4, type=float, metavar=("MIN_X", "MIN_Y", "MAX_X", "MAX_Y"), required=True)

    nearest_parser = subparsers.add_parser("nearest", help="find nearest point to a target")
    nearest_parser.add_argument("--target", nargs=2, type=float, metavar=("X", "Y"), required=True)

    subparsers.add_parser("stats", help="print quadtree shape statistics")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    points = load_points(args.points)
    boundary = Rectangle(*args.boundary)
    tree = build_quadtree(points, boundary, capacity=args.capacity, max_depth=args.max_depth)

    if args.command == "range":
        area = Rectangle(*args.area)
        results = [point.to_dict() for point in tree.range_query(area)]
        print(json.dumps({"matches": results}, indent=2))
        return 0

    if args.command == "nearest":
        target = Point(args.target[0], args.target[1])
        match = tree.nearest_neighbor(target)
        print(json.dumps({"nearest": None if match is None else match.to_dict()}, indent=2))
        return 0

    if args.command == "stats":
        print(
            json.dumps(
                {
                    "points": tree.point_count(),
                    "nodes": tree.node_count(),
                    "max_depth_reached": tree.max_observed_depth(),
                    "capacity": tree.capacity,
                    "configured_max_depth": tree.max_depth,
                },
                indent=2,
            )
        )
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
