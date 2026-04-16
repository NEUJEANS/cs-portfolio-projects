from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable, Sequence
from xml.sax.saxutils import escape as xml_escape


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


@dataclass(frozen=True)
class QueryStats:
    nodes_visited: int

    def to_dict(self) -> dict[str, int]:
        return {"nodes_visited": self.nodes_visited}


@dataclass(frozen=True)
class ExplainStep:
    node: dict[str, object]
    depth: int
    overlap: bool
    left_action: str
    right_action: str
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "node": self.node,
            "depth": self.depth,
            "overlap": self.overlap,
            "left_action": self.left_action,
            "right_action": self.right_action,
            "reasons": self.reasons,
        }


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

    def delete(self, interval: Interval) -> bool:
        deleted, self.root = self._delete(self.root, interval)
        if deleted:
            self.size -= 1
        return deleted

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
        return self.find_overlaps_with_stats(query)[0]

    def find_overlaps_with_stats(self, query: Interval) -> tuple[list[Interval], QueryStats]:
        results: list[Interval] = []
        nodes_visited = self._collect_overlaps(self.root, query, results)
        return results, QueryStats(nodes_visited=nodes_visited)

    def naive_find_overlaps(self, query: Interval) -> list[Interval]:
        return [interval for interval in self.inorder() if interval.overlaps(query)]

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

    def explain_overlap_query(self, query: Interval) -> dict[str, object]:
        overlaps, stats = self.find_overlaps_with_stats(query)
        steps: list[ExplainStep] = []

        def walk(node: Node | None, depth: int) -> None:
            if node is None:
                return
            overlap = node.interval.overlaps(query)
            left_searchable = node.left is not None and node.left.max_end >= query.start
            right_searchable = node.right is not None and node.interval.start <= query.end
            left_action = "skip-empty"
            right_action = "skip-empty"
            reasons: list[str] = []

            if node.left is not None:
                if left_searchable:
                    left_action = "search"
                    reasons.append(
                        f"search left because left.max_end={node.left.max_end} reaches query.start={query.start}"
                    )
                else:
                    left_action = "prune"
                    reasons.append(
                        f"prune left because left.max_end={node.left.max_end} is below query.start={query.start}"
                    )
            if node.right is not None:
                if right_searchable:
                    right_action = "search"
                    reasons.append(
                        f"search right because node.start={node.interval.start} is at or before query.end={query.end}"
                    )
                else:
                    right_action = "prune"
                    reasons.append(
                        f"prune right because node.start={node.interval.start} is after query.end={query.end}"
                    )
            if overlap:
                reasons.insert(0, "current node overlaps the query, so include it in the result set")
            else:
                reasons.insert(0, "current node does not overlap the query")

            steps.append(
                ExplainStep(
                    node=node.interval.to_dict(),
                    depth=depth,
                    overlap=overlap,
                    left_action=left_action,
                    right_action=right_action,
                    reasons=reasons,
                )
            )
            if left_searchable:
                walk(node.left, depth + 1)
            if right_searchable:
                walk(node.right, depth + 1)

        walk(self.root, 0)
        return {
            "query": query.to_dict(),
            "matches": [interval.to_dict() for interval in overlaps],
            "query_stats": stats.to_dict(),
            "steps": [step.to_dict() for step in steps],
        }

    def export_query_trace_dot(self, query: Interval) -> str:
        lines = [
            "digraph interval_tree_query_trace {",
            '  rankdir="TB";',
            '  node [shape=record, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            f'  query [shape=note, style="filled", fillcolor="#eef2ff", label="query|[{query.start}, {query.end}]{_label_suffix(query.label)}"];',
        ]
        if self.root is None:
            lines.append('  empty [label="empty tree"];')
            lines.append('  query -> empty [style=dashed];')
            lines.append("}")
            return "\n".join(lines)

        counter = 0

        def walk(node: Node | None) -> tuple[str | None, int]:
            nonlocal counter
            if node is None:
                return None, 0
            node_id = f"node_{counter}"
            counter += 1

            overlap = node.interval.overlaps(query)
            left_relevant = node.left is not None and node.left.max_end >= query.start
            right_relevant = node.right is not None and node.interval.start <= query.end
            pruned_left = node.left is not None and not left_relevant
            pruned_right = node.right is not None and not right_relevant
            was_visited = overlap or left_relevant or right_relevant or node is self.root
            fill = "#dcfce7" if overlap else "#f8fafc"
            penwidth = 2 if was_visited else 1

            lines.append(
                "  "
                + f'{node_id} [style="filled", fillcolor="{fill}", penwidth={penwidth}, '
                + 'label="'
                + _dot_escape(
                    f"[{node.interval.start}, {node.interval.end}]{_label_suffix(node.interval.label)}"
                    + f"|max_end={node.max_end}"
                )
                + '"];'
            )
            if overlap:
                lines.append(f'  query -> {node_id} [style=dashed, color="#16a34a", label="overlap"];')

            left_id, left_visits = walk(node.left)
            right_id, right_visits = walk(node.right)

            if left_id is not None:
                edge_style = "solid" if left_relevant else "dashed"
                edge_color = "#2563eb" if left_relevant else "#94a3b8"
                edge_label = "search left" if left_relevant else "pruned: left.max_end < query.start"
                lines.append(
                    f'  {node_id} -> {left_id} [color="{edge_color}", style="{edge_style}", label="{_dot_escape(edge_label)}"];'
                )
            if right_id is not None:
                edge_style = "solid" if right_relevant else "dashed"
                edge_color = "#2563eb" if right_relevant else "#94a3b8"
                edge_label = "search right" if right_relevant else "pruned: node.start > query.end"
                lines.append(
                    f'  {node_id} -> {right_id} [color="{edge_color}", style="{edge_style}", label="{_dot_escape(edge_label)}"];'
                )

            nodes_visited = 1
            if left_relevant:
                nodes_visited += left_visits
            if right_relevant:
                nodes_visited += right_visits
            if pruned_left or pruned_right:
                lines.append(f'  {node_id} [xlabel="visited={nodes_visited}"];')
            return node_id, nodes_visited

        root_id, _ = walk(self.root)
        lines.append('  root_anchor [shape=point, width=0.01, label=""];')
        if root_id is not None:
            lines.append(f"  root_anchor -> {root_id};")
        lines.append("}")
        return "\n".join(lines)

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

    def _delete(self, node: Node | None, interval: Interval) -> tuple[bool, Node | None]:
        if node is None:
            return False, None
        if interval < node.interval:
            deleted, node.left = self._delete(node.left, interval)
            if deleted:
                self._refresh(node)
            return deleted, node
        if interval > node.interval:
            deleted, node.right = self._delete(node.right, interval)
            if deleted:
                self._refresh(node)
            return deleted, node

        if node.left is None:
            return True, node.right
        if node.right is None:
            return True, node.left

        successor, new_right = self._pop_min(node.right)
        node.interval = successor.interval
        node.right = new_right
        self._refresh(node)
        return True, node

    def _pop_min(self, node: Node) -> tuple[Node, Node | None]:
        if node.left is None:
            return node, node.right
        successor, node.left = self._pop_min(node.left)
        self._refresh(node)
        return successor, node

    def _collect_overlaps(self, node: Node | None, query: Interval, results: list[Interval]) -> int:
        if node is None:
            return 0
        nodes_visited = 1
        if node.left is not None and node.left.max_end >= query.start:
            nodes_visited += self._collect_overlaps(node.left, query, results)
        if node.interval.overlaps(query):
            results.append(node.interval)
        if node.right is not None and node.interval.start <= query.end:
            nodes_visited += self._collect_overlaps(node.right, query, results)
        return nodes_visited

    @staticmethod
    def _refresh(node: Node) -> None:
        node.max_end = max(
            node.interval.end,
            float("-inf") if node.left is None else node.left.max_end,
            float("-inf") if node.right is None else node.right.max_end,
        )


def _label_suffix(label: str | None) -> str:
    return "" if label is None else f"\\n{label}"


def _dot_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def parse_interval_spec(spec: str) -> Interval:
    body, _, label = spec.partition(":")
    start_text, sep, end_text = body.partition("-")
    if not sep:
        raise ValueError(f"interval '{spec}' must look like start-end or start-end:label")
    return Interval(int(start_text), int(end_text), label or None)


def load_intervals(args_specs: Iterable[str]) -> list[Interval]:
    return [parse_interval_spec(spec) for spec in args_specs]


def generate_synthetic_intervals(
    *,
    count: int,
    seed: int,
    start_max: int,
    width_max: int,
) -> list[Interval]:
    randomizer = random.Random(seed)
    intervals: list[Interval] = []
    for index in range(count):
        start = randomizer.randint(0, start_max)
        end = start + randomizer.randint(0, width_max)
        intervals.append(Interval(start, end, f"interval-{index}"))
    return intervals


def benchmark_overlap_queries(
    *,
    interval_count: int,
    query_count: int,
    seed: int,
    start_max: int,
    width_max: int,
    query_width_max: int,
) -> dict[str, object]:
    intervals = generate_synthetic_intervals(
        count=interval_count,
        seed=seed,
        start_max=start_max,
        width_max=width_max,
    )
    tree = IntervalTree(intervals)
    randomizer = random.Random(seed + 1)

    tree_elapsed_ns = 0
    naive_elapsed_ns = 0
    total_nodes_visited = 0
    worst_nodes_visited = 0
    all_matched = True
    sample_query: Interval | None = None
    sample_tree_hits: list[Interval] = []
    sample_naive_hits: list[Interval] = []

    for query_index in range(query_count):
        query_start = randomizer.randint(0, start_max)
        query_end = query_start + randomizer.randint(0, query_width_max)
        query = Interval(query_start, query_end, f"query-{query_index}")

        started = time.perf_counter_ns()
        tree_hits, stats = tree.find_overlaps_with_stats(query)
        tree_elapsed_ns += time.perf_counter_ns() - started

        started = time.perf_counter_ns()
        naive_hits = tree.naive_find_overlaps(query)
        naive_elapsed_ns += time.perf_counter_ns() - started

        total_nodes_visited += stats.nodes_visited
        worst_nodes_visited = max(worst_nodes_visited, stats.nodes_visited)
        if tree_hits != naive_hits:
            all_matched = False
        if sample_query is None:
            sample_query = query
            sample_tree_hits = tree_hits
            sample_naive_hits = naive_hits

    average_tree_ms = tree_elapsed_ns / query_count / 1_000_000 if query_count else 0.0
    average_naive_ms = naive_elapsed_ns / query_count / 1_000_000 if query_count else 0.0
    average_nodes_visited = total_nodes_visited / query_count if query_count else 0.0
    valid, errors = tree.validate()

    return {
        "interval_count": tree.size,
        "query_count": query_count,
        "seed": seed,
        "start_max": start_max,
        "width_max": width_max,
        "query_width_max": query_width_max,
        "tree_height": tree.height(),
        "root": None if tree.root is None else tree.root.interval.to_dict(),
        "max_end": None if tree.root is None else tree.root.max_end,
        "valid": valid,
        "errors": errors,
        "tree_average_ms": round(average_tree_ms, 6),
        "naive_average_ms": round(average_naive_ms, 6),
        "speedup_vs_naive": None if average_tree_ms == 0 else round(average_naive_ms / average_tree_ms, 3),
        "average_nodes_visited": round(average_nodes_visited, 3),
        "worst_nodes_visited": worst_nodes_visited,
        "average_visit_ratio": None if tree.size == 0 else round(average_nodes_visited / tree.size, 3),
        "same_results": all_matched,
        "sample_query": None if sample_query is None else sample_query.to_dict(),
        "sample_tree_hits": [interval.to_dict() for interval in sample_tree_hits],
        "sample_naive_hits": [interval.to_dict() for interval in sample_naive_hits],
    }


def validate_benchmark_args(*, intervals: int, queries: int, start_max: int, width_max: int, query_width_max: int) -> None:
    if intervals <= 0:
        raise ValueError("--intervals must be positive")
    if queries <= 0:
        raise ValueError("--queries must be positive")
    if start_max < 0:
        raise ValueError("--start-max must be non-negative")
    if width_max < 0:
        raise ValueError("--width-max must be non-negative")
    if query_width_max < 0:
        raise ValueError("--query-width-max must be non-negative")


def benchmark_overlap_series(
    *,
    interval_counts: Sequence[int],
    query_count: int,
    seed: int,
    start_max: int,
    width_max: int,
    query_width_max: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, interval_count in enumerate(interval_counts):
        validate_benchmark_args(
            intervals=interval_count,
            queries=query_count,
            start_max=start_max,
            width_max=width_max,
            query_width_max=query_width_max,
        )
        row = benchmark_overlap_queries(
            interval_count=interval_count,
            query_count=query_count,
            seed=seed + offset,
            start_max=start_max,
            width_max=width_max,
            query_width_max=query_width_max,
        )
        rows.append(row)
    return rows


def render_benchmark_series_csv(rows: Sequence[dict[str, object]]) -> str:
    headers = [
        "interval_count",
        "query_count",
        "seed",
        "tree_height",
        "tree_average_ms",
        "naive_average_ms",
        "speedup_vs_naive",
        "average_nodes_visited",
        "worst_nodes_visited",
        "average_visit_ratio",
        "same_results",
        "valid",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(
            ",".join(
                json.dumps(row.get(header)) if isinstance(row.get(header), bool) else str(row.get(header))
                for header in headers
            )
        )
    return "\n".join(lines) + "\n"


def parse_benchmark_series_csv(csv_text: str) -> list[dict[str, object]]:
    reader = csv.DictReader(csv_text.splitlines())
    rows: list[dict[str, object]] = []
    int_fields = {"interval_count", "query_count", "seed", "tree_height", "worst_nodes_visited"}
    float_fields = {"tree_average_ms", "naive_average_ms", "speedup_vs_naive", "average_nodes_visited", "average_visit_ratio"}
    bool_fields = {"same_results", "valid"}
    for raw in reader:
        row: dict[str, object] = {}
        for key, value in raw.items():
            if value is None:
                row[key] = None
            elif key in int_fields:
                row[key] = int(value)
            elif key in float_fields:
                row[key] = None if value == "None" else float(value)
            elif key in bool_fields:
                row[key] = value.lower() == "true"
            else:
                row[key] = value
        rows.append(row)
    return rows


def render_benchmark_series_svg(rows: Sequence[dict[str, object]], *, title: str = "Interval tree benchmark series") -> str:
    if not rows:
        raise ValueError("benchmark chart requires at least one row")

    interval_counts = [int(row["interval_count"]) for row in rows]
    tree_values = [float(row["tree_average_ms"]) for row in rows]
    naive_values = [float(row["naive_average_ms"]) for row in rows]
    speedups = [float(row["speedup_vs_naive"]) for row in rows if row.get("speedup_vs_naive") is not None]

    width = 960
    height = 540
    left = 90
    right = 40
    top = 90
    bottom = 90
    chart_width = width - left - right
    chart_height = height - top - bottom

    combined = tree_values + naive_values
    min_value = min(combined)
    max_value = max(combined)
    if max_value == min_value:
        max_value = min_value + 1.0

    def project(values: Sequence[float]) -> list[tuple[float, float]]:
        if len(values) == 1:
            x_positions = [left + chart_width / 2]
        else:
            x_positions = [left + chart_width * index / (len(values) - 1) for index in range(len(values))]
        return [
            (x, top + chart_height - ((value - min_value) / (max_value - min_value)) * chart_height)
            for x, value in zip(x_positions, values)
        ]

    tree_points = project(tree_values)
    naive_points = project(naive_values)

    def point_markup(points: Sequence[tuple[float, float]], color: str) -> str:
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        circles = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" />' for x, y in points)
        return f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{polyline}" />{circles}'

    y_ticks = []
    for step in range(5):
        ratio = step / 4
        value = max_value - (max_value - min_value) * ratio
        y = top + chart_height * ratio
        y_ticks.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1" />'
            f'<text x="{left-12}" y="{y+4:.1f}" font-size="12" text-anchor="end" fill="#475569">{value:.4f} ms</text>'
        )

    x_ticks = []
    for index, interval_count in enumerate(interval_counts):
        x = left + chart_width / 2 if len(interval_counts) == 1 else left + chart_width * index / (len(interval_counts) - 1)
        x_ticks.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" stroke="#f1f5f9" stroke-width="1" />'
            f'<text x="{x:.1f}" y="{height-bottom+24}" font-size="12" text-anchor="middle" fill="#475569">{interval_count}</text>'
        )

    subtitle = (
        f"{len(rows)} workload sizes • avg speedup {sum(speedups)/len(speedups):.2f}× over naive scan"
        if speedups else
        f"{len(rows)} workload sizes"
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{xml_escape(title)}</title>
  <desc id="desc">Line chart comparing interval-tree and naive overlap-query timings as interval counts grow.</desc>
  <rect width="100%" height="100%" fill="#f8fafc" rx="24" />
  <text x="{left}" y="42" font-size="28" font-family="Helvetica, Arial, sans-serif" font-weight="700" fill="#0f172a">{xml_escape(title)}</text>
  <text x="{left}" y="68" font-size="15" font-family="Helvetica, Arial, sans-serif" fill="#475569">{xml_escape(subtitle)}</text>
  <rect x="{left}" y="{top}" width="{chart_width}" height="{chart_height}" fill="#ffffff" stroke="#cbd5e1" rx="18" />
  {''.join(y_ticks)}
  {''.join(x_ticks)}
  <line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#0f172a" stroke-width="1.5" />
  <line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#0f172a" stroke-width="1.5" />
  {point_markup(naive_points, '#dc2626')}
  {point_markup(tree_points, '#2563eb')}
  <rect x="{width-260}" y="28" width="214" height="58" rx="12" fill="#ffffff" stroke="#cbd5e1" />
  <line x1="{width-240}" y1="50" x2="{width-200}" y2="50" stroke="#2563eb" stroke-width="3" />
  <circle cx="{width-220}" cy="50" r="4.5" fill="#2563eb" />
  <text x="{width-190}" y="55" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="#0f172a">interval tree</text>
  <line x1="{width-240}" y1="71" x2="{width-200}" y2="71" stroke="#dc2626" stroke-width="3" />
  <circle cx="{width-220}" cy="71" r="4.5" fill="#dc2626" />
  <text x="{width-190}" y="76" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="#0f172a">naive scan</text>
  <text x="{left + chart_width / 2}" y="{height - 28}" font-size="14" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" fill="#334155">interval count</text>
  <text x="24" y="{top + chart_height / 2}" font-size="14" font-family="Helvetica, Arial, sans-serif" fill="#334155" transform="rotate(-90 24 {top + chart_height / 2})">average query time (ms)</text>
</svg>'''


def write_benchmark_chart_from_rows(rows: Sequence[dict[str, object]], output_path: Path, *, title: str = "Interval tree benchmark series") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_benchmark_series_svg(rows, title=title), encoding="utf-8")
    return output_path



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
    any_overlap = tree.find_any_overlap(query)
    return {
        "command": "demo",
        "query": query.to_dict(),
        "point": point,
        "any_overlap": None if any_overlap is None else any_overlap.to_dict(),
        "all_overlaps": [interval.to_dict() for interval in tree.find_overlaps(query)],
        "point_hits": [interval.to_dict() for interval in tree.find_point(point)],
        "query_trace_dot": tree.export_query_trace_dot(query),
        **tree.summary(),
    }


def command_build(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    return {"command": "build", "input": args.intervals, **tree.summary()}


def command_overlap(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    query = parse_interval_spec(args.query)
    any_overlap = tree.find_any_overlap(query)
    overlaps, stats = tree.find_overlaps_with_stats(query)
    return {
        "command": "overlap",
        "input": args.intervals,
        "query": query.to_dict(),
        "any_overlap": None if any_overlap is None else any_overlap.to_dict(),
        "all_overlaps": [interval.to_dict() for interval in overlaps],
        "query_stats": stats.to_dict(),
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


def command_delete(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    interval = parse_interval_spec(args.interval)
    deleted = tree.delete(interval)
    return {
        "command": "delete",
        "input": args.intervals,
        "interval": interval.to_dict(),
        "deleted": deleted,
        **tree.summary(),
    }


def command_benchmark(args: argparse.Namespace) -> dict[str, object]:
    validate_benchmark_args(
        intervals=args.intervals,
        queries=args.queries,
        start_max=args.start_max,
        width_max=args.width_max,
        query_width_max=args.query_width_max,
    )
    return {
        "command": "benchmark",
        **benchmark_overlap_queries(
            interval_count=args.intervals,
            query_count=args.queries,
            seed=args.seed,
            start_max=args.start_max,
            width_max=args.width_max,
            query_width_max=args.query_width_max,
        ),
    }


def command_benchmark_series(args: argparse.Namespace) -> dict[str, object]:
    interval_counts = [int(part.strip()) for part in args.interval_counts.split(",") if part.strip()]
    if not interval_counts:
        raise ValueError("--interval-counts must include at least one positive integer")

    rows = benchmark_overlap_series(
        interval_counts=interval_counts,
        query_count=args.queries,
        seed=args.seed,
        start_max=args.start_max,
        width_max=args.width_max,
        query_width_max=args.query_width_max,
    )
    payload: dict[str, object] = {
        "command": "benchmark-series",
        "interval_counts": interval_counts,
        "query_count": args.queries,
        "seed": args.seed,
        "start_max": args.start_max,
        "width_max": args.width_max,
        "query_width_max": args.query_width_max,
        "rows": rows,
    }

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["json_artifact"] = str(output_json)
    if args.output_csv:
        output_csv = Path(args.output_csv)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        output_csv.write_text(render_benchmark_series_csv(rows), encoding="utf-8")
        payload["csv_artifact"] = str(output_csv)
    return payload

def command_benchmark_chart(args: argparse.Namespace) -> dict[str, object]:
    output_path = Path(args.output_svg)
    if args.input_csv:
        rows = parse_benchmark_series_csv(Path(args.input_csv).read_text(encoding="utf-8"))
    else:
        interval_counts = [int(part.strip()) for part in args.interval_counts.split(",") if part.strip()]
        if not interval_counts:
            raise ValueError("--interval-counts must include at least one positive integer")
        rows = benchmark_overlap_series(
            interval_counts=interval_counts,
            query_count=args.queries,
            seed=args.seed,
            start_max=args.start_max,
            width_max=args.width_max,
            query_width_max=args.query_width_max,
        )
    artifact = write_benchmark_chart_from_rows(rows, output_path, title=args.title)
    return {
        "command": "benchmark-chart",
        "title": args.title,
        "point_count": len(rows),
        "artifact": {"path": str(artifact), "format": "svg"},
        "source_csv": args.input_csv,
        "rows": rows,
    }



def render_query_trace_artifact(*, dot_text: str, output_path: Path, artifact_format: str) -> Path:
    artifact_format = artifact_format.lower()
    if artifact_format not in {"dot", "svg", "png"}:
        raise ValueError("--format must be dot, svg, or png")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if artifact_format == "dot":
        output_path.write_text(dot_text, encoding="utf-8")
        return output_path

    dot_binary = shutil.which("dot")
    if dot_binary is None:
        raise ValueError("Graphviz 'dot' is required for svg/png trace rendering but was not found on PATH")

    completed = subprocess.run(
        [dot_binary, f"-T{artifact_format}", "-o", str(output_path)],
        input=dot_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown Graphviz error"
        raise ValueError(f"Graphviz rendering failed: {stderr}")
    return output_path


def command_trace(args: argparse.Namespace) -> dict[str, object]:
    if not getattr(args, "output", None) and getattr(args, "format", "dot").lower() != "dot":
        raise ValueError("--format only applies when --output is provided")

    tree = IntervalTree(load_intervals(args.intervals))
    query = parse_interval_spec(args.query)
    overlaps, stats = tree.find_overlaps_with_stats(query)
    payload = {
        "command": "trace",
        "input": args.intervals,
        "query": query.to_dict(),
        "all_overlaps": [interval.to_dict() for interval in overlaps],
        "query_stats": stats.to_dict(),
        "query_trace_dot": tree.export_query_trace_dot(query),
        **tree.summary(),
    }
    if getattr(args, "output", None):
        output_path = render_query_trace_artifact(
            dot_text=payload["query_trace_dot"],
            output_path=Path(args.output),
            artifact_format=args.format,
        )
        payload["artifact"] = {"path": str(output_path), "format": args.format.lower()}
    return payload


def command_explain(args: argparse.Namespace) -> dict[str, object]:
    tree = IntervalTree(load_intervals(args.intervals))
    query = parse_interval_spec(args.query)
    return {
        "command": "explain",
        "input": args.intervals,
        **tree.explain_overlap_query(query),
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

    delete_parser = subparsers.add_parser("delete", help="delete one interval from a built tree")
    delete_parser.add_argument("interval", help="interval to delete")
    delete_parser.add_argument("intervals", nargs="+", help="interval specs")
    delete_parser.set_defaults(handler=command_delete)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare interval-tree overlap queries against naive scans on synthetic workloads",
    )
    benchmark_parser.add_argument("--intervals", type=int, default=500, help="number of synthetic intervals")
    benchmark_parser.add_argument("--queries", type=int, default=250, help="number of synthetic queries")
    benchmark_parser.add_argument("--seed", type=int, default=7, help="random seed for reproducibility")
    benchmark_parser.add_argument("--start-max", type=int, default=5000, help="max generated interval/query start")
    benchmark_parser.add_argument("--width-max", type=int, default=40, help="max generated interval width")
    benchmark_parser.add_argument("--query-width-max", type=int, default=60, help="max generated query width")
    benchmark_parser.set_defaults(handler=command_benchmark)

    benchmark_series_parser = subparsers.add_parser(
        "benchmark-series",
        help="run the overlap benchmark across several interval counts and optionally write JSON/CSV artifacts",
    )
    benchmark_series_parser.add_argument(
        "--interval-counts",
        default="100,250,500,1000",
        help="comma-separated interval counts to benchmark (default: 100,250,500,1000)",
    )
    benchmark_series_parser.add_argument("--queries", type=int, default=250, help="number of synthetic queries per run")
    benchmark_series_parser.add_argument("--seed", type=int, default=7, help="base random seed for reproducibility")
    benchmark_series_parser.add_argument("--start-max", type=int, default=5000, help="max generated interval/query start")
    benchmark_series_parser.add_argument("--width-max", type=int, default=40, help="max generated interval width")
    benchmark_series_parser.add_argument("--query-width-max", type=int, default=60, help="max generated query width")
    benchmark_series_parser.add_argument("--output-json", help="optional path to write the full JSON payload")
    benchmark_series_parser.add_argument("--output-csv", help="optional path to write a compact CSV summary")
    benchmark_series_parser.set_defaults(handler=command_benchmark_series)

    benchmark_chart_parser = subparsers.add_parser(
        "benchmark-chart",
        help="render a small SVG chart from a benchmark-series CSV artifact or a freshly generated series",
    )
    benchmark_chart_parser.add_argument("--input-csv", help="optional CSV artifact generated by benchmark-series")
    benchmark_chart_parser.add_argument(
        "--interval-counts",
        default="100,250,500,1000",
        help="comma-separated interval counts to benchmark when --input-csv is omitted",
    )
    benchmark_chart_parser.add_argument("--queries", type=int, default=250, help="number of synthetic queries per run")
    benchmark_chart_parser.add_argument("--seed", type=int, default=7, help="base random seed for reproducibility")
    benchmark_chart_parser.add_argument("--start-max", type=int, default=5000, help="max generated interval/query start")
    benchmark_chart_parser.add_argument("--width-max", type=int, default=40, help="max generated interval width")
    benchmark_chart_parser.add_argument("--query-width-max", type=int, default=60, help="max generated query width")
    benchmark_chart_parser.add_argument("--title", default="Interval tree benchmark series", help="chart title")
    benchmark_chart_parser.add_argument("--output-svg", required=True, help="path to write the SVG chart artifact")
    benchmark_chart_parser.set_defaults(handler=command_benchmark_chart)

    trace_parser = subparsers.add_parser(
        "trace",
        help="export a Graphviz DOT trace showing which branches overlap search visits or prunes",
    )
    trace_parser.add_argument("query", help="query interval spec")
    trace_parser.add_argument("intervals", nargs="+", help="interval specs")
    trace_parser.add_argument("--output", help="optional path to write a DOT/SVG/PNG artifact")
    trace_parser.add_argument(
        "--format",
        default="dot",
        help="artifact format when --output is used: dot, svg, or png (default: dot)",
    )
    trace_parser.set_defaults(handler=command_trace)

    explain_parser = subparsers.add_parser(
        "explain",
        help="narrate why overlap search visited or pruned each branch for one query",
    )
    explain_parser.add_argument("query", help="query interval spec")
    explain_parser.add_argument("intervals", nargs="+", help="interval specs")
    explain_parser.set_defaults(handler=command_explain)

    args = parser.parse_args()
    try:
        payload = args.handler(args)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
