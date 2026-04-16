from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import random
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class SplitResult:
    pivot: int
    found: bool
    left: list[int]
    right: list[int]
    left_root: int | None = None
    right_root: int | None = None


@dataclass
class Node:
    key: int
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None


@dataclass
class AccessTraceStep:
    key: int
    found: bool
    root_before: int | None
    root_after: int | None
    rotations_used: int
    comparisons_used: int


class SplayTree:
    def __init__(self, values: Iterable[int] | None = None) -> None:
        self.root: Node | None = None
        self.size = 0
        self.rotation_count = 0
        self.splay_steps = 0
        self.comparison_count = 0
        if values is not None:
            for value in values:
                self.insert(value)

    def _rotate_left(self, pivot: Node) -> None:
        child = pivot.right
        if child is None:
            return
        pivot.right = child.left
        if child.left is not None:
            child.left.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot.parent.left is pivot:
            pivot.parent.left = child
        else:
            pivot.parent.right = child
        child.left = pivot
        pivot.parent = child
        self.rotation_count += 1

    def _rotate_right(self, pivot: Node) -> None:
        child = pivot.left
        if child is None:
            return
        pivot.left = child.right
        if child.right is not None:
            child.right.parent = pivot
        child.parent = pivot.parent
        if pivot.parent is None:
            self.root = child
        elif pivot.parent.left is pivot:
            pivot.parent.left = child
        else:
            pivot.parent.right = child
        child.right = pivot
        pivot.parent = child
        self.rotation_count += 1

    def _splay(self, node: Node | None) -> None:
        while node is not None and node.parent is not None:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                if parent.left is node:
                    self._rotate_right(parent)
                else:
                    self._rotate_left(parent)
            elif grandparent.left is parent and parent.left is node:
                self._rotate_right(grandparent)
                self._rotate_right(parent)
            elif grandparent.right is parent and parent.right is node:
                self._rotate_left(grandparent)
                self._rotate_left(parent)
            elif grandparent.left is parent and parent.right is node:
                self._rotate_left(parent)
                self._rotate_right(grandparent)
            else:
                self._rotate_right(parent)
                self._rotate_left(grandparent)
            self.splay_steps += 1

    def insert(self, key: int) -> bool:
        if self.root is None:
            self.root = Node(key)
            self.size = 1
            return True
        current = self.root
        while current is not None:
            self.comparison_count += 1
            if key < current.key:
                if current.left is None:
                    current.left = Node(key=key, parent=current)
                    self.size += 1
                    self._splay(current.left)
                    return True
                current = current.left
            elif key > current.key:
                if current.right is None:
                    current.right = Node(key=key, parent=current)
                    self.size += 1
                    self._splay(current.right)
                    return True
                current = current.right
            else:
                self._splay(current)
                return False
        return False

    def find(self, key: int) -> bool:
        current = self.root
        last = None
        while current is not None:
            last = current
            self.comparison_count += 1
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                self._splay(current)
                return True
        self._splay(last)
        return False

    def delete(self, key: int) -> bool:
        if not self.find(key) or self.root is None or self.root.key != key:
            return False
        left = self.root.left
        right = self.root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None
        self.root = self._join(left, right)
        self.size -= 1
        return True

    def split(self, pivot: int) -> SplitResult:
        if self.root is None:
            return SplitResult(pivot=pivot, found=False, left=[], right=[])
        found = self.find(pivot)
        assert self.root is not None
        if found:
            left_root = self.root.left
            right_root = self.root.right
            if left_root is not None:
                left_root.parent = None
            if right_root is not None:
                right_root.parent = None
            self.root.left = None
            self.root.right = None
            return SplitResult(
                pivot=pivot,
                found=True,
                left=SplayTree._inorder_from(left_root),
                right=SplayTree._inorder_from(right_root),
                left_root=None if left_root is None else left_root.key,
                right_root=None if right_root is None else right_root.key,
            )

        root = self.root
        if root.key < pivot:
            left_root = root
            right_root = root.right
            left_root.right = None
            if right_root is not None:
                right_root.parent = None
            return SplitResult(
                pivot=pivot,
                found=False,
                left=SplayTree._inorder_from(left_root),
                right=SplayTree._inorder_from(right_root),
                left_root=left_root.key,
                right_root=None if right_root is None else right_root.key,
            )

        right_root = root
        left_root = root.left
        right_root.left = None
        if left_root is not None:
            left_root.parent = None
        return SplitResult(
            pivot=pivot,
            found=False,
            left=SplayTree._inorder_from(left_root),
            right=SplayTree._inorder_from(right_root),
            left_root=None if left_root is None else left_root.key,
            right_root=right_root.key,
        )

    @classmethod
    def join_from_values(cls, left_values: Iterable[int], right_values: Iterable[int]) -> "SplayTree":
        left_tree = cls(left_values)
        right_tree = cls(right_values)
        if left_tree.root is not None and right_tree.root is not None:
            left_max = left_tree.inorder()[-1]
            right_min = right_tree.inorder()[0]
            if left_max >= right_min:
                raise ValueError("left values must all be smaller than right values")
        tree = cls()
        tree.root = tree._join(left_tree.root, right_tree.root)
        tree.size = len(tree.inorder())
        tree.rotation_count = left_tree.rotation_count + right_tree.rotation_count + tree.rotation_count
        tree.splay_steps = left_tree.splay_steps + right_tree.splay_steps + tree.splay_steps
        tree.comparison_count = left_tree.comparison_count + right_tree.comparison_count + tree.comparison_count
        return tree

    @staticmethod
    def _inorder_from(node: Node | None) -> list[int]:
        items: list[int] = []

        def walk(current: Node | None) -> None:
            if current is None:
                return
            walk(current.left)
            items.append(current.key)
            walk(current.right)

        walk(node)
        return items

    def _join(self, left: Node | None, right: Node | None) -> Node | None:
        if left is None:
            return right
        self.root = left
        current = left
        while current.right is not None:
            current = current.right
        self._splay(current)
        assert self.root is current
        current.right = right
        if right is not None:
            right.parent = current
        return current

    def inorder(self) -> list[int]:
        items: list[int] = []

        def walk(node: Node | None) -> None:
            if node is None:
                return
            walk(node.left)
            items.append(node.key)
            walk(node.right)

        walk(self.root)
        return items

    def snapshot(self) -> dict:
        return {
            "values": self.inorder(),
            "root": self.root.key if self.root is not None else None,
            "size": self.size,
            "rotation_count": self.rotation_count,
            "splay_steps": self.splay_steps,
            "comparison_count": self.comparison_count,
        }

    def structure_snapshot(self) -> dict[str, object] | None:
        def build(node: Node | None) -> dict[str, object] | None:
            if node is None:
                return None
            return {
                "key": node.key,
                "left": build(node.left),
                "right": build(node.right),
            }

        return build(self.root)

    def detailed_snapshot(
        self,
        *,
        label: str | None = None,
        step_index: int | None = None,
        access_key: int | None = None,
        found: bool | None = None,
        trace_step: dict[str, int | bool | None] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            **self.snapshot(),
            "structure": self.structure_snapshot(),
        }
        if label is not None:
            payload["label"] = label
        if step_index is not None:
            payload["step_index"] = step_index
        if access_key is not None:
            payload["access_key"] = access_key
        if found is not None:
            payload["found"] = found
        if trace_step is not None:
            payload["trace_step"] = trace_step
        return payload

    @classmethod
    def from_snapshot(cls, payload: dict) -> "SplayTree":
        tree = cls(payload.get("values", []))
        tree.rotation_count = payload.get("rotation_count", tree.rotation_count)
        tree.splay_steps = payload.get("splay_steps", tree.splay_steps)
        tree.comparison_count = payload.get("comparison_count", tree.comparison_count)
        root_key = payload.get("root")
        if root_key is not None:
            tree.find(root_key)
        return tree

    def trace_access_sequence(self, keys: Iterable[int], *, capture_tree_snapshots: bool = False) -> dict:
        sequence = list(keys)
        before_root = self.root.key if self.root is not None else None
        rotations_before = self.rotation_count
        comparisons_before = self.comparison_count
        hits = 0
        misses = 0
        steps: list[dict[str, int | bool | None]] = []
        snapshot_frames: list[dict[str, object]] = []
        if capture_tree_snapshots:
            snapshot_frames.append(self.detailed_snapshot(label="initial", step_index=0))
        for index, key in enumerate(sequence, start=1):
            step_root_before = self.root.key if self.root is not None else None
            step_rotations_before = self.rotation_count
            step_comparisons_before = self.comparison_count
            found = self.find(key)
            if found:
                hits += 1
            else:
                misses += 1
            step = AccessTraceStep(
                key=key,
                found=found,
                root_before=step_root_before,
                root_after=self.root.key if self.root is not None else None,
                rotations_used=self.rotation_count - step_rotations_before,
                comparisons_used=self.comparison_count - step_comparisons_before,
            )
            step_payload = step.__dict__
            steps.append(step_payload)
            if capture_tree_snapshots:
                snapshot_frames.append(
                    self.detailed_snapshot(
                        label=f"after access {key}",
                        step_index=index,
                        access_key=key,
                        found=found,
                        trace_step=step_payload,
                    )
                )
        summary: dict[str, object] = {
            "requested_keys": sequence,
            "hits": hits,
            "misses": misses,
            "root_before": before_root,
            "root_after": self.root.key if self.root is not None else None,
            "rotations_used": self.rotation_count - rotations_before,
            "comparisons_used": self.comparison_count - comparisons_before,
            "size": self.size,
            "steps": steps,
        }
        if capture_tree_snapshots:
            summary["tree_snapshots"] = snapshot_frames
        return summary

    def access_sequence(self, keys: Iterable[int]) -> dict:
        summary = self.trace_access_sequence(keys)
        summary.pop("steps", None)
        return summary

    def to_dot(self, *, highlight_keys: Iterable[int] | None = None, title: str | None = None) -> str:
        highlight = set(highlight_keys or [])
        lines = ["digraph SplayTree {", "  rankdir=TB;", '  node [shape=circle, fontname="Helvetica"];']
        if title:
            lines.append(f'  labelloc="t"; label="{title}";')
        if self.root is None:
            lines.append('  empty [shape=plaintext, label="(empty)"];')
            lines.append("}")
            return "\n".join(lines) + "\n"

        null_counter = 0

        def walk(node: Node) -> None:
            nonlocal null_counter
            attrs = []
            if node is self.root:
                attrs.append('penwidth=2')
            if node.key in highlight:
                attrs.append('style="filled,bold"')
                attrs.append('fillcolor="lightgoldenrod1"')
            attr_text = ""
            if attrs:
                attr_text = ", " + ", ".join(attrs)
            lines.append(f'  n{node.key} [label="{node.key}"{attr_text}];')
            for side in ("left", "right"):
                child = getattr(node, side)
                if child is None:
                    null_counter += 1
                    lines.append(f'  null{null_counter} [shape=point];')
                    lines.append(f'  n{node.key} -> null{null_counter} [style=dashed];')
                else:
                    lines.append(f'  n{node.key} -> n{child.key};')
                    walk(child)

        walk(self.root)
        lines.append("}")
        return "\n".join(lines) + "\n"

    def to_mermaid(self, *, highlight_keys: Iterable[int] | None = None, title: str | None = None) -> str:
        highlight = set(highlight_keys or [])
        lines = ["flowchart TD"]
        if title:
            lines.append(f"    %% {title}")
        if self.root is None:
            lines.append('    empty["(empty)"]')
            return "\n".join(lines) + "\n"

        visited: set[int] = set()

        def node_id(key: int) -> str:
            return f"n{key}"

        def walk(node: Node) -> None:
            if node.key in visited:
                return
            visited.add(node.key)
            lines.append(f'    {node_id(node.key)}["{node.key}"]')
            for child in (node.left, node.right):
                if child is None:
                    continue
                lines.append(f"    {node_id(node.key)} --> {node_id(child.key)}")
                walk(child)

        walk(self.root)
        lines.append("    classDef root stroke-width:4px;")
        lines.append("    classDef highlight fill:#f6d365,stroke-width:3px;")
        lines.append(f"    class {node_id(self.root.key)} root;")
        if highlight:
            highlight_nodes = ",".join(node_id(key) for key in sorted(highlight) if key in visited)
            if highlight_nodes:
                lines.append(f"    class {highlight_nodes} highlight;")
        return "\n".join(lines) + "\n"


def parse_values(path: Path) -> list[int]:
    values = []
    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            values.append(int(stripped))
        except ValueError as exc:
            raise ValueError(f"invalid integer on line {line_number}: {stripped!r}") from exc
    return values


def load_tree(path: Path) -> SplayTree:
    return SplayTree.from_snapshot(json.loads(path.read_text()))


def save_tree(path: Path, tree: SplayTree) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree.snapshot(), indent=2) + "\n")


def save_snapshot_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def split_result_snapshot(values: list[int], *, root: int | None) -> dict[str, object]:
    return {
        "values": values,
        "root": root,
        "size": len(values),
        "rotation_count": 0,
        "splay_steps": 0,
        "comparison_count": 0,
    }


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def trace_snapshot_filename(step_index: int, access_key: int | None = None) -> str:
    if step_index == 0:
        return "00-initial.json"
    if access_key is None:
        raise ValueError("access_key is required for non-initial trace snapshots")
    return f"{step_index:02d}-after-access-{access_key}.json"


def export_trace_step_snapshots(summary: dict[str, object], output_dir: Path) -> dict[str, object]:
    frames = summary.pop("tree_snapshots", None)
    if frames is None:
        return summary

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_snapshots: list[dict[str, object]] = []
    for frame in frames:
        step_index = int(frame["step_index"])
        access_key = frame.get("access_key")
        filename = trace_snapshot_filename(step_index, access_key if isinstance(access_key, int) else None)
        save_snapshot_payload(output_dir / filename, frame)
        manifest_snapshots.append(
            {
                "step_index": step_index,
                "access_key": access_key,
                "label": frame.get("label"),
                "path": filename,
                "root": frame.get("root"),
                "found": frame.get("found"),
            }
        )

    manifest = {
        "requested_keys": summary["requested_keys"],
        "snapshot_count": len(manifest_snapshots),
        "snapshots": manifest_snapshots,
    }
    manifest_path = output_dir / "manifest.json"
    save_snapshot_payload(manifest_path, manifest)
    summary["step_snapshot_dir"] = str(output_dir)
    summary["step_snapshot_manifest"] = str(manifest_path)
    summary["step_snapshot_count"] = len(manifest_snapshots)
    summary["step_snapshot_files"] = manifest_snapshots
    return summary


BENCHMARK_CSV_FIELDNAMES = [
    "size",
    "seed",
    "hot_set_size",
    "workload",
    "query_count",
    "splay_hits",
    "splay_comparisons_used",
    "splay_rotations_used",
    "splay_comparisons_per_query",
    "splay_rotations_per_query",
    "splay_root_after",
    "red_black_hits",
    "red_black_comparisons_used",
    "red_black_comparisons_per_query",
    "red_black_height",
    "red_black_root",
    "comparison_gap",
]

BENCHMARK_SERIES_CSV_FIELDNAMES = [
    "series_index",
    "size",
    "seed",
    "hot_set_size",
    "hot_set_ratio",
    "workload",
    "query_count",
    "splay_hits",
    "splay_comparisons_used",
    "splay_rotations_used",
    "splay_comparisons_per_query",
    "splay_rotations_per_query",
    "splay_root_after",
    "red_black_hits",
    "red_black_comparisons_used",
    "red_black_comparisons_per_query",
    "red_black_height",
    "red_black_root",
    "comparison_gap",
]


def benchmark_csv_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    workloads = payload["workloads"]
    hot_set_size = payload["hot_set_size"]
    rows: list[dict[str, object]] = []
    for workload_name in ("hotset", "uniform_random"):
        workload = workloads[workload_name]
        splay = workload["splay"]
        red_black = workload["red_black"]
        rows.append(
            {
                "size": payload["size"],
                "seed": payload["seed"],
                "hot_set_size": hot_set_size,
                "workload": workload_name,
                "query_count": workload["queries"],
                "splay_hits": splay["hits"],
                "splay_comparisons_used": splay["comparisons_used"],
                "splay_rotations_used": splay["rotations_used"],
                "splay_comparisons_per_query": splay["comparisons_per_query"],
                "splay_rotations_per_query": splay["rotations_per_query"],
                "splay_root_after": splay["root_after"],
                "red_black_hits": red_black["hits"],
                "red_black_comparisons_used": red_black["comparisons_used"],
                "red_black_comparisons_per_query": red_black["comparisons_per_query"],
                "red_black_height": red_black["height"],
                "red_black_root": red_black["root"],
                "comparison_gap": red_black["comparisons_used"] - splay["comparisons_used"],
            }
        )
    return rows


def benchmark_series_csv_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, entry in enumerate(payload["entries"]):
        for row in benchmark_csv_rows(entry):
            rows.append(
                {
                    "series_index": index,
                    "hot_set_ratio": round(row["hot_set_size"] / row["size"], 4),
                    **row,
                }
            )
    return rows


def save_benchmark_csv(path: Path, payload: dict[str, object]) -> None:
    rows = benchmark_csv_rows(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BENCHMARK_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def save_benchmark_series_csv(path: Path, payload: dict[str, object]) -> None:
    rows = benchmark_series_csv_rows(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BENCHMARK_SERIES_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def markdown_link(target_path: Path, *, report_path: Path | None = None) -> str:
    if report_path is not None:
        href = Path(os.path.relpath(target_path, start=report_path.parent))
    else:
        href = target_path
    return f"[`{target_path.name}`]({href.as_posix()})"


def benchmark_report_markdown(
    payload: dict[str, object],
    *,
    report_path: Path | None = None,
    json_output: Path | None = None,
    csv_output: Path | None = None,
) -> str:
    summary_rows = payload["summary"]
    sizes = payload["sizes"]
    hotset_splay = [row["hotset_splay_comparisons_per_query"] for row in summary_rows]
    hotset_red_black = [row["hotset_red_black_comparisons_per_query"] for row in summary_rows]
    uniform_splay = [row["uniform_random_splay_comparisons_per_query"] for row in summary_rows]
    uniform_red_black = [row["uniform_random_red_black_comparisons_per_query"] for row in summary_rows]

    best_hotset = payload["takeaway"]["best_hotset_gap"]
    best_uniform = payload["takeaway"]["best_uniform_random_gap"]

    artifact_lines: list[str] = []
    if json_output is not None:
        artifact_lines.append(
            f"- full benchmark-series JSON: {markdown_link(json_output, report_path=report_path)}"
        )
    if csv_output is not None:
        artifact_lines.append(
            f"- chart-ready CSV rows: {markdown_link(csv_output, report_path=report_path)}"
        )
    if not artifact_lines:
        artifact_lines.append("- no external JSON/CSV artifact files were requested for this run")

    table_lines = [
        "| Size | Seed | Hot-set gap (RB-Splay comps) | Uniform gap (RB-Splay comps) | Hot-set splay cmp/query | Hot-set RB cmp/query | Uniform splay cmp/query | Uniform RB cmp/query |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        table_lines.append(
            "| {size} | {seed} | {hot_gap:+d} | {uniform_gap:+d} | {hot_splay:.3f} | {hot_rb:.3f} | {uniform_splay:.3f} | {uniform_rb:.3f} |".format(
                size=row["size"],
                seed=row["seed"],
                hot_gap=row["hotset_comparison_gap"],
                uniform_gap=row["uniform_random_comparison_gap"],
                hot_splay=row["hotset_splay_comparisons_per_query"],
                hot_rb=row["hotset_red_black_comparisons_per_query"],
                uniform_splay=row["uniform_random_splay_comparisons_per_query"],
                uniform_rb=row["uniform_random_red_black_comparisons_per_query"],
            )
        )

    hotset_chart_ceiling = max(max(hotset_splay), max(hotset_red_black)) + 1
    uniform_chart_ceiling = max(max(uniform_splay), max(uniform_red_black)) + 1

    hotset_chart = textwrap.dedent(
        f"""
        ```mermaid
        xychart-beta
            title "Hot-set comparisons per query (line 1 = splay, line 2 = red-black)"
            x-axis "Tree size" [{", ".join(str(size) for size in sizes)}]
            y-axis "Comparisons / query" 0 --> {hotset_chart_ceiling:.1f}
            line [{", ".join(f"{value:.3f}" for value in hotset_splay)}]
            line [{", ".join(f"{value:.3f}" for value in hotset_red_black)}]
        ```
        """
    ).strip()
    uniform_chart = textwrap.dedent(
        f"""
        ```mermaid
        xychart-beta
            title "Uniform-random comparisons per query (line 1 = splay, line 2 = red-black)"
            x-axis "Tree size" [{", ".join(str(size) for size in sizes)}]
            y-axis "Comparisons / query" 0 --> {uniform_chart_ceiling:.1f}
            line [{", ".join(f"{value:.3f}" for value in uniform_splay)}]
            line [{", ".join(f"{value:.3f}" for value in uniform_red_black)}]
        ```
        """
    ).strip()

    markdown = [
        "# Splay Tree Benchmark Report",
        "",
        "## Setup",
        "",
        f"- sizes: `{sizes}`",
        f"- hot-set size: `{payload['hot_set_size']}`",
        f"- hot queries per size: `{payload['hot_queries']}`",
        f"- uniform-random queries per size: `{payload['random_queries']}`",
        f"- seed base: `{payload['seed_base']}`",
        "- interpretation rule: positive gap means the splay tree used fewer total key comparisons than the red-black baseline",
        "",
        "## Embedded artifact links",
        "",
        *artifact_lines,
        "",
        "## Summary",
        "",
        f"- Best hot-set result: size `{best_hotset['size']}` with a `{best_hotset['hotset_comparison_gap']:+d}` comparison gap and splay averaging `{best_hotset['hotset_splay_comparisons_per_query']:.3f}` comparisons/query.",
        f"- Most favorable uniform-random result: size `{best_uniform['size']}` with a `{best_uniform['uniform_random_comparison_gap']:+d}` comparison gap and splay averaging `{best_uniform['uniform_random_splay_comparisons_per_query']:.3f}` comparisons/query.",
        "- Hot-set workloads should usually favor splay trees more strongly than uniform-random workloads, which gives you a clean locality story for interviews.",
        "",
        "## Per-size metrics",
        "",
        *table_lines,
        "",
        "## Hot-set chart",
        "",
        hotset_chart,
        "",
        "## Uniform-random chart",
        "",
        uniform_chart,
        "",
        "## Interview talking points",
        "",
        "- The hot-set chart makes the self-adjusting value proposition visible: repeated popular keys move toward the root and stay cheap to revisit.",
        "- The uniform-random chart keeps the story honest by showing where locality fades and the red-black baseline can stay competitive.",
        (
            "- Because the report links directly to committed JSON/CSV artifacts, you can reuse the same data in portfolio charts without rerunning ad-hoc analysis."
            if json_output is not None or csv_output is not None
            else "- Add --json-output/--csv-output when you want the Markdown report to point at committed chart data as well as inline charts."
        ),
    ]
    return "\n".join(markdown) + "\n"


def load_red_black_tree_class() -> type:
    module_path = Path(__file__).resolve().parents[1] / "red-black-tree-lab" / "red_black_tree.py"
    spec = importlib.util.spec_from_file_location("red_black_tree_lab_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load red-black tree module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.RedBlackTree


def red_black_search_depth(tree: object, key: int) -> tuple[bool, int]:
    current = tree.root
    comparisons = 0
    while current is not None:
        comparisons += 1
        if key < current.key:
            current = current.left
        elif key > current.key:
            current = current.right
        else:
            return True, comparisons
    return False, comparisons


def make_benchmark_values(size: int, seed: int) -> list[int]:
    values = list(range(1, size + 1))
    random.Random(seed).shuffle(values)
    return values


def make_hot_queries(values: list[int], *, query_count: int, hot_set_size: int, seed: int) -> tuple[list[int], list[int]]:
    rng = random.Random(seed)
    hot_keys = sorted(values[:hot_set_size])
    queries = [rng.choice(hot_keys) for _ in range(query_count)]
    return hot_keys, queries


def make_random_queries(values: list[int], *, query_count: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.choice(values) for _ in range(query_count)]


def run_comparison_workload(values: list[int], queries: list[int]) -> dict[str, object]:
    RedBlackTree = load_red_black_tree_class()

    splay_tree = SplayTree(values)
    rb_tree = RedBlackTree()
    for value in values:
        rb_tree.insert(value)

    splay_before_rotations = splay_tree.rotation_count
    splay_before_comparisons = splay_tree.comparison_count
    splay_hits = 0
    for key in queries:
        if splay_tree.find(key):
            splay_hits += 1

    rb_hits = 0
    rb_comparisons = 0
    for key in queries:
        found, comparisons = red_black_search_depth(rb_tree, key)
        rb_comparisons += comparisons
        if found:
            rb_hits += 1

    query_count = len(queries)
    return {
        "queries": query_count,
        "splay": {
            "hits": splay_hits,
            "comparisons_used": splay_tree.comparison_count - splay_before_comparisons,
            "rotations_used": splay_tree.rotation_count - splay_before_rotations,
            "comparisons_per_query": round((splay_tree.comparison_count - splay_before_comparisons) / query_count, 3),
            "rotations_per_query": round((splay_tree.rotation_count - splay_before_rotations) / query_count, 3),
            "root_after": None if splay_tree.root is None else splay_tree.root.key,
        },
        "red_black": {
            "hits": rb_hits,
            "comparisons_used": rb_comparisons,
            "comparisons_per_query": round(rb_comparisons / query_count, 3),
            "height": rb_tree.height(),
            "root": None if rb_tree.root is None else rb_tree.root.key,
        },
    }


def benchmark_trees(*, size: int, hot_set_size: int, hot_queries: int, random_queries: int, seed: int) -> dict[str, object]:
    if size <= 0:
        raise ValueError("size must be positive")
    if hot_set_size <= 0 or hot_set_size > size:
        raise ValueError("hot-set-size must be between 1 and size")
    if hot_queries <= 0 or random_queries <= 0:
        raise ValueError("query counts must be positive")

    values = make_benchmark_values(size, seed)
    hot_keys, hot_workload = make_hot_queries(values, query_count=hot_queries, hot_set_size=hot_set_size, seed=seed + 1)
    random_workload = make_random_queries(values, query_count=random_queries, seed=seed + 2)

    hot_result = run_comparison_workload(values, hot_workload)
    random_result = run_comparison_workload(values, random_workload)

    return {
        "size": size,
        "seed": seed,
        "hot_set_size": hot_set_size,
        "hot_keys": hot_keys,
        "build_preview": values[: min(12, len(values))],
        "workloads": {
            "hotset": hot_result,
            "uniform_random": random_result,
        },
        "takeaway": {
            "hotset_comparison_gap": hot_result["red_black"]["comparisons_used"] - hot_result["splay"]["comparisons_used"],
            "uniform_random_comparison_gap": random_result["red_black"]["comparisons_used"] - random_result["splay"]["comparisons_used"],
            "interpretation": (
                "positive gap means the splay tree used fewer key comparisons than the red-black tree on that workload"
            ),
        },
    }


def normalize_series_sizes(sizes: Iterable[int]) -> list[int]:
    normalized: list[int] = []
    seen: set[int] = set()
    for size in sizes:
        if size <= 0:
            raise ValueError("sizes must be positive integers")
        if size in seen:
            continue
        seen.add(size)
        normalized.append(size)
    if not normalized:
        raise ValueError("at least one benchmark size is required")
    return normalized


def benchmark_series(*, sizes: Iterable[int], hot_set_size: int, hot_queries: int, random_queries: int, seed: int) -> dict[str, object]:
    normalized_sizes = normalize_series_sizes(sizes)
    if hot_set_size <= 0:
        raise ValueError("hot-set-size must be positive")
    if hot_queries <= 0 or random_queries <= 0:
        raise ValueError("query counts must be positive")
    if any(size < hot_set_size for size in normalized_sizes):
        raise ValueError("every benchmark size must be at least as large as hot-set-size")

    entries: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for index, size in enumerate(normalized_sizes):
        entry_seed = seed + index
        entry = benchmark_trees(
            size=size,
            hot_set_size=hot_set_size,
            hot_queries=hot_queries,
            random_queries=random_queries,
            seed=entry_seed,
        )
        entries.append(entry)
        summary_rows.append(
            {
                "size": size,
                "seed": entry_seed,
                "hotset_comparison_gap": entry["takeaway"]["hotset_comparison_gap"],
                "uniform_random_comparison_gap": entry["takeaway"]["uniform_random_comparison_gap"],
                "hotset_splay_comparisons_per_query": entry["workloads"]["hotset"]["splay"]["comparisons_per_query"],
                "hotset_red_black_comparisons_per_query": entry["workloads"]["hotset"]["red_black"]["comparisons_per_query"],
                "uniform_random_splay_comparisons_per_query": entry["workloads"]["uniform_random"]["splay"]["comparisons_per_query"],
                "uniform_random_red_black_comparisons_per_query": entry["workloads"]["uniform_random"]["red_black"]["comparisons_per_query"],
            }
        )

    best_hotset = max(summary_rows, key=lambda row: row["hotset_comparison_gap"])
    best_uniform_random = max(summary_rows, key=lambda row: row["uniform_random_comparison_gap"])

    return {
        "sizes": normalized_sizes,
        "seed_base": seed,
        "hot_set_size": hot_set_size,
        "hot_queries": hot_queries,
        "random_queries": random_queries,
        "entries": entries,
        "summary": summary_rows,
        "takeaway": {
            "best_hotset_gap": best_hotset,
            "best_uniform_random_gap": best_uniform_random,
            "interpretation": (
                "positive gap means the splay tree used fewer key comparisons than the red-black tree at that size/workload"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Splay tree lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a snapshot from newline-delimited integers")
    build_parser.add_argument("--input", required=True, type=Path)
    build_parser.add_argument("--output", required=True, type=Path)

    access_parser = subparsers.add_parser("access", help="run an access sequence against a snapshot")
    access_parser.add_argument("--snapshot", required=True, type=Path)
    access_parser.add_argument("--output", type=Path)
    access_parser.add_argument("keys", nargs="+", type=int)

    trace_parser = subparsers.add_parser(
        "trace",
        help="run an access sequence and optionally export before/after Graphviz DOT diagrams",
    )
    trace_parser.add_argument("--snapshot", required=True, type=Path)
    trace_parser.add_argument("--output", type=Path)
    trace_parser.add_argument("--before-dot", type=Path)
    trace_parser.add_argument("--after-dot", type=Path)
    trace_parser.add_argument("--before-mermaid", type=Path)
    trace_parser.add_argument("--after-mermaid", type=Path)
    trace_parser.add_argument(
        "--step-snapshots-dir",
        type=Path,
        help="optional directory for initial/per-step structured tree snapshots plus a manifest",
    )
    trace_parser.add_argument("keys", nargs="+", type=int)

    insert_parser = subparsers.add_parser("insert", help="insert a key into a snapshot")
    insert_parser.add_argument("--snapshot", required=True, type=Path)
    insert_parser.add_argument("--output", required=True, type=Path)
    insert_parser.add_argument("key", type=int)

    delete_parser = subparsers.add_parser("delete", help="delete a key from a snapshot")
    delete_parser.add_argument("--snapshot", required=True, type=Path)
    delete_parser.add_argument("--output", required=True, type=Path)
    delete_parser.add_argument("key", type=int)

    split_parser = subparsers.add_parser("split", help="split a snapshot into values below and above a pivot")
    split_parser.add_argument("--snapshot", required=True, type=Path)
    split_parser.add_argument("--left-output", type=Path, help="optional snapshot path for values below the pivot")
    split_parser.add_argument("--right-output", type=Path, help="optional snapshot path for values above the pivot")
    split_parser.add_argument("pivot", type=int)

    join_parser = subparsers.add_parser("join", help="join two sorted disjoint value sets into a single snapshot")
    join_parser.add_argument("--left-input", required=True, type=Path)
    join_parser.add_argument("--right-input", required=True, type=Path)
    join_parser.add_argument("--output", required=True, type=Path)

    show_parser = subparsers.add_parser("show", help="show current snapshot summary")
    show_parser.add_argument("--snapshot", required=True, type=Path)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare skewed and random access workloads against the red-black-tree-lab baseline",
    )
    benchmark_parser.add_argument("--size", type=int, default=255, help="number of keys to build into both trees")
    benchmark_parser.add_argument("--hot-set-size", type=int, default=8, help="number of hot keys for the skewed workload")
    benchmark_parser.add_argument("--hot-queries", type=int, default=256, help="number of skewed hot-set queries")
    benchmark_parser.add_argument(
        "--random-queries", type=int, default=256, help="number of uniformly random successful queries"
    )
    benchmark_parser.add_argument("--seed", type=int, default=42, help="deterministic seed for build order and queries")
    benchmark_parser.add_argument("--json-output", type=Path, help="optional path to save the benchmark payload as JSON")
    benchmark_parser.add_argument("--csv-output", type=Path, help="optional path to save chart-ready benchmark rows as CSV")

    benchmark_series_parser = subparsers.add_parser(
        "benchmark-series",
        help="run the red-black comparison benchmark across multiple tree sizes and export chart-ready series data",
    )
    benchmark_series_parser.add_argument(
        "sizes",
        nargs="+",
        type=int,
        help="one or more tree sizes to sweep, for example: 63 127 255",
    )
    benchmark_series_parser.add_argument(
        "--hot-set-size", type=int, default=8, help="number of hot keys reused inside each skewed workload"
    )
    benchmark_series_parser.add_argument(
        "--hot-queries", type=int, default=256, help="number of skewed hot-set queries per tree size"
    )
    benchmark_series_parser.add_argument(
        "--random-queries", type=int, default=256, help="number of uniformly random successful queries per tree size"
    )
    benchmark_series_parser.add_argument(
        "--seed", type=int, default=42, help="deterministic base seed; each size increments the seed by its series index"
    )
    benchmark_series_parser.add_argument(
        "--json-output", type=Path, help="optional path to save the full benchmark-series payload as JSON"
    )
    benchmark_series_parser.add_argument(
        "--csv-output", type=Path, help="optional path to save flattened chart-ready series rows as CSV"
    )

    benchmark_report_parser = subparsers.add_parser(
        "benchmark-report",
        help="render a Markdown portfolio report from a benchmark-series run",
    )
    benchmark_report_parser.add_argument(
        "sizes",
        nargs="+",
        type=int,
        help="one or more tree sizes to sweep, for example: 63 127 255",
    )
    benchmark_report_parser.add_argument(
        "--hot-set-size", type=int, default=8, help="number of hot keys reused inside each skewed workload"
    )
    benchmark_report_parser.add_argument(
        "--hot-queries", type=int, default=256, help="number of skewed hot-set queries per tree size"
    )
    benchmark_report_parser.add_argument(
        "--random-queries", type=int, default=256, help="number of uniformly random successful queries per tree size"
    )
    benchmark_report_parser.add_argument(
        "--seed", type=int, default=42, help="deterministic base seed; each size increments the seed by its series index"
    )
    benchmark_report_parser.add_argument(
        "--json-output", type=Path, help="optional path to save the full benchmark-series payload as JSON"
    )
    benchmark_report_parser.add_argument(
        "--csv-output", type=Path, help="optional path to save flattened chart-ready series rows as CSV"
    )
    benchmark_report_parser.add_argument(
        "--output", type=Path, help="optional Markdown path for the generated benchmark report"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            tree = SplayTree(parse_values(args.input))
            save_tree(args.output, tree)
            print(json.dumps(tree.snapshot(), indent=2))
            return 0

        if args.command == "access":
            tree = load_tree(args.snapshot)
            summary = tree.access_sequence(args.keys)
            if args.output is not None:
                save_tree(args.output, tree)
            print(json.dumps(summary, indent=2))
            return 0

        if args.command == "trace":
            tree = load_tree(args.snapshot)
            if args.before_dot is not None:
                save_text(args.before_dot, tree.to_dot(title="before access trace"))
            if args.before_mermaid is not None:
                save_text(args.before_mermaid, tree.to_mermaid(title="before access trace"))
            summary = tree.trace_access_sequence(
                args.keys,
                capture_tree_snapshots=args.step_snapshots_dir is not None,
            )
            if args.output is not None:
                save_tree(args.output, tree)
            if args.after_dot is not None:
                save_text(args.after_dot, tree.to_dot(highlight_keys=args.keys, title="after access trace"))
            if args.after_mermaid is not None:
                save_text(args.after_mermaid, tree.to_mermaid(highlight_keys=args.keys, title="after access trace"))
            if args.step_snapshots_dir is not None:
                summary = export_trace_step_snapshots(summary, args.step_snapshots_dir)
            print(json.dumps(summary, indent=2))
            return 0

        if args.command == "insert":
            tree = load_tree(args.snapshot)
            inserted = tree.insert(args.key)
            save_tree(args.output, tree)
            print(json.dumps({"inserted": inserted, **tree.snapshot()}, indent=2))
            return 0

        if args.command == "delete":
            tree = load_tree(args.snapshot)
            deleted = tree.delete(args.key)
            save_tree(args.output, tree)
            print(json.dumps({"deleted": deleted, **tree.snapshot()}, indent=2))
            return 0

        if args.command == "split":
            tree = load_tree(args.snapshot)
            result = tree.split(args.pivot)
            if args.left_output is not None:
                save_snapshot_payload(args.left_output, split_result_snapshot(result.left, root=result.left_root))
            if args.right_output is not None:
                save_snapshot_payload(args.right_output, split_result_snapshot(result.right, root=result.right_root))
            print(json.dumps(result.__dict__, indent=2))
            return 0

        if args.command == "join":
            tree = SplayTree.join_from_values(parse_values(args.left_input), parse_values(args.right_input))
            save_tree(args.output, tree)
            print(json.dumps(tree.snapshot(), indent=2))
            return 0

        if args.command == "show":
            tree = load_tree(args.snapshot)
            print(json.dumps(tree.snapshot(), indent=2))
            return 0

        if args.command == "benchmark":
            payload = benchmark_trees(
                size=args.size,
                hot_set_size=args.hot_set_size,
                hot_queries=args.hot_queries,
                random_queries=args.random_queries,
                seed=args.seed,
            )
            if args.json_output is not None:
                save_snapshot_payload(args.json_output, payload)
            if args.csv_output is not None:
                save_benchmark_csv(args.csv_output, payload)
            print(json.dumps(payload, indent=2))
            return 0

        if args.command == "benchmark-series":
            payload = benchmark_series(
                sizes=args.sizes,
                hot_set_size=args.hot_set_size,
                hot_queries=args.hot_queries,
                random_queries=args.random_queries,
                seed=args.seed,
            )
            if args.json_output is not None:
                save_snapshot_payload(args.json_output, payload)
            if args.csv_output is not None:
                save_benchmark_series_csv(args.csv_output, payload)
            print(json.dumps(payload, indent=2))
            return 0

        if args.command == "benchmark-report":
            payload = benchmark_series(
                sizes=args.sizes,
                hot_set_size=args.hot_set_size,
                hot_queries=args.hot_queries,
                random_queries=args.random_queries,
                seed=args.seed,
            )
            if args.json_output is not None:
                save_snapshot_payload(args.json_output, payload)
            if args.csv_output is not None:
                save_benchmark_series_csv(args.csv_output, payload)
            markdown = benchmark_report_markdown(
                payload,
                report_path=args.output,
                json_output=args.json_output,
                csv_output=args.csv_output,
            )
            response = {
                "command": "benchmark-report",
                **payload,
                "markdown": markdown,
            }
            if args.output is not None:
                save_text(args.output, markdown)
                response["output"] = str(args.output)
            if args.json_output is not None:
                response["json_output"] = str(args.json_output)
            if args.csv_output is not None:
                response["csv_output"] = str(args.csv_output)
            print(json.dumps(response, indent=2))
            return 0
    except ValueError as exc:
        parser.exit(2, f"error: {exc}\n")

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
