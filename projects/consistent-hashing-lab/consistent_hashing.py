from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import html
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


HASH_SPACE = 2**128
NODE_PALETTE = (
    "#2563eb",
    "#dc2626",
    "#059669",
    "#d97706",
    "#7c3aed",
    "#db2777",
    "#0891b2",
    "#65a30d",
)


def stable_hash(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


@dataclass(frozen=True)
class RingPoint:
    position: int
    physical_node: str
    virtual_node: str


class ConsistentHashRing:
    def __init__(self, nodes: Sequence[str] | None = None, virtual_nodes: int = 128) -> None:
        if virtual_nodes <= 0:
            raise ValueError("virtual_nodes must be positive")
        self.virtual_nodes = virtual_nodes
        self.nodes: list[str] = []
        self._ring: list[RingPoint] = []
        self._positions: list[int] = []
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node: str) -> None:
        if not node:
            raise ValueError("node name must be non-empty")
        if node in self.nodes:
            raise ValueError(f"duplicate node: {node}")
        self.nodes.append(node)
        for index in range(self.virtual_nodes):
            virtual_name = f"{node}#{index}"
            point = RingPoint(
                position=stable_hash(virtual_name),
                physical_node=node,
                virtual_node=virtual_name,
            )
            self._ring.append(point)
        self._ring.sort(key=lambda item: item.position)
        self._positions = [point.position for point in self._ring]

    def remove_node(self, node: str) -> None:
        if node not in self.nodes:
            raise ValueError(f"unknown node: {node}")
        self.nodes.remove(node)
        self._ring = [point for point in self._ring if point.physical_node != node]
        self._positions = [point.position for point in self._ring]

    def ring_points(self) -> list[RingPoint]:
        return list(self._ring)

    def effective_replication_factor(self, replication_factor: int) -> int:
        if replication_factor <= 0:
            raise ValueError("replication_factor must be positive")
        return min(replication_factor, len(self.nodes))

    def get_nodes(self, key: str, replication_factor: int = 1) -> list[str]:
        if not self._ring:
            raise ValueError("ring has no nodes")

        distinct_target = self.effective_replication_factor(replication_factor)
        position = stable_hash(key)
        index = bisect.bisect_left(self._positions, position)
        if index == len(self._positions):
            index = 0

        selected: list[str] = []
        seen: set[str] = set()
        for offset in range(len(self._ring)):
            point = self._ring[(index + offset) % len(self._ring)]
            if point.physical_node in seen:
                continue
            selected.append(point.physical_node)
            seen.add(point.physical_node)
            if len(selected) == distinct_target:
                return selected

        return selected

    def get_node(self, key: str) -> str:
        return self.get_nodes(key, replication_factor=1)[0]

    def assign_keys(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, str] | dict[str, list[str]]:
        if replication_factor == 1:
            return {key: self.get_node(key) for key in keys}
        return {key: self.get_nodes(key, replication_factor=replication_factor) for key in keys}

    def distribution(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for nodes in self.assign_keys(keys, replication_factor=replication_factor).values():
            if isinstance(nodes, str):
                counts[nodes] += 1
            else:
                counts.update(nodes)
        return {node: counts.get(node, 0) for node in self.nodes}

    def load_report(self, keys: Iterable[str], replication_factor: int = 1) -> dict[str, object]:
        key_list = list(keys)
        effective_replication_factor = self.effective_replication_factor(replication_factor) if self.nodes else 0
        distribution = self.distribution(key_list, replication_factor=replication_factor)
        total_keys = len(key_list)
        loads = list(distribution.values())
        placement_count = total_keys * effective_replication_factor if self.nodes else 0
        average = placement_count / len(self.nodes) if self.nodes else 0.0
        return {
            "total_keys": total_keys,
            "nodes": len(self.nodes),
            "virtual_nodes_per_physical": self.virtual_nodes,
            "replication_factor": replication_factor,
            "effective_replication_factor": effective_replication_factor,
            "total_replica_placements": placement_count,
            "distribution": distribution,
            "max_load": max(loads) if loads else 0,
            "min_load": min(loads) if loads else 0,
            "average_load": average,
            "imbalance_ratio": (max(loads) / average) if loads and average else 0.0,
        }


def generate_keys(count: int, prefix: str = "key") -> list[str]:
    if count < 0:
        raise ValueError("count must be non-negative")
    return [f"{prefix}-{index}" for index in range(count)]


def simulate_remap(
    nodes: Sequence[str],
    keys: Sequence[str],
    virtual_nodes: int,
    add: str | None = None,
    remove: str | None = None,
    replication_factor: int = 1,
) -> dict[str, object]:
    if add and remove:
        raise ValueError("choose either add or remove, not both")
    before = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
    before_assignments = before.assign_keys(keys, replication_factor=replication_factor)

    if add:
        after_nodes = list(nodes)
        after_nodes.append(add)
    elif remove:
        after_nodes = [node for node in nodes if node != remove]
        if len(after_nodes) == len(nodes):
            raise ValueError(f"cannot remove unknown node: {remove}")
    else:
        raise ValueError("either add or remove must be provided")

    after = ConsistentHashRing(after_nodes, virtual_nodes=virtual_nodes)
    after_assignments = after.assign_keys(keys, replication_factor=replication_factor)

    moved = sorted(key for key in keys if before_assignments[key] != after_assignments[key])
    replica_placement_changes = 0
    for key in keys:
        before_nodes = before_assignments[key]
        after_nodes_for_key = after_assignments[key]
        if isinstance(before_nodes, str):
            if before_nodes != after_nodes_for_key:
                replica_placement_changes += 1
        else:
            replica_placement_changes += len(set(before_nodes).symmetric_difference(set(after_nodes_for_key)))

    return {
        "before_nodes": list(nodes),
        "after_nodes": after_nodes,
        "key_count": len(keys),
        "replication_factor": replication_factor,
        "effective_before_replication_factor": before.effective_replication_factor(replication_factor),
        "effective_after_replication_factor": after.effective_replication_factor(replication_factor),
        "moved_keys": len(moved),
        "movement_ratio": (len(moved) / len(keys)) if keys else 0.0,
        "replica_placement_changes": replica_placement_changes,
        "sample_moved_keys": moved[:10],
        "before_distribution": before.distribution(keys, replication_factor=replication_factor),
        "after_distribution": after.distribution(keys, replication_factor=replication_factor),
    }


def benchmark_virtual_nodes(
    nodes: Sequence[str],
    key_count: int,
    virtual_node_counts: Sequence[int],
    key_prefix: str = "key",
    replication_factor: int = 1,
    add: str | None = None,
    remove: str | None = None,
) -> dict[str, object]:
    if not virtual_node_counts:
        raise ValueError("virtual_node_counts must not be empty")

    keys = generate_keys(key_count, prefix=key_prefix)
    benchmark_points: list[dict[str, object]] = []
    seen_counts: set[int] = set()
    for virtual_nodes in virtual_node_counts:
        if virtual_nodes in seen_counts:
            continue
        seen_counts.add(virtual_nodes)
        ring = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
        load_report = ring.load_report(keys, replication_factor=replication_factor)
        point: dict[str, object] = {
            "virtual_nodes": virtual_nodes,
            "max_load": load_report["max_load"],
            "min_load": load_report["min_load"],
            "average_load": load_report["average_load"],
            "imbalance_ratio": load_report["imbalance_ratio"],
        }
        if add or remove:
            remap_summary = simulate_remap(
                nodes,
                keys,
                virtual_nodes=virtual_nodes,
                add=add,
                remove=remove,
                replication_factor=replication_factor,
            )
            point["moved_keys"] = remap_summary["moved_keys"]
            point["movement_ratio"] = remap_summary["movement_ratio"]
            point["replica_placement_changes"] = remap_summary["replica_placement_changes"]
        benchmark_points.append(point)

    best_imbalance = min(benchmark_points, key=lambda item: (item["imbalance_ratio"], item["virtual_nodes"]))
    payload: dict[str, object] = {
        "nodes": list(nodes),
        "node_count": len(nodes),
        "key_count": key_count,
        "replication_factor": replication_factor,
        "key_prefix": key_prefix,
        "virtual_node_counts": [point["virtual_nodes"] for point in benchmark_points],
        "series": benchmark_points,
        "best_imbalance_virtual_nodes": best_imbalance["virtual_nodes"],
        "best_imbalance_ratio": best_imbalance["imbalance_ratio"],
    }
    if add:
        payload["topology_change"] = {"action": "add", "node": add}
    elif remove:
        payload["topology_change"] = {"action": "remove", "node": remove}
    return payload


def _format_float(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural or f"{singular}s"


def node_color_map(nodes: Sequence[str]) -> dict[str, str]:
    return {node: NODE_PALETTE[index % len(NODE_PALETTE)] for index, node in enumerate(nodes)}


def build_visualization_payload(
    nodes: Sequence[str],
    keys: Sequence[str],
    virtual_nodes: int,
    replication_factor: int = 1,
    displayed_key_count: int = 12,
    title: str = "Consistent Hash Ring Visualization",
) -> dict[str, object]:
    key_list = list(keys)
    if not key_list:
        raise ValueError("visualization requires at least one key")

    ring = ConsistentHashRing(nodes, virtual_nodes=virtual_nodes)
    colors = node_color_map(ring.nodes)
    display_count = min(displayed_key_count, len(key_list))
    display_keys = key_list[:display_count]
    assignments = ring.assign_keys(display_keys, replication_factor=replication_factor)
    load_report = ring.load_report(key_list, replication_factor=replication_factor)

    sample_assignments: list[dict[str, object]] = []
    for index, key in enumerate(display_keys, start=1):
        owners = assignments[key]
        if isinstance(owners, str):
            owner_list = [owners]
        else:
            owner_list = list(owners)
        sample_assignments.append(
            {
                "token": f"k{index}",
                "key": key,
                "owners": owner_list,
                "primary_owner": owner_list[0],
                "owner_colors": [colors[owner] for owner in owner_list],
            }
        )

    ring_points = [
        {
            "physical_node": point.physical_node,
            "virtual_node": point.virtual_node,
            "position": point.position,
            "fraction": point.position / HASH_SPACE,
            "color": colors[point.physical_node],
        }
        for point in ring.ring_points()
    ]

    return {
        "title": title,
        "nodes": list(ring.nodes),
        "node_colors": colors,
        "virtual_nodes_per_physical": virtual_nodes,
        "virtual_point_count": len(ring_points),
        "replication_factor": replication_factor,
        "effective_replication_factor": ring.effective_replication_factor(replication_factor),
        "total_keys": len(key_list),
        "displayed_key_count": display_count,
        "hidden_key_count": len(key_list) - display_count,
        "load_report": load_report,
        "sample_assignments": sample_assignments,
        "ring_points": ring_points,
    }


def _hash_fraction(position: int) -> float:
    return position / HASH_SPACE


def _ring_angle(position: int) -> float:
    return math.tau * _hash_fraction(position) - (math.pi / 2)


def _polar_to_cartesian(center_x: float, center_y: float, radius: float, angle: float) -> tuple[float, float]:
    return (center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius)


def summarize_visualization_payload(payload: dict[str, object], preview_points: int = 12) -> dict[str, object]:
    summary = dict(payload)
    ring_points = list(payload["ring_points"])
    counts: Counter[str] = Counter(point["physical_node"] for point in ring_points)
    summary["ring_points_preview"] = ring_points[:preview_points]
    summary["ring_points_preview_truncated"] = len(ring_points) > preview_points
    summary["ring_points_by_node"] = {node: counts.get(node, 0) for node in payload["nodes"]}
    summary.pop("ring_points", None)
    return summary


def visualization_hidden_key_summary(payload: dict[str, object]) -> str:
    hidden = int(payload["hidden_key_count"])
    displayed = int(payload["displayed_key_count"])
    if hidden == 0:
        return f"All {displayed} {_pluralize(displayed, 'key')} are displayed on the ring."
    return f"Showing {displayed} key markers on the ring; {hidden} more keys still count toward the load report."


def visualization_replication_summary(payload: dict[str, object]) -> str:
    requested = int(payload["replication_factor"])
    effective = int(payload["effective_replication_factor"])
    if requested == effective:
        return f"replication factor {effective}"
    return f"replication capped at {effective} of requested {requested}"


def _distribution_percentage(value: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{(value / total) * 100:.1f}%"


def render_visualization_svg(payload: dict[str, object]) -> str:
    width = 1280
    height = 820
    center_x = 340
    center_y = 430
    outer_radius = 245
    key_radius = 188
    virtual_point_count = int(payload["virtual_point_count"])
    if virtual_point_count <= 96:
        point_radius = 4
    elif virtual_point_count <= 256:
        point_radius = 3
    else:
        point_radius = 2
    title = html.escape(str(payload["title"]))
    load_report = payload["load_report"]
    distribution = load_report["distribution"]
    max_distribution = max(distribution.values(), default=1) or 1
    total_placements = int(load_report["total_replica_placements"])
    hidden_key_summary = html.escape(visualization_hidden_key_summary(payload))
    replication_summary = html.escape(visualization_replication_summary(payload))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{title}</title>",
        f"<desc id=\"desc\">{title} showing consistent-hash virtual points, replica-aware sample assignments, and node load distribution.</desc>",
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="56" y="68" font-size="30" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#0f172a">{title}</text>',
        '<text x="56" y="100" font-size="15" font-family="Inter, Arial, sans-serif" fill="#475569">Virtual points appear on the ring perimeter. Sample key tokens inside the ring show which physical node owns each placement.</text>',
        f'<circle cx="{center_x}" cy="{center_y}" r="{outer_radius}" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>',
        f'<circle cx="{center_x}" cy="{center_y}" r="{key_radius}" fill="#eff6ff" stroke="#bfdbfe" stroke-width="2"/>',
        f'<circle cx="{center_x}" cy="{center_y}" r="116" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
        f'<text x="{center_x}" y="{center_y - 18}" text-anchor="middle" font-size="22" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#0f172a">{payload["virtual_point_count"]} virtual points</text>',
        f'<text x="{center_x}" y="{center_y + 12}" text-anchor="middle" font-size="16" font-family="Inter, Arial, sans-serif" fill="#334155">{payload["nodes"] and len(payload["nodes"])} physical nodes</text>',
        f'<text x="{center_x}" y="{center_y + 36}" text-anchor="middle" font-size="16" font-family="Inter, Arial, sans-serif" fill="#334155">{replication_summary}</text>',
    ]

    for ring_point in payload["ring_points"]:
        angle = _ring_angle(int(ring_point["position"]))
        x, y = _polar_to_cartesian(center_x, center_y, outer_radius, angle)
        lines.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{point_radius}" fill="{ring_point["color"]}" opacity="0.9">'
            f"<title>{html.escape(str(ring_point['virtual_node']))} on {html.escape(str(ring_point['physical_node']))}</title></circle>"
        )

    for assignment in payload["sample_assignments"]:
        angle = _ring_angle(stable_hash(str(assignment["key"])))
        x, y = _polar_to_cartesian(center_x, center_y, key_radius, angle)
        lines.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="16" fill="{assignment["owner_colors"][0]}" stroke="#ffffff" stroke-width="3">'
            f"<title>{html.escape(str(assignment['key']))} → {html.escape(', '.join(assignment['owners']))}</title></circle>"
        )
        lines.append(
            f'<text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle" font-size="11" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#ffffff">{html.escape(str(assignment["token"]))}</text>'
        )

    lines.extend(
        [
            '<rect x="660" y="128" width="566" height="204" rx="20" fill="#ffffff" stroke="#dbeafe" stroke-width="2"/>',
            '<text x="688" y="164" font-size="22" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#0f172a">Load distribution</text>',
            f'<text x="688" y="192" font-size="15" font-family="Inter, Arial, sans-serif" fill="#475569">{payload["total_keys"]} total keys, {load_report["total_replica_placements"]} placements, imbalance ratio {html.escape(_format_float(float(load_report["imbalance_ratio"])))}</text>',
        ]
    )

    bar_left = 690
    bar_width = 360
    for index, node in enumerate(payload["nodes"]):
        value = distribution[node]
        width_ratio = value / max_distribution if max_distribution else 0.0
        percentage = _distribution_percentage(value, total_placements)
        y = 226 + (index * 38)
        bar_fill = payload["node_colors"][node]
        lines.append(
            f'<text x="688" y="{y}" font-size="14" font-family="Inter, Arial, sans-serif" font-weight="600" fill="#1e293b">{html.escape(str(node))}</text>'
        )
        lines.append(
            f'<rect x="{bar_left}" y="{y + 10}" width="{bar_width}" height="14" rx="7" fill="#e2e8f0"/>'
        )
        lines.append(
            f'<rect x="{bar_left}" y="{y + 10}" width="{bar_width * width_ratio:.2f}" height="14" rx="7" fill="{bar_fill}"/>'
        )
        lines.append(
            f'<text x="{bar_left + bar_width + 18}" y="{y + 22}" font-size="13" font-family="Inter, Arial, sans-serif" fill="#334155">{value} placements ({percentage})</text>'
        )

    panel_top = 360
    panel_height = 390
    lines.extend(
        [
            f'<rect x="660" y="{panel_top}" width="566" height="{panel_height}" rx="20" fill="#ffffff" stroke="#dbeafe" stroke-width="2"/>',
            f'<text x="688" y="{panel_top + 36}" font-size="22" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#0f172a">Sample assignments</text>',
            f'<text x="688" y="{panel_top + 64}" font-size="15" font-family="Inter, Arial, sans-serif" fill="#475569">{hidden_key_summary}</text>',
            f'<text x="688" y="{panel_top + 100}" font-size="13" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#334155">Token</text>',
            f'<text x="760" y="{panel_top + 100}" font-size="13" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#334155">Key</text>',
            f'<text x="1020" y="{panel_top + 100}" font-size="13" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#334155">Owners</text>',
        ]
    )

    row_y = panel_top + 136
    row_gap = 24
    for assignment in payload["sample_assignments"]:
        owners_text = ", ".join(str(owner) for owner in assignment["owners"])
        lines.append(
            f'<text x="688" y="{row_y}" font-size="13" font-family="Inter, Arial, sans-serif" font-weight="700" fill="{assignment["owner_colors"][0]}">{html.escape(str(assignment["token"]))}</text>'
        )
        lines.append(
            f'<text x="760" y="{row_y}" font-size="13" font-family="Inter, Arial, sans-serif" fill="#1e293b">{html.escape(str(assignment["key"]))}</text>'
        )
        lines.append(
            f'<text x="1020" y="{row_y}" font-size="13" font-family="Inter, Arial, sans-serif" fill="#1e293b">{html.escape(owners_text)}</text>'
        )
        row_y += row_gap

    if payload["hidden_key_count"]:
        lines.append(
            f'<text x="688" y="{panel_top + panel_height - 24}" font-size="13" font-family="Inter, Arial, sans-serif" fill="#64748b">Hidden keys are omitted from the ring markers to keep the diagram readable, but all keys remain in the load metrics.</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_visualization_html(payload: dict[str, object]) -> str:
    svg = render_visualization_svg(payload)
    rows = []
    for assignment in payload["sample_assignments"]:
        owners_html = "<br/>".join(html.escape(str(owner)) for owner in assignment["owners"])
        rows.append(
            "<tr>"
            f"<td><strong style=\"color:{assignment['owner_colors'][0]}\">{html.escape(str(assignment['token']))}</strong></td>"
            f"<td><code>{html.escape(str(assignment['key']))}</code></td>"
            f"<td>{owners_html}</td>"
            "</tr>"
        )
    load_report = payload["load_report"]
    hidden_key_summary = visualization_hidden_key_summary(payload)
    cards = [
        ("Physical nodes", str(len(payload["nodes"]))),
        ("Virtual nodes per physical", str(payload["virtual_nodes_per_physical"])),
        ("Total keys", str(payload["total_keys"])),
        ("Effective replication", f"{payload['effective_replication_factor']} / {payload['replication_factor']}"),
        ("Imbalance ratio", _format_float(float(load_report["imbalance_ratio"]))),
    ]
    card_html = "".join(
        f'<div class="card"><span class="label">{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
        for label, value in cards
    )
    distribution_items = "".join(
        f"<li><span class=\"swatch\" style=\"background:{payload['node_colors'][node]}\"></span><strong>{html.escape(str(node))}</strong><span>{load_report['distribution'][node]} placements ({_distribution_percentage(load_report['distribution'][node], load_report['total_replica_placements'])})</span></li>"
        for node in payload["nodes"]
    )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(str(payload['title']))}</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: #e2e8f0; color: #0f172a; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 28px; }}
    h1 {{ margin: 0 0 10px; font-size: 34px; }}
    p {{ color: #334155; line-height: 1.6; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 20px 0 24px; }}
    .card {{ background: white; border-radius: 18px; padding: 16px 18px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }}
    .card .label {{ display: block; color: #64748b; font-size: 13px; margin-bottom: 6px; }}
    .visual {{ background: white; border-radius: 24px; padding: 12px; box-shadow: 0 14px 36px rgba(15, 23, 42, 0.12); overflow: auto; }}
    .layout {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; margin-top: 24px; }}
    .panel {{ background: white; border-radius: 24px; padding: 22px; box-shadow: 0 14px 36px rgba(15, 23, 42, 0.12); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid #e2e8f0; vertical-align: top; font-size: 14px; }}
    ul {{ list-style: none; padding: 0; margin: 14px 0 0; }}
    li {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; color: #334155; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 999px; display: inline-block; }}
    code {{ background: #eff6ff; border-radius: 8px; padding: 2px 6px; }}
    @media (max-width: 1100px) {{ .layout {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(str(payload['title']))}</h1>
    <p>Portfolio-ready snapshot of a deterministic consistent-hashing ring. The outer ring shows virtual-node placement, the inner tokens show sample keys, and the side panels keep the load story readable without opening the JSON output.</p>
    <section class=\"cards\">{card_html}</section>
    <section class=\"visual\">{svg}</section>
    <section class=\"layout\">
      <article class=\"panel\">
        <h2>Sample assignments</h2>
        <p>{html.escape(hidden_key_summary)}</p>
        <table>
          <thead><tr><th>Token</th><th>Key</th><th>Owners</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </article>
      <article class=\"panel\">
        <h2>Node placement summary</h2>
        <p>Total replica placements: <strong>{load_report['total_replica_placements']}</strong>. The legend below matches the ring colors and load bars in the SVG.</p>
        <ul>{distribution_items}</ul>
      </article>
    </section>
  </main>
</body>
</html>
"""


def save_visualization_svg(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_visualization_svg(payload), encoding="utf-8")


def save_visualization_html(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_visualization_html(payload), encoding="utf-8")


def benchmark_series_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    topology_change = payload.get("topology_change")
    topology_action = ""
    topology_node = ""
    if isinstance(topology_change, dict):
        topology_action = str(topology_change.get("action", ""))
        topology_node = str(topology_change.get("node", ""))

    rows: list[dict[str, object]] = []
    for point in payload["series"]:
        rows.append(
            {
                "node_count": payload["node_count"],
                "key_count": payload["key_count"],
                "replication_factor": payload["replication_factor"],
                "virtual_nodes": point["virtual_nodes"],
                "max_load": point["max_load"],
                "min_load": point["min_load"],
                "average_load": round(float(point["average_load"]), 4),
                "imbalance_ratio": round(float(point["imbalance_ratio"]), 4),
                "moved_keys": point.get("moved_keys", 0),
                "movement_ratio": round(float(point.get("movement_ratio", 0.0)), 4),
                "replica_placement_changes": point.get("replica_placement_changes", 0),
                "best_imbalance_virtual_nodes": payload["best_imbalance_virtual_nodes"],
                "best_imbalance_ratio": round(float(payload["best_imbalance_ratio"]), 4),
                "topology_action": topology_action,
                "topology_node": topology_node,
            }
        )
    return rows


def save_benchmark_series_csv(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = benchmark_series_rows(payload)
    fieldnames = [
        "node_count",
        "key_count",
        "replication_factor",
        "virtual_nodes",
        "max_load",
        "min_load",
        "average_load",
        "imbalance_ratio",
        "moved_keys",
        "movement_ratio",
        "replica_placement_changes",
        "best_imbalance_virtual_nodes",
        "best_imbalance_ratio",
        "topology_action",
        "topology_node",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def render_benchmark_series_markdown(payload: dict[str, object]) -> str:
    topology_change = payload.get("topology_change")
    topology_line = "- Topology change: none"
    if isinstance(topology_change, dict):
        topology_line = f"- Topology change: {topology_change['action']} `{topology_change['node']}`"

    lines = [
        "# Consistent Hashing Virtual-Node Benchmark Report",
        "",
        "Deterministic benchmark summary for the consistent-hashing lab. It turns the JSON benchmark series into a recruiter-friendly table so load-balance and remap tradeoffs are readable without extra scripting.",
        "",
        f"- Physical nodes: {payload['node_count']} ({', '.join(payload['nodes'])})",
        f"- Keys: {payload['key_count']}",
        f"- Replication factor: {payload['replication_factor']}",
        topology_line,
        f"- Best imbalance ratio: {_format_float(float(payload['best_imbalance_ratio']))} at `{payload['best_imbalance_virtual_nodes']}` virtual nodes per physical node",
        "",
        "## Benchmark series",
        "",
        "| Virtual nodes | Max load | Min load | Average load | Imbalance ratio | Moved keys | Movement ratio | Replica placement changes |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for point in payload["series"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(point["virtual_nodes"]),
                    str(point["max_load"]),
                    str(point["min_load"]),
                    _format_float(float(point["average_load"])),
                    _format_float(float(point["imbalance_ratio"])),
                    str(point.get("moved_keys", 0)),
                    _format_float(float(point.get("movement_ratio", 0.0))),
                    str(point.get("replica_placement_changes", 0)),
                ]
            )
            + " |"
        )

    best_virtual_nodes = payload["best_imbalance_virtual_nodes"]
    best_point = next(point for point in payload["series"] if point["virtual_nodes"] == best_virtual_nodes)
    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            f"- The most balanced tested ring used `{best_virtual_nodes}` virtual nodes per physical node, with an imbalance ratio of `{_format_float(float(best_point['imbalance_ratio']))}`.",
            f"- At that setting, the load range was `{best_point['min_load']}` to `{best_point['max_load']}` around an average of `{_format_float(float(best_point['average_load']))}` keys per physical node.",
        ]
    )
    if "movement_ratio" in best_point:
        lines.append(
            f"- Under the tested topology change, the best-balance configuration moved `{best_point.get('moved_keys', 0)}` keys, a movement ratio of `{_format_float(float(best_point.get('movement_ratio', 0.0)))}`, with `{best_point.get('replica_placement_changes', 0)}` replica-placement changes."
        )
    return "\n".join(lines) + "\n"


def save_benchmark_series_markdown(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_benchmark_series_markdown(payload), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consistent hashing ring lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign = subparsers.add_parser("assign", help="assign keys to nodes")
    assign.add_argument("--nodes", nargs="+", required=True)
    assign.add_argument("--keys", nargs="+", required=True)
    assign.add_argument("--virtual-nodes", type=positive_int, default=128)
    assign.add_argument("--replication-factor", type=positive_int, default=1)

    report = subparsers.add_parser("report", help="show load distribution for generated keys")
    report.add_argument("--nodes", nargs="+", required=True)
    report.add_argument("--key-count", type=int, required=True)
    report.add_argument("--key-prefix", default="key")
    report.add_argument("--virtual-nodes", type=positive_int, default=128)
    report.add_argument("--replication-factor", type=positive_int, default=1)

    remap = subparsers.add_parser("remap", help="simulate node add/remove remapping")
    remap.add_argument("--nodes", nargs="+", required=True)
    remap.add_argument("--key-count", type=int, required=True)
    remap.add_argument("--key-prefix", default="key")
    remap.add_argument("--virtual-nodes", type=positive_int, default=128)
    remap.add_argument("--replication-factor", type=positive_int, default=1)
    remap_change = remap.add_mutually_exclusive_group(required=True)
    remap_change.add_argument("--add-node")
    remap_change.add_argument("--remove-node")

    benchmark = subparsers.add_parser(
        "benchmark",
        help="compare multiple virtual-node counts for load balance and optional remapping",
    )
    benchmark.add_argument("--nodes", nargs="+", required=True)
    benchmark.add_argument("--key-count", type=int, required=True)
    benchmark.add_argument("--key-prefix", default="key")
    benchmark.add_argument("--virtual-node-counts", nargs="+", type=positive_int, required=True)
    benchmark.add_argument("--replication-factor", type=positive_int, default=1)
    benchmark.add_argument("--csv-out")
    benchmark.add_argument("--markdown-out")
    benchmark_change = benchmark.add_mutually_exclusive_group()
    benchmark_change.add_argument("--add-node")
    benchmark_change.add_argument("--remove-node")

    visualize = subparsers.add_parser(
        "visualize",
        help="render a portfolio-ready consistent-hash ring visualization",
    )
    visualize.add_argument("--nodes", nargs="+", required=True)
    key_source = visualize.add_mutually_exclusive_group(required=True)
    key_source.add_argument("--keys", nargs="+")
    key_source.add_argument("--key-count", type=positive_int)
    visualize.add_argument("--key-prefix", default="key")
    visualize.add_argument("--displayed-key-count", type=positive_int, default=12)
    visualize.add_argument("--virtual-nodes", type=positive_int, default=128)
    visualize.add_argument("--replication-factor", type=positive_int, default=1)
    visualize.add_argument("--title", default="Consistent Hash Ring Visualization")
    visualize.add_argument("--svg-out")
    visualize.add_argument("--html-out")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload_for_stdout: dict[str, object] | None = None

    if args.command == "assign":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.assign_keys(args.keys, replication_factor=args.replication_factor)
    elif args.command == "report":
        ring = ConsistentHashRing(args.nodes, virtual_nodes=args.virtual_nodes)
        payload = ring.load_report(
            generate_keys(args.key_count, args.key_prefix),
            replication_factor=args.replication_factor,
        )
    elif args.command == "remap":
        payload = simulate_remap(
            args.nodes,
            generate_keys(args.key_count, args.key_prefix),
            virtual_nodes=args.virtual_nodes,
            add=args.add_node,
            remove=args.remove_node,
            replication_factor=args.replication_factor,
        )
    elif args.command == "visualize":
        keys = args.keys if args.keys else generate_keys(args.key_count, args.key_prefix)
        payload = build_visualization_payload(
            args.nodes,
            keys,
            virtual_nodes=args.virtual_nodes,
            replication_factor=args.replication_factor,
            displayed_key_count=args.displayed_key_count,
            title=args.title,
        )
        if args.svg_out:
            svg_output_path = Path(args.svg_out)
            save_visualization_svg(payload, svg_output_path)
            payload["svg_output"] = str(svg_output_path)
        if args.html_out:
            html_output_path = Path(args.html_out)
            save_visualization_html(payload, html_output_path)
            payload["html_output"] = str(html_output_path)
        payload_for_stdout = summarize_visualization_payload(payload)
    else:
        payload = benchmark_virtual_nodes(
            args.nodes,
            key_count=args.key_count,
            virtual_node_counts=args.virtual_node_counts,
            key_prefix=args.key_prefix,
            replication_factor=args.replication_factor,
            add=args.add_node,
            remove=args.remove_node,
        )
        if args.csv_out:
            csv_output_path = Path(args.csv_out)
            save_benchmark_series_csv(payload, csv_output_path)
            payload["csv_output"] = str(csv_output_path)
        if args.markdown_out:
            markdown_output_path = Path(args.markdown_out)
            save_benchmark_series_markdown(payload, markdown_output_path)
            payload["markdown_output"] = str(markdown_output_path)
    if payload_for_stdout is None:
        payload_for_stdout = payload

    print(json.dumps(payload_for_stdout, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
