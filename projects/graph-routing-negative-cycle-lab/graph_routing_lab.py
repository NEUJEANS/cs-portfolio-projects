from __future__ import annotations

import argparse
import os
import html
import json
import textwrap
from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path
from typing import Iterable, Mapping

INF = float("inf")


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    weight: int

    def to_dict(self) -> dict[str, object]:
        return {"source": self.source, "target": self.target, "weight": self.weight}


@dataclass(frozen=True)
class PathResult:
    source: str
    target: str
    cost: float
    path: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "cost": self.cost,
            "path": list(self.path),
        }


@dataclass(frozen=True)
class BellmanFordResult:
    source: str
    distances: dict[str, float]
    predecessors: dict[str, str | None]
    iterations: tuple[dict[str, object], ...]
    negative_cycle: tuple[str, ...] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "distances": dict(sorted(self.distances.items())),
            "predecessors": dict(sorted(self.predecessors.items())),
            "iterations": list(self.iterations),
            "negative_cycle": list(self.negative_cycle) if self.negative_cycle else None,
        }


@dataclass(frozen=True)
class JohnsonResult:
    potentials: dict[str, float]
    reweighted_edges: tuple[Edge, ...]
    paths: dict[str, dict[str, PathResult]]

    def to_dict(self) -> dict[str, object]:
        return {
            "potentials": dict(sorted(self.potentials.items())),
            "reweighted_edges": [edge.to_dict() for edge in self.reweighted_edges],
            "paths": {
                source: {
                    target: path.to_dict() for target, path in sorted(targets.items())
                }
                for source, targets in sorted(self.paths.items())
            },
        }


@dataclass(frozen=True)
class RoutingReport:
    graph_name: str
    nodes: tuple[str, ...]
    edges: tuple[Edge, ...]
    bellman_ford: BellmanFordResult | None
    johnson: JohnsonResult | None

    def to_dict(self) -> dict[str, object]:
        return {
            "graph": self.graph_name,
            "nodes": list(self.nodes),
            "edges": [edge.to_dict() for edge in self.edges],
            "bellman_ford": self.bellman_ford.to_dict() if self.bellman_ford else None,
            "johnson": self.johnson.to_dict() if self.johnson else None,
        }


@dataclass(frozen=True)
class RouteTableEntry:
    node: str
    cost: float
    predecessor: str | None
    path: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "node": self.node,
            "cost": self.cost,
            "predecessor": self.predecessor,
            "path": list(self.path),
            "status": self.status,
        }


@dataclass(frozen=True)
class EdgeChange:
    source: str
    target: str
    baseline_weight: int | None
    candidate_weight: int | None
    change: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "baseline_weight": self.baseline_weight,
            "candidate_weight": self.candidate_weight,
            "change": self.change,
        }


@dataclass(frozen=True)
class RouteDiff:
    node: str
    baseline: RouteTableEntry | None
    candidate: RouteTableEntry | None
    changed_fields: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "node": self.node,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "changed_fields": list(self.changed_fields),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class RoutingComparison:
    baseline_graph: str
    candidate_graph: str
    source: str
    baseline_negative_cycle: tuple[str, ...] | None
    candidate_negative_cycle: tuple[str, ...] | None
    edge_changes: tuple[EdgeChange, ...]
    route_diffs: tuple[RouteDiff, ...]
    changed_route_count: int
    unchanged_route_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_graph": self.baseline_graph,
            "candidate_graph": self.candidate_graph,
            "source": self.source,
            "baseline_negative_cycle": list(self.baseline_negative_cycle) if self.baseline_negative_cycle else None,
            "candidate_negative_cycle": list(self.candidate_negative_cycle) if self.candidate_negative_cycle else None,
            "edge_changes": [change.to_dict() for change in self.edge_changes],
            "route_diffs": [diff.to_dict() for diff in self.route_diffs],
            "changed_route_count": self.changed_route_count,
            "unchanged_route_count": self.unchanged_route_count,
        }


@dataclass(frozen=True)
class ComparisonMetrics:
    changed_diffs: tuple[RouteDiff, ...]
    same_cost_reroutes: int
    cost_changes: int
    predecessor_changes: int
    status_changes: int
    presence_changes: int


@dataclass(frozen=True)
class GalleryArtifact:
    label: str
    path: Path
    description: str


@dataclass(frozen=True)
class GalleryScenario:
    slug: str
    title: str
    description: str
    baseline_graph: Path
    candidate_graph: Path
    source: str
    artifacts: tuple[GalleryArtifact, ...]


@dataclass(frozen=True)
class RoutingGallery:
    title: str
    description: str
    manifest_path: Path
    scenarios: tuple[GalleryScenario, ...]


@dataclass(frozen=True)
class GalleryScenarioSummary:
    scenario: GalleryScenario
    comparison: RoutingComparison
    baseline_graph_name: str
    candidate_graph_name: str
    same_cost_reroutes: int
    cost_changes: int
    predecessor_changes: int
    status_changes: int
    changed_nodes: tuple[str, ...]
    story_label: str


def load_graph(path: str | Path) -> tuple[str, tuple[str, ...], tuple[Edge, ...]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    graph_name = str(payload.get("name", Path(path).stem))
    nodes = payload.get("nodes")
    edges_payload = payload.get("edges")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("graph payload must include a non-empty 'nodes' list")
    if len(set(nodes)) != len(nodes):
        raise ValueError("graph nodes must be unique")
    node_set = set(nodes)
    edges: list[Edge] = []
    if not isinstance(edges_payload, list):
        raise ValueError("graph payload must include an 'edges' list")
    for item in edges_payload:
        source = item.get("source")
        target = item.get("target")
        weight = item.get("weight")
        if source not in node_set or target not in node_set:
            raise ValueError("all edge endpoints must exist in the node list")
        if not isinstance(weight, int):
            raise ValueError("edge weights must be integers")
        edges.append(Edge(source, target, weight))
    return graph_name, tuple(nodes), tuple(edges)


def bellman_ford(nodes: Iterable[str], edges: Iterable[Edge], source: str) -> BellmanFordResult:
    ordered_nodes = tuple(nodes)
    if source not in ordered_nodes:
        raise ValueError(f"unknown source {source!r}")
    distances = {node: INF for node in ordered_nodes}
    predecessors = {node: None for node in ordered_nodes}
    distances[source] = 0
    edge_list = list(edges)
    iterations: list[dict[str, object]] = []

    for iteration in range(len(ordered_nodes) - 1):
        changed = False
        relaxations: list[dict[str, object]] = []
        for edge in edge_list:
            if distances[edge.source] == INF:
                continue
            candidate = distances[edge.source] + edge.weight
            if candidate < distances[edge.target]:
                distances[edge.target] = candidate
                predecessors[edge.target] = edge.source
                changed = True
                relaxations.append(edge.to_dict())
        iterations.append(
            {
                "iteration": iteration + 1,
                "changed": changed,
                "relaxed_edges": relaxations,
                "distances": dict(sorted(distances.items())),
            }
        )
        if not changed:
            break

    negative_cycle = find_negative_cycle(ordered_nodes, edge_list, distances, predecessors)
    return BellmanFordResult(
        source=source,
        distances=dict(sorted(distances.items())),
        predecessors=dict(sorted(predecessors.items())),
        iterations=tuple(iterations),
        negative_cycle=negative_cycle,
    )


def find_negative_cycle(
    nodes: tuple[str, ...],
    edges: list[Edge],
    distances: Mapping[str, float],
    predecessors: Mapping[str, str | None],
) -> tuple[str, ...] | None:
    witness: str | None = None
    for edge in edges:
        if distances[edge.source] == INF:
            continue
        if distances[edge.source] + edge.weight < distances[edge.target]:
            witness = edge.target
            break
    if witness is None:
        return None

    walker = witness
    trail_predecessors = dict(predecessors)
    for edge in edges:
        if distances[edge.source] == INF:
            continue
        if distances[edge.source] + edge.weight < distances[edge.target]:
            trail_predecessors[edge.target] = edge.source
    for _ in range(len(nodes)):
        next_node = trail_predecessors.get(walker)
        if next_node is None:
            return (witness,)
        walker = next_node

    cycle = [walker]
    current = trail_predecessors[walker]
    while current is not None and current != walker:
        cycle.append(current)
        current = trail_predecessors[current]
    cycle.append(walker)
    cycle.reverse()
    return tuple(cycle)


def dijkstra(nodes: Iterable[str], edges: Iterable[Edge], source: str) -> dict[str, PathResult]:
    adjacency = {node: [] for node in nodes}
    for edge in edges:
        adjacency[edge.source].append((edge.target, edge.weight))
    for values in adjacency.values():
        values.sort()

    best_cost = {node: INF for node in adjacency}
    best_path = {node: tuple() for node in adjacency}
    best_cost[source] = 0
    best_path[source] = (source,)
    queue: list[tuple[float, tuple[str, ...], str]] = [(0, (source,), source)]

    while queue:
        cost, path, node = heappop(queue)
        if cost > best_cost[node]:
            continue
        if cost == best_cost[node] and path > best_path[node] and best_path[node]:
            continue
        for neighbor, weight in adjacency[node]:
            next_cost = cost + weight
            next_path = path + (neighbor,)
            if next_cost < best_cost[neighbor] or (
                next_cost == best_cost[neighbor] and (not best_path[neighbor] or next_path < best_path[neighbor])
            ):
                best_cost[neighbor] = next_cost
                best_path[neighbor] = next_path
                heappush(queue, (next_cost, next_path, neighbor))

    return {
        node: PathResult(source=source, target=node, cost=best_cost[node], path=best_path[node])
        for node in sorted(adjacency)
    }


def johnson(nodes: Iterable[str], edges: Iterable[Edge]) -> JohnsonResult:
    ordered_nodes = tuple(nodes)
    super_source = "__super_source__"
    augmented_nodes = ordered_nodes + (super_source,)
    augmented_edges = list(edges) + [Edge(super_source, node, 0) for node in ordered_nodes]
    bf = bellman_ford(augmented_nodes, augmented_edges, super_source)
    if bf.negative_cycle:
        raise ValueError(f"negative cycle detected: {' -> '.join(bf.negative_cycle)}")
    potentials = bf.distances
    reweighted_edges = tuple(
        Edge(edge.source, edge.target, int(edge.weight + potentials[edge.source] - potentials[edge.target]))
        for edge in edges
    )
    paths: dict[str, dict[str, PathResult]] = {}
    for source in ordered_nodes:
        reweighted_paths = dijkstra(ordered_nodes, reweighted_edges, source)
        paths[source] = {}
        for target, path in reweighted_paths.items():
            if path.cost == INF:
                actual_cost = INF
            else:
                actual_cost = path.cost - potentials[source] + potentials[target]
            paths[source][target] = PathResult(
                source=source,
                target=target,
                cost=actual_cost,
                path=path.path,
            )
    filtered_potentials = {node: potentials[node] for node in ordered_nodes}
    return JohnsonResult(
        potentials=dict(sorted(filtered_potentials.items())),
        reweighted_edges=reweighted_edges,
        paths=paths,
    )


def render_pretty(report: RoutingReport) -> str:
    lines = [f"Graph: {report.graph_name}", f"Nodes: {', '.join(report.nodes)}", "Edges:"]
    for edge in report.edges:
        lines.append(f"- {edge.source} -> {edge.target} ({edge.weight})")
    if report.bellman_ford:
        lines.append("")
        lines.append(f"Bellman-Ford from {report.bellman_ford.source}:")
        lines.append(f"Iterations logged: {len(report.bellman_ford.iterations)}")
        for node, distance in report.bellman_ford.distances.items():
            predecessor = report.bellman_ford.predecessors[node] or "—"
            lines.append(f"- {node}: dist={_format_cost(distance)} predecessor={predecessor}")
        if report.bellman_ford.negative_cycle:
            lines.append("Negative cycle: " + " -> ".join(report.bellman_ford.negative_cycle))
    if report.johnson:
        lines.append("")
        lines.append("Johnson all-pairs shortest paths:")
        for source, targets in sorted(report.johnson.paths.items()):
            lines.append(f"[{source}]")
            for target, result in sorted(targets.items()):
                path_text = " -> ".join(result.path) if result.path else "unreachable"
                lines.append(f"  {target}: cost={_format_cost(result.cost)} path={path_text}")
    return "\n".join(lines)


def _escape_markdown_cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _markdown_table(lines: list[str], headers: list[str], rows: Iterable[Iterable[str]]) -> None:
    lines.append("| " + " | ".join(_escape_markdown_cell(header) for header in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_escape_markdown_cell(cell) for cell in row) + " |")


def _html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _nodes_reachable_from_starts(edges: Iterable[Edge], starts: Iterable[str]) -> set[str]:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source, []).append(edge.target)
    seen = {node for node in starts}
    queue = deque(seen)
    while queue:
        node = queue.popleft()
        for neighbor in adjacency.get(node, []):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return seen


def render_markdown(report: RoutingReport) -> str:
    lines = [f"# {report.graph_name} routing report", ""]
    lines.append(f"- Nodes: {len(report.nodes)}")
    lines.append(f"- Edges: {len(report.edges)}")
    lines.append("")
    lines.append("## Edge list")
    _markdown_table(
        lines,
        ["Source", "Target", "Weight"],
        ([edge.source, edge.target, str(edge.weight)] for edge in report.edges),
    )

    if report.bellman_ford:
        shortest_paths = build_shortest_path_results(report.bellman_ford)
        unstable_nodes: set[str] = set()
        if report.bellman_ford.negative_cycle:
            unstable_nodes = _nodes_reachable_from_starts(
                report.edges,
                report.bellman_ford.negative_cycle[:-1],
            )
        lines.append("")
        lines.append(f"## Bellman-Ford from {report.bellman_ford.source}")
        _markdown_table(
            lines,
            ["Node", "Distance", "Predecessor", "Path", "Status"],
            (
                [
                    node,
                    _format_cost(result.cost),
                    report.bellman_ford.predecessors[node] or "—",
                    (
                        "undefined (reachable negative cycle)"
                        if node in unstable_nodes
                        else (" -> ".join(result.path) if result.path else "unreachable")
                    ),
                    "cycle-reachable" if node in unstable_nodes else ("reachable" if result.path else "unreachable"),
                ]
                for node, result in shortest_paths.items()
            ),
        )
        if report.bellman_ford.negative_cycle:
            lines.append("")
            lines.append("### Reachable negative cycle")
            lines.append("- Cycle: " + " -> ".join(report.bellman_ford.negative_cycle))
            cycle_nodes = set(report.bellman_ford.negative_cycle[:-1])
            if cycle_nodes:
                lines.append("- Cycle nodes: " + ", ".join(sorted(cycle_nodes)))
            if unstable_nodes:
                lines.append("- Unstable shortest-path nodes: " + ", ".join(sorted(unstable_nodes)))
            lines.append(
                "- Note: shortest-path costs that can keep traversing this cycle are not well-defined."
            )
        lines.append("")
        lines.append("### Iteration log")
        for iteration in report.bellman_ford.iterations:
            relaxed_edges = iteration["relaxed_edges"]
            if relaxed_edges:
                relaxed_text = ", ".join(
                    f"{edge['source']}->{edge['target']} ({edge['weight']})" for edge in relaxed_edges
                )
            else:
                relaxed_text = "none"
            changed_text = "changed" if iteration["changed"] else "stable"
            lines.append(
                f"- Iteration {iteration['iteration']}: {changed_text}; relaxed edges: {relaxed_text}"
            )

    if report.johnson:
        lines.append("")
        lines.append("## Johnson all-pairs shortest paths")
        _markdown_table(
            lines,
            ["Source", "Target", "Cost", "Path"],
            (
                [
                    source,
                    target,
                    _format_cost(result.cost),
                    " -> ".join(result.path) if result.path else "unreachable",
                ]
                for source, targets in sorted(report.johnson.paths.items())
                for target, result in sorted(targets.items())
            ),
        )

    return "\n".join(lines) + "\n"


def _sanitize_identifier(value: str) -> str:
    sanitized = "".join(character if character.isalnum() else "_" for character in value)
    if not sanitized:
        return "_"
    if sanitized[0].isdigit():
        return f"_{sanitized}"
    return sanitized


def _dot_quote(value: str) -> str:
    return json.dumps(value)


def _format_cost(value: float) -> str:
    if value == INF:
        return "∞"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _path_edges(path: tuple[str, ...]) -> set[tuple[str, str]]:
    return {(path[index], path[index + 1]) for index in range(len(path) - 1)}


def _cycle_edges(cycle: tuple[str, ...]) -> set[tuple[str, str]]:
    return {(cycle[index], cycle[index + 1]) for index in range(len(cycle) - 1)}


def export_mermaid(report: RoutingReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    highlighted_path_edges: set[tuple[str, str]] = set()
    shortest_path_nodes: set[str] = set()
    negative_cycle_edges: set[tuple[str, str]] = set()
    negative_cycle_nodes: set[str] = set()

    if report.bellman_ford:
        for node, result in build_shortest_path_results(report.bellman_ford).items():
            shortest_path_nodes.update(result.path)
            highlighted_path_edges.update(_path_edges(result.path))
        if report.bellman_ford.negative_cycle:
            negative_cycle_nodes.update(report.bellman_ford.negative_cycle)
            negative_cycle_edges.update(_cycle_edges(report.bellman_ford.negative_cycle))

    lines = [f"%% {report.graph_name}", "flowchart LR"]
    for node in report.nodes:
        identifier = _sanitize_identifier(node)
        suffix = []
        if report.bellman_ford:
            distance = report.bellman_ford.distances[node]
            suffix.append(f"dist={_format_cost(distance)}")
        lines.append(f'    {identifier}["{node}' + (f' | {", ".join(suffix)}' if suffix else "") + '"]')

    for edge in report.edges:
        source_id = _sanitize_identifier(edge.source)
        target_id = _sanitize_identifier(edge.target)
        edge_key = (edge.source, edge.target)
        if edge_key in negative_cycle_edges:
            arrow = f' ==>|"{edge.weight}"| '
        elif edge_key in highlighted_path_edges:
            arrow = f' -->|"{edge.weight}"| '
        else:
            arrow = f' -.->|"{edge.weight}"| '
        lines.append(f"    {source_id}{arrow}{target_id}")

    lines.append("")
    lines.append("    classDef default fill:#f8fafc,stroke:#475569,color:#0f172a;")
    lines.append("    classDef shortest fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;")
    lines.append("    classDef cycle fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:3px;")

    if shortest_path_nodes:
        lines.append("    class " + ",".join(_sanitize_identifier(node) for node in sorted(shortest_path_nodes)) + " shortest;")
    if negative_cycle_nodes:
        lines.append("    class " + ",".join(_sanitize_identifier(node) for node in sorted(negative_cycle_nodes)) + " cycle;")
    if report.bellman_ford and report.bellman_ford.negative_cycle:
        lines.append(
            "    %% negative cycle: " + " -> ".join(report.bellman_ford.negative_cycle)
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def export_markdown(report: RoutingReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(report), encoding="utf-8")
    return output


def export_dot(report: RoutingReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    highlighted_path_edges: set[tuple[str, str]] = set()
    shortest_path_nodes: set[str] = set()
    negative_cycle_edges: set[tuple[str, str]] = set()
    negative_cycle_nodes: set[str] = set()

    if report.bellman_ford:
        for node, result in build_shortest_path_results(report.bellman_ford).items():
            shortest_path_nodes.update(result.path)
            highlighted_path_edges.update(_path_edges(result.path))
        if report.bellman_ford.negative_cycle:
            negative_cycle_nodes.update(report.bellman_ford.negative_cycle)
            negative_cycle_edges.update(_cycle_edges(report.bellman_ford.negative_cycle))

    lines = [
        f"digraph {_sanitize_identifier(report.graph_name)} {{",
        "    rankdir=LR;",
        f"    graph [label={_dot_quote(report.graph_name)}, labelloc=\"t\", bgcolor=\"white\"];",
        "    node [shape=box, style=\"rounded,filled\", fillcolor=\"#f8fafc\", color=\"#475569\", fontcolor=\"#0f172a\"];",
        "    edge [color=\"#94a3b8\", fontcolor=\"#334155\"];",
    ]

    for node in report.nodes:
        identifier = _sanitize_identifier(node)
        label = node
        if report.bellman_ford:
            label += f"\\ndist={_format_cost(report.bellman_ford.distances[node])}"
        if node in negative_cycle_nodes:
            attrs = 'fillcolor="#fee2e2", color="#dc2626", fontcolor="#7f1d1d", penwidth=3'
        elif node in shortest_path_nodes:
            attrs = 'fillcolor="#dbeafe", color="#2563eb", fontcolor="#1e3a8a", penwidth=2'
        else:
            attrs = None
        attribute_text = f", {attrs}" if attrs else ""
        lines.append(f"    {identifier} [label={_dot_quote(label)}{attribute_text}];")

    for edge in report.edges:
        edge_key = (edge.source, edge.target)
        if edge_key in negative_cycle_edges:
            attrs = 'color="#dc2626", fontcolor="#7f1d1d", penwidth=3'
        elif edge_key in highlighted_path_edges:
            attrs = 'color="#2563eb", fontcolor="#1e3a8a", penwidth=2'
        else:
            attrs = 'style=dashed'
        lines.append(
            f"    {_sanitize_identifier(edge.source)} -> {_sanitize_identifier(edge.target)} "
            f"[label={_dot_quote(str(edge.weight))}, {attrs}];"
        )

    if report.bellman_ford and report.bellman_ford.negative_cycle:
        lines.append(f"    // negative cycle: {' -> '.join(report.bellman_ford.negative_cycle)}")
    lines.append("}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def build_shortest_path_results(result: BellmanFordResult) -> dict[str, PathResult]:
    paths: dict[str, PathResult] = {}
    for node, distance in result.distances.items():
        if distance == INF:
            path: tuple[str, ...] = tuple()
        else:
            chain: list[str] = []
            current: str | None = node
            seen: set[str] = set()
            while current is not None and current not in seen:
                chain.append(current)
                seen.add(current)
                current = result.predecessors[current]
            path = tuple(reversed(chain))
            if path and path[0] != result.source:
                path = (result.source,) if node == result.source else tuple()
        paths[node] = PathResult(source=result.source, target=node, cost=distance, path=path)
    return paths


def build_route_table(report: RoutingReport) -> dict[str, RouteTableEntry]:
    if report.bellman_ford is None:
        raise ValueError('route-table export requires Bellman-Ford data')
    shortest_paths = build_shortest_path_results(report.bellman_ford)
    unstable_nodes: set[str] = set()
    if report.bellman_ford.negative_cycle:
        unstable_nodes = _nodes_reachable_from_starts(report.edges, report.bellman_ford.negative_cycle[:-1])
    return {
        node: RouteTableEntry(
            node=node,
            cost=result.cost,
            predecessor=report.bellman_ford.predecessors[node],
            path=result.path,
            status=(
                'cycle-reachable'
                if node in unstable_nodes
                else ('reachable' if result.path else 'unreachable')
            ),
        )
        for node, result in shortest_paths.items()
    }


def _format_route_entry_path(entry: RouteTableEntry | None) -> str:
    if entry is None:
        return 'absent'
    return ' -> '.join(entry.path) if entry.path else 'unreachable'


def _format_route_entry_cost(entry: RouteTableEntry | None) -> str:
    if entry is None:
        return '—'
    return _format_cost(entry.cost)


def _format_route_entry_predecessor(entry: RouteTableEntry | None) -> str:
    if entry is None:
        return '—'
    return entry.predecessor or '—'


def _format_route_entry_status(entry: RouteTableEntry | None) -> str:
    if entry is None:
        return 'absent'
    return entry.status


def _format_cost_delta(baseline: RouteTableEntry | None, candidate: RouteTableEntry | None) -> str:
    if baseline is None or candidate is None:
        return 'n/a'
    if baseline.cost == INF or candidate.cost == INF:
        return 'n/a'
    delta = candidate.cost - baseline.cost
    if isinstance(delta, float) and delta.is_integer():
        delta = int(delta)
    if delta == 0:
        return 'unchanged'
    return f'{delta:+}'


def _summarize_route_diff(baseline: RouteTableEntry | None, candidate: RouteTableEntry | None, changed_fields: tuple[str, ...]) -> str:
    if baseline is None and candidate is None:
        return 'absent in both graphs'
    if baseline is None:
        return 'node added in candidate graph'
    if candidate is None:
        return 'node removed from candidate graph'
    if not changed_fields:
        return 'unchanged'

    parts: list[str] = []
    if 'status' in changed_fields:
        parts.append(f'status {baseline.status} -> {candidate.status}')
    if 'cost' in changed_fields:
        parts.append(f'cost {_format_cost(baseline.cost)} -> {_format_cost(candidate.cost)}')
    if 'predecessor' in changed_fields:
        parts.append(
            'predecessor '
            + f'{baseline.predecessor or "—"} -> {candidate.predecessor or "—"}'
        )
    if 'path' in changed_fields:
        prefix = 'path changed at same cost' if baseline.cost == candidate.cost else 'path'
        parts.append(
            f'{prefix}: [{_format_route_entry_path(baseline)}] => [{_format_route_entry_path(candidate)}]'
        )
    if 'presence' in changed_fields:
        parts.append('node presence changed')
    return '; '.join(parts)


def compare_reports(baseline_report: RoutingReport, candidate_report: RoutingReport) -> RoutingComparison:
    if baseline_report.bellman_ford is None or candidate_report.bellman_ford is None:
        raise ValueError('route comparison requires Bellman-Ford data in both reports')
    if baseline_report.bellman_ford.source != candidate_report.bellman_ford.source:
        raise ValueError('route comparison requires the same Bellman-Ford source in both reports')

    baseline_edges = {(edge.source, edge.target): edge.weight for edge in baseline_report.edges}
    candidate_edges = {(edge.source, edge.target): edge.weight for edge in candidate_report.edges}
    edge_changes: list[EdgeChange] = []
    for source, target in sorted(set(baseline_edges) | set(candidate_edges)):
        baseline_weight = baseline_edges.get((source, target))
        candidate_weight = candidate_edges.get((source, target))
        if baseline_weight == candidate_weight:
            continue
        if baseline_weight is None:
            change = 'added'
        elif candidate_weight is None:
            change = 'removed'
        else:
            change = 'weight-changed'
        edge_changes.append(
            EdgeChange(
                source=source,
                target=target,
                baseline_weight=baseline_weight,
                candidate_weight=candidate_weight,
                change=change,
            )
        )

    baseline_table = build_route_table(baseline_report)
    candidate_table = build_route_table(candidate_report)
    route_diffs: list[RouteDiff] = []
    changed_route_count = 0
    unchanged_route_count = 0
    for node in sorted(set(baseline_table) | set(candidate_table)):
        baseline = baseline_table.get(node)
        candidate = candidate_table.get(node)
        changed_fields: list[str] = []
        if baseline is None or candidate is None:
            changed_fields.append('presence')
        else:
            if baseline.status != candidate.status:
                changed_fields.append('status')
            if baseline.cost != candidate.cost:
                changed_fields.append('cost')
            if baseline.predecessor != candidate.predecessor:
                changed_fields.append('predecessor')
            if baseline.path != candidate.path:
                changed_fields.append('path')
        if changed_fields:
            changed_route_count += 1
        else:
            unchanged_route_count += 1
        route_diffs.append(
            RouteDiff(
                node=node,
                baseline=baseline,
                candidate=candidate,
                changed_fields=tuple(changed_fields),
                summary=_summarize_route_diff(baseline, candidate, tuple(changed_fields)),
            )
        )

    return RoutingComparison(
        baseline_graph=baseline_report.graph_name,
        candidate_graph=candidate_report.graph_name,
        source=baseline_report.bellman_ford.source,
        baseline_negative_cycle=baseline_report.bellman_ford.negative_cycle,
        candidate_negative_cycle=candidate_report.bellman_ford.negative_cycle,
        edge_changes=tuple(edge_changes),
        route_diffs=tuple(route_diffs),
        changed_route_count=changed_route_count,
        unchanged_route_count=unchanged_route_count,
    )


def summarize_comparison_metrics(comparison: RoutingComparison) -> ComparisonMetrics:
    changed_diffs = tuple(diff for diff in comparison.route_diffs if diff.changed_fields)
    same_cost_reroutes = sum(
        1
        for diff in changed_diffs
        if (
            diff.baseline is not None
            and diff.candidate is not None
            and 'path' in diff.changed_fields
            and 'cost' not in diff.changed_fields
            and 'status' not in diff.changed_fields
            and 'presence' not in diff.changed_fields
            and diff.baseline.status == 'reachable'
            and diff.candidate.status == 'reachable'
        )
    )
    return ComparisonMetrics(
        changed_diffs=changed_diffs,
        same_cost_reroutes=same_cost_reroutes,
        cost_changes=sum(1 for diff in changed_diffs if 'cost' in diff.changed_fields),
        predecessor_changes=sum(1 for diff in changed_diffs if 'predecessor' in diff.changed_fields),
        status_changes=sum(1 for diff in changed_diffs if 'status' in diff.changed_fields),
        presence_changes=sum(1 for diff in changed_diffs if 'presence' in diff.changed_fields),
    )


def render_pretty_comparison(comparison: RoutingComparison) -> str:
    lines = [
        f'Route-table comparison: {comparison.baseline_graph} vs {comparison.candidate_graph}',
        f'Source: {comparison.source}',
        f'Changed edges: {len(comparison.edge_changes)}',
        f'Changed route entries: {comparison.changed_route_count}',
        f'Unchanged route entries: {comparison.unchanged_route_count}',
        'Baseline negative cycle: '
        + (' -> '.join(comparison.baseline_negative_cycle) if comparison.baseline_negative_cycle else 'none'),
        'Candidate negative cycle: '
        + (' -> '.join(comparison.candidate_negative_cycle) if comparison.candidate_negative_cycle else 'none'),
    ]

    lines.append('')
    lines.append('Edge changes:')
    if comparison.edge_changes:
        for change in comparison.edge_changes:
            lines.append(
                '- '
                + f'{change.source} -> {change.target}: '
                + f'{change.baseline_weight if change.baseline_weight is not None else "absent"} '
                + f'-> {change.candidate_weight if change.candidate_weight is not None else "absent"} '
                + f'({change.change})'
            )
    else:
        lines.append('- none')

    lines.append('')
    lines.append('Route diffs:')
    changed_diffs = [diff for diff in comparison.route_diffs if diff.changed_fields]
    if changed_diffs:
        for diff in changed_diffs:
            lines.append(
                '- '
                + f'{diff.node}: {diff.summary}'
            )
    else:
        lines.append('- none')
    return "\n".join(lines)


def render_markdown_comparison(comparison: RoutingComparison) -> str:
    lines = [
        f'# {comparison.baseline_graph} vs {comparison.candidate_graph} route diff report',
        '',
        f'- Source: {comparison.source}',
        f'- Changed edges: {len(comparison.edge_changes)}',
        f'- Changed route entries: {comparison.changed_route_count}',
        f'- Unchanged route entries: {comparison.unchanged_route_count}',
        '- Baseline negative cycle: '
        + (' -> '.join(comparison.baseline_negative_cycle) if comparison.baseline_negative_cycle else 'none'),
        '- Candidate negative cycle: '
        + (' -> '.join(comparison.candidate_negative_cycle) if comparison.candidate_negative_cycle else 'none'),
        '',
        '## Edge changes',
    ]
    if comparison.edge_changes:
        _markdown_table(
            lines,
            ['Source', 'Target', 'Baseline weight', 'Candidate weight', 'Change'],
            (
                [
                    change.source,
                    change.target,
                    str(change.baseline_weight) if change.baseline_weight is not None else 'absent',
                    str(change.candidate_weight) if change.candidate_weight is not None else 'absent',
                    change.change,
                ]
                for change in comparison.edge_changes
            ),
        )
    else:
        lines.append('- No edge changes.')

    lines.append('')
    lines.append('## Route-table diff')
    changed_diffs = [diff for diff in comparison.route_diffs if diff.changed_fields]
    if changed_diffs:
        _markdown_table(
            lines,
            [
                'Node',
                'Baseline cost',
                'Baseline predecessor',
                'Baseline path',
                'Baseline status',
                'Candidate cost',
                'Candidate predecessor',
                'Candidate path',
                'Candidate status',
                'Changed fields',
                'Summary',
            ],
            (
                [
                    diff.node,
                    _format_route_entry_cost(diff.baseline),
                    _format_route_entry_predecessor(diff.baseline),
                    _format_route_entry_path(diff.baseline),
                    _format_route_entry_status(diff.baseline),
                    _format_route_entry_cost(diff.candidate),
                    _format_route_entry_predecessor(diff.candidate),
                    _format_route_entry_path(diff.candidate),
                    _format_route_entry_status(diff.candidate),
                    ', '.join(diff.changed_fields),
                    diff.summary,
                ]
                for diff in changed_diffs
            ),
        )
    else:
        lines.append('- No route-table changes.')
    return "\n".join(lines) + "\n"


def _render_changed_field_badges(changed_fields: tuple[str, ...]) -> str:
    if not changed_fields:
        return '<span class="badge muted">unchanged</span>'
    return ''.join(
        f'<span class="badge field-{_html_escape(field)}">{_html_escape(field.replace("-", " "))}</span>'
        for field in changed_fields
    )


def _wrap_svg_text(text: str, *, width: int, max_lines: int) -> tuple[str, ...]:
    wrapped = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [text]
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(' .,:;') + '…'
    return tuple(wrapped)


def _render_svg_text_block(x: int, y: int, lines: Iterable[str], class_name: str, *, line_height: int = 20) -> str:
    lines_tuple = tuple(lines)
    if not lines_tuple:
        return ''
    tspans = [f'<tspan x="{x}" dy="0">{_html_escape(lines_tuple[0])}</tspan>']
    tspans.extend(
        f'<tspan x="{x}" dy="{line_height}">{_html_escape(line)}</tspan>'
        for line in lines_tuple[1:]
    )
    return f'<text x="{x}" y="{y}" class="{class_name}">' + ''.join(tspans) + '</text>'


def render_svg_comparison(comparison: RoutingComparison) -> str:
    metrics = summarize_comparison_metrics(comparison)
    same_cost_reroutes = metrics.same_cost_reroutes
    cost_changes = metrics.cost_changes
    predecessor_changes = metrics.predecessor_changes
    presence_changes = metrics.presence_changes
    featured_diffs = list(metrics.changed_diffs[:3])

    summary_cards: list[tuple[str, str, str]] = [
        ('Changed edges', str(len(comparison.edge_changes)), 'edge-weight or edge-presence differences'),
        ('Changed routes', str(comparison.changed_route_count), 'route-table entries that changed'),
        ('Same-cost reroutes', str(same_cost_reroutes), 'paths that shifted without a cost delta'),
        ('Predecessor changes', str(predecessor_changes), 'Bellman-Ford predecessor swaps'),
    ]
    if cost_changes:
        summary_cards.append(('Cost-changing routes', str(cost_changes), 'routes whose total cost changed'))
    elif presence_changes:
        summary_cards.append(('Node presence changes', str(presence_changes), 'nodes only present in one variant'))

    width = 1200
    card_width = 204
    card_height = 112
    route_card_height = 138
    footer_height = 42

    summary_y = 224
    route_y = summary_y + card_height + 18
    height = route_y + max(1, len(featured_diffs)) * route_card_height + footer_height

    elements: list[str] = []
    elements.append(f'<rect width="{width}" height="{height}" fill="#f8fafc" rx="28" />')
    elements.append(
        '<rect x="24" y="24" width="1152" height="184" rx="24" fill="#ffffff" stroke="#dbe3ef" />'
    )
    elements.append(_render_svg_text_block(52, 58, ('Graph routing diff snapshot',), 'eyebrow', line_height=18))
    elements.append(
        _render_svg_text_block(
            52,
            94,
            (f'{comparison.baseline_graph} vs {comparison.candidate_graph}',),
            'headline',
            line_height=22,
        )
    )
    lede = (
        f'Source {comparison.source}; baseline negative cycle '
        + ('present' if comparison.baseline_negative_cycle else 'none')
        + '; candidate negative cycle '
        + ('present' if comparison.candidate_negative_cycle else 'none')
        + '.'
    )
    elements.append(_render_svg_text_block(52, 126, _wrap_svg_text(lede, width=80, max_lines=2), 'lede', line_height=20))
    elements.append(
        _render_svg_text_block(
            52,
            168,
            (f'Edge changes: {len(comparison.edge_changes)}', f'Changed routes: {comparison.changed_route_count}', f'Unchanged routes: {comparison.unchanged_route_count}'),
            'meta',
            line_height=18,
        )
    )

    edge_preview_list = [
        f'{change.source}→{change.target}: '
        + f'{change.baseline_weight if change.baseline_weight is not None else "absent"}→{change.candidate_weight if change.candidate_weight is not None else "absent"}'
        for change in comparison.edge_changes[:3]
    ]
    if len(comparison.edge_changes) > 3:
        edge_preview_list.append(f'+{len(comparison.edge_changes) - 3} more edge changes')
    edge_preview_lines = tuple(edge_preview_list) or ('No edge changes',)
    elements.append('<rect x="774" y="48" width="364" height="136" rx="20" fill="#eff6ff" stroke="#bfdbfe" />')
    elements.append(_render_svg_text_block(798, 78, ('Edge preview',), 'sectionLabel', line_height=18))
    elements.append(_render_svg_text_block(798, 108, edge_preview_lines, 'smallMono', line_height=18))

    summary_start_x = 44
    summary_gap = 14
    for index, (label, value, description) in enumerate(summary_cards[:5]):
        x = summary_start_x + index * (card_width + summary_gap)
        elements.append(
            f'<rect x="{x}" y="{summary_y}" width="{card_width}" height="{card_height}" rx="20" fill="#ffffff" stroke="#dbe3ef" />'
        )
        elements.append(_render_svg_text_block(x + 18, summary_y + 34, (label,), 'cardLabel', line_height=16))
        elements.append(_render_svg_text_block(x + 18, summary_y + 72, (value,), 'cardValue', line_height=22))
        elements.append(
            _render_svg_text_block(
                x + 18,
                summary_y + 94,
                _wrap_svg_text(description, width=24, max_lines=2),
                'cardNote',
                line_height=15,
            )
        )

    for index, diff in enumerate(featured_diffs or [None]):
        y = route_y + index * route_card_height
        elements.append(
            f'<rect x="24" y="{y}" width="1152" height="{route_card_height - 14}" rx="22" fill="#ffffff" stroke="#dbe3ef" />'
        )
        if diff is None:
            elements.append(_render_svg_text_block(52, y + 44, ('No changed route entries. The baseline and candidate route tables match.',), 'routeSummary', line_height=20))
            continue
        accent = '#2563eb' if 'cost' in diff.changed_fields else ('#dc2626' if 'presence' in diff.changed_fields or 'status' in diff.changed_fields else '#7c3aed')
        elements.append(f'<rect x="24" y="{y}" width="12" height="{route_card_height - 14}" rx="6" fill="{accent}" />')
        elements.append(_render_svg_text_block(52, y + 28, (f'Node {diff.node}',), 'routeNode', line_height=18))
        badge_text = ' · '.join(field.replace('-', ' ') for field in diff.changed_fields) or 'unchanged'
        elements.append(_render_svg_text_block(52, y + 52, (badge_text,), 'routeBadge', line_height=18))
        summary_lines = _wrap_svg_text(diff.summary, width=74, max_lines=3)
        elements.append(_render_svg_text_block(52, y + 82, summary_lines, 'routeSummary', line_height=18))
        metric_lines = (
            f'cost {_format_route_entry_cost(diff.baseline)} → {_format_route_entry_cost(diff.candidate)}',
            f'predecessor {_format_route_entry_predecessor(diff.baseline)} → {_format_route_entry_predecessor(diff.candidate)}',
            f'delta {_format_cost_delta(diff.baseline, diff.candidate)}',
        )
        elements.append(_render_svg_text_block(760, y + 40, metric_lines, 'smallMono', line_height=18))
        path_lines = (
            f'baseline: {_format_route_entry_path(diff.baseline)}',
            f'candidate: {_format_route_entry_path(diff.candidate)}',
        )
        elements.append(
            _render_svg_text_block(
                760,
                y + 96,
                tuple(
                    line
                    for entry in path_lines
                    for line in _wrap_svg_text(entry, width=46, max_lines=2)
                ),
                'smallMono',
                line_height=17,
            )
        )

    footer_note = (
        f'Showing first {len(featured_diffs)} changed routes out of {len(metrics.changed_diffs)} total.'
        if len(metrics.changed_diffs) > len(featured_diffs)
        else 'Deterministic static artifact for README thumbnails, slide decks, and quick routing-change reviews.'
    )
    elements.append(_render_svg_text_block(38, height - 18, (footer_note,), 'footer', line_height=18))

    title_text = f'{comparison.baseline_graph} vs {comparison.candidate_graph} route diff summary card'
    desc_text = (
        f'Source {comparison.source}. Changed edges {len(comparison.edge_changes)}. '
        f'Changed routes {comparison.changed_route_count}. Same-cost reroutes {same_cost_reroutes}.'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" preserveAspectRatio="xMidYMin meet" role="img" aria-labelledby="svg-title svg-desc">
  <title id="svg-title">{_html_escape(title_text)}</title>
  <desc id="svg-desc">{_html_escape(desc_text)}</desc>
  <style>
    text {{ font-family: Inter, "Segoe UI", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif; fill: #10233d; }}
    .eyebrow {{ font-size: 16px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; fill: #2563eb; }}
    .headline {{ font-size: 30px; font-weight: 700; }}
    .lede {{ font-size: 16px; fill: #51627a; }}
    .meta {{ font-size: 15px; fill: #51627a; }}
    .sectionLabel {{ font-size: 16px; font-weight: 700; fill: #1d4ed8; }}
    .cardLabel {{ font-size: 15px; fill: #51627a; }}
    .cardValue {{ font-size: 32px; font-weight: 700; }}
    .cardNote {{ font-size: 13px; fill: #51627a; }}
    .routeNode {{ font-size: 20px; font-weight: 700; }}
    .routeBadge {{ font-size: 14px; font-weight: 700; fill: #2563eb; }}
    .routeSummary {{ font-size: 16px; fill: #10233d; }}
    .smallMono {{ font-family: "SFMono-Regular", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; fill: #334155; }}
    .footer {{ font-size: 14px; fill: #51627a; }}
  </style>
  {''.join(elements)}
</svg>
'''


def render_html_comparison(comparison: RoutingComparison) -> str:
    metrics = summarize_comparison_metrics(comparison)
    changed_diffs = list(metrics.changed_diffs)
    same_cost_reroutes = metrics.same_cost_reroutes
    cost_changes = metrics.cost_changes
    predecessor_changes = metrics.predecessor_changes
    presence_changes = metrics.presence_changes

    summary_cards = [
        ('Changed edges', str(len(comparison.edge_changes)), 'Edge-weight or edge-presence differences between the two graph variants.'),
        ('Changed routes', str(comparison.changed_route_count), 'Route-table entries whose cost, path, predecessor, or status changed.'),
        ('Same-cost reroutes', str(same_cost_reroutes), 'Routes that kept the same total cost but switched to a different path.'),
        ('Predecessor changes', str(predecessor_changes), 'Routes whose Bellman-Ford predecessor changed in the candidate graph.'),
    ]
    if presence_changes:
        summary_cards.append(
            ('Node presence changes', str(presence_changes), 'Nodes that only appear in one route table variant.')
        )
    if cost_changes:
        summary_cards.append(
            ('Cost-changing routes', str(cost_changes), 'Routes whose total Bellman-Ford cost changed between graphs.')
        )

    summary_cards_html = ''.join(
        f'''<article class="summary-card">
      <p class="summary-label">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description in summary_cards
    )

    route_cards_html = ''.join(
        f'''<article class="route-card {'route-card--cost' if 'cost' in diff.changed_fields else ('route-card--presence' if 'presence' in diff.changed_fields or 'status' in diff.changed_fields else 'route-card--path')}">
      <div class="route-card-header">
        <div>
          <p class="eyebrow">Node {_html_escape(diff.node)}</p>
          <h3>{_html_escape(diff.summary)}</h3>
        </div>
        <div class="badge-row">{_render_changed_field_badges(diff.changed_fields)}</div>
      </div>
      <dl class="route-metrics">
        <div><dt>Baseline cost</dt><dd>{_html_escape(_format_route_entry_cost(diff.baseline))}</dd></div>
        <div><dt>Candidate cost</dt><dd>{_html_escape(_format_route_entry_cost(diff.candidate))}</dd></div>
        <div><dt>Cost delta</dt><dd>{_html_escape(_format_cost_delta(diff.baseline, diff.candidate))}</dd></div>
        <div><dt>Baseline predecessor</dt><dd>{_html_escape(_format_route_entry_predecessor(diff.baseline))}</dd></div>
        <div><dt>Candidate predecessor</dt><dd>{_html_escape(_format_route_entry_predecessor(diff.candidate))}</dd></div>
        <div><dt>Status</dt><dd>{_html_escape(_format_route_entry_status(diff.baseline))} → {_html_escape(_format_route_entry_status(diff.candidate))}</dd></div>
      </dl>
      <div class="path-columns">
        <div>
          <p class="path-label">Baseline path</p>
          <code>{_html_escape(_format_route_entry_path(diff.baseline))}</code>
        </div>
        <div>
          <p class="path-label">Candidate path</p>
          <code>{_html_escape(_format_route_entry_path(diff.candidate))}</code>
        </div>
      </div>
    </article>'''
        for diff in changed_diffs
    ) or '<p class="empty-state">No changed route entries. The two route tables are identical for this source.</p>'

    edge_rows_html = ''.join(
        f'''<tr>
          <td><code>{_html_escape(change.source)}</code></td>
          <td><code>{_html_escape(change.target)}</code></td>
          <td>{_html_escape(str(change.baseline_weight) if change.baseline_weight is not None else 'absent')}</td>
          <td>{_html_escape(str(change.candidate_weight) if change.candidate_weight is not None else 'absent')}</td>
          <td><span class="badge field-{_html_escape(change.change)}">{_html_escape(change.change)}</span></td>
        </tr>'''
        for change in comparison.edge_changes
    ) or '<tr><td colspan="5" class="empty-cell">No edge changes.</td></tr>'

    route_table_rows_html = ''.join(
        f'''<tr class="{'row-cost' if 'cost' in diff.changed_fields else ('row-presence' if 'presence' in diff.changed_fields or 'status' in diff.changed_fields else 'row-path')}">
          <td><code>{_html_escape(diff.node)}</code></td>
          <td>{_html_escape(_format_route_entry_cost(diff.baseline))}</td>
          <td>{_html_escape(_format_route_entry_cost(diff.candidate))}</td>
          <td><code>{_html_escape(_format_route_entry_path(diff.baseline))}</code></td>
          <td><code>{_html_escape(_format_route_entry_path(diff.candidate))}</code></td>
          <td>{_html_escape(_format_route_entry_predecessor(diff.baseline))} → {_html_escape(_format_route_entry_predecessor(diff.candidate))}</td>
          <td><div class="badge-row">{_render_changed_field_badges(diff.changed_fields)}</div></td>
          <td>{_html_escape(diff.summary)}</td>
        </tr>'''
        for diff in changed_diffs
    ) or '<tr><td colspan="8" class="empty-cell">No route-table changes.</td></tr>'

    negative_cycle_note = ''
    if comparison.baseline_negative_cycle or comparison.candidate_negative_cycle:
        negative_cycle_note = f'''<section class="callout warning">
      <h2>Negative-cycle context</h2>
      <p>Baseline cycle: <code>{_html_escape(' -> '.join(comparison.baseline_negative_cycle) if comparison.baseline_negative_cycle else 'none')}</code></p>
      <p>Candidate cycle: <code>{_html_escape(' -> '.join(comparison.candidate_negative_cycle) if comparison.candidate_negative_cycle else 'none')}</code></p>
    </section>'''

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(comparison.baseline_graph)} vs {_html_escape(comparison.candidate_graph)} route diff dashboard</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --border: #dbe3ef;
        --text: #10233d;
        --muted: #51627a;
        --accent: #2563eb;
        --accent-soft: #dbeafe;
        --path: #7c3aed;
        --path-soft: #ede9fe;
        --warn: #dc2626;
        --warn-soft: #fee2e2;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: linear-gradient(180deg, #eff6ff 0%, var(--bg) 18rem); color: var(--text); }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
      .hero, .panel, .callout {{ background: var(--panel); border: 1px solid var(--border); border-radius: 20px; box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06); }}
      .hero {{ padding: 28px; margin-bottom: 20px; }}
      .eyebrow {{ margin: 0 0 8px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); }}
      h1, h2, h3 {{ margin: 0; }}
      .lede {{ margin: 14px 0 0; max-width: 72ch; color: var(--muted); line-height: 1.6; }}
      .meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; color: var(--muted); font-size: 0.95rem; }}
      .summary-grid, .route-card-grid {{ display: grid; gap: 16px; }}
      .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-bottom: 20px; }}
      .summary-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 18px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05); }}
      .summary-card strong {{ display: block; margin-top: 6px; font-size: 1.8rem; }}
      .summary-label {{ margin: 0; color: var(--muted); font-size: 0.92rem; }}
      .summary-card p:last-child {{ margin-bottom: 0; color: var(--muted); line-height: 1.5; }}
      .panel {{ padding: 24px; margin-bottom: 20px; }}
      .panel-header {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 16px; }}
      .panel-header p {{ margin: 8px 0 0; color: var(--muted); }}
      .route-card-grid {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
      .route-card {{ border: 1px solid var(--border); border-radius: 18px; padding: 18px; background: #fcfdff; }}
      .route-card--cost {{ background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%); border-color: #bfdbfe; }}
      .route-card--path {{ background: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%); border-color: #ddd6fe; }}
      .route-card--presence {{ background: linear-gradient(180deg, #ffffff 0%, #fef2f2 100%); border-color: #fecaca; }}
      .route-card-header {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 16px; }}
      .route-card h3 {{ margin-top: 4px; font-size: 1.05rem; line-height: 1.45; }}
      .badge-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
      .badge {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 10px; font-size: 0.8rem; font-weight: 700; background: var(--accent-soft); color: var(--accent); }}
      .badge.field-path {{ background: var(--path-soft); color: var(--path); }}
      .badge.field-cost, .badge.field-weight-changed {{ background: var(--accent-soft); color: var(--accent); }}
      .badge.field-predecessor {{ background: #e0f2fe; color: #0369a1; }}
      .badge.field-status, .badge.field-presence, .badge.field-added, .badge.field-removed {{ background: var(--warn-soft); color: var(--warn); }}
      .badge.muted {{ background: #e2e8f0; color: #475569; }}
      .route-metrics {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0 0 16px; }}
      .route-metrics div {{ padding: 10px 12px; background: rgba(255,255,255,0.8); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.25); }}
      .route-metrics dt {{ margin: 0 0 4px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
      .route-metrics dd {{ margin: 0; font-size: 1rem; font-weight: 600; }}
      .path-columns {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
      .path-label {{ margin: 0 0 6px; font-size: 0.84rem; color: var(--muted); }}
      code {{ display: inline-block; max-width: 100%; white-space: normal; word-break: break-word; font-family: "SFMono-Regular", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: rgba(15, 23, 42, 0.05); padding: 2px 6px; border-radius: 8px; }}
      .table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 16px; }}
      table {{ width: 100%; border-collapse: collapse; min-width: 760px; background: white; }}
      th, td {{ padding: 12px 14px; border-bottom: 1px solid #e2e8f0; vertical-align: top; text-align: left; }}
      th {{ background: #eff6ff; font-size: 0.84rem; text-transform: uppercase; letter-spacing: 0.05em; color: #1d4ed8; }}
      tr:last-child td {{ border-bottom: none; }}
      .row-cost td:first-child {{ box-shadow: inset 4px 0 0 var(--accent); }}
      .row-path td:first-child {{ box-shadow: inset 4px 0 0 var(--path); }}
      .row-presence td:first-child {{ box-shadow: inset 4px 0 0 var(--warn); }}
      .callout {{ padding: 20px 24px; margin-bottom: 20px; }}
      .callout.warning {{ background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%); border-color: #fdba74; }}
      .empty-state, .empty-cell {{ color: var(--muted); }}
      .empty-cell {{ text-align: center; padding: 18px; }}
      @media (max-width: 820px) {{
        main {{ padding-inline: 14px; }}
        .hero, .panel, .callout {{ border-radius: 16px; }}
        .route-card-header, .panel-header {{ flex-direction: column; align-items: start; }}
        .route-metrics, .path-columns {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Graph routing route diff dashboard</p>
        <h1>{_html_escape(comparison.baseline_graph)} → {_html_escape(comparison.candidate_graph)}</h1>
        <p class="lede">Bellman-Ford source <code>{_html_escape(comparison.source)}</code>. This static artifact turns the route-table diff into portfolio-friendly cards plus a detailed audit table so reviewers can quickly see whether the candidate graph changed path cost, predecessor, or only the chosen path.</p>
        <div class="meta">
          <span>Deterministic static artifact</span>
          <span>Changed routes: {comparison.changed_route_count}</span>
          <span>Unchanged routes: {comparison.unchanged_route_count}</span>
          <span>Edge changes: {len(comparison.edge_changes)}</span>
        </div>
      </section>

      <section class="summary-grid">
        {summary_cards_html}
      </section>

      {negative_cycle_note}

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>Changed route highlights</h2>
            <p>Card-style summaries make cost regressions, same-cost reroutes, and predecessor shifts easy to show in screenshots.</p>
          </div>
        </div>
        <div class="route-card-grid">
          {route_cards_html}
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>Edge changes</h2>
            <p>Direct graph differences that explain the route-table shifts.</p>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Target</th>
                <th>Baseline weight</th>
                <th>Candidate weight</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {edge_rows_html}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>Route-table diff audit</h2>
            <p>Detailed baseline-versus-candidate comparison for the changed nodes only.</p>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Node</th>
                <th>Baseline cost</th>
                <th>Candidate cost</th>
                <th>Baseline path</th>
                <th>Candidate path</th>
                <th>Predecessor shift</th>
                <th>Changed fields</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {route_table_rows_html}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </body>
</html>
'''


def export_compare_markdown(comparison: RoutingComparison, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_comparison(comparison), encoding='utf-8')
    return output


def export_compare_html(comparison: RoutingComparison, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html_comparison(comparison), encoding='utf-8')
    return output


def export_compare_svg(comparison: RoutingComparison, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_svg_comparison(comparison), encoding='utf-8')
    return output


def relative_output_path(target: str | Path, output_path: str | Path) -> str:
    return Path(os.path.relpath(Path(target), start=Path(output_path).parent)).as_posix()


def _validate_non_empty_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'gallery manifest field {field_name!r} must be a non-empty string')
    return value.strip()


def _resolve_manifest_path(base_dir: Path, raw_path: object, *, field_name: str) -> Path:
    text = _validate_non_empty_string(raw_path, field_name=field_name)
    path = Path(text)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _load_gallery_artifacts(base_dir: Path, payload: object, *, scenario_slug: str) -> tuple[GalleryArtifact, ...]:
    if payload is None:
        return tuple()
    if not isinstance(payload, list):
        raise ValueError(f'gallery manifest scenario {scenario_slug!r} must define artifacts as a list')
    artifacts: list[GalleryArtifact] = []
    for index, artifact_payload in enumerate(payload, start=1):
        if not isinstance(artifact_payload, dict):
            raise ValueError(
                f'gallery manifest scenario {scenario_slug!r} artifact #{index} must be an object'
            )
        label = _validate_non_empty_string(
            artifact_payload.get('label'),
            field_name=f'{scenario_slug}.artifacts[{index}].label',
        )
        description = _validate_non_empty_string(
            artifact_payload.get('description'),
            field_name=f'{scenario_slug}.artifacts[{index}].description',
        )
        artifact_path = _resolve_manifest_path(
            base_dir,
            artifact_payload.get('path'),
            field_name=f'{scenario_slug}.artifacts[{index}].path',
        )
        if not artifact_path.exists():
            raise ValueError(
                f'gallery manifest scenario {scenario_slug!r} references a missing artifact: {artifact_path}'
            )
        artifacts.append(GalleryArtifact(label=label, path=artifact_path, description=description))
    return tuple(artifacts)


def load_routing_gallery_manifest(path: str | Path) -> RoutingGallery:
    manifest_path = Path(path).resolve()
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('gallery manifest must be a JSON object')
    scenarios_payload = payload.get('scenarios')
    if not isinstance(scenarios_payload, list) or not scenarios_payload:
        raise ValueError('gallery manifest must include a non-empty scenarios list')

    base_dir = manifest_path.parent
    title = _validate_non_empty_string(payload.get('title', 'Graph routing diff gallery'), field_name='title')
    description = _validate_non_empty_string(
        payload.get(
            'description',
            'Portfolio-friendly landing page for multiple route-diff scenarios and their artifact bundles.',
        ),
        field_name='description',
    )

    scenarios: list[GalleryScenario] = []
    seen_slugs: set[str] = set()
    for index, scenario_payload in enumerate(scenarios_payload, start=1):
        if not isinstance(scenario_payload, dict):
            raise ValueError(f'gallery manifest scenario #{index} must be an object')
        slug = _validate_non_empty_string(
            scenario_payload.get('slug'),
            field_name=f'scenarios[{index}].slug',
        )
        if slug in seen_slugs:
            raise ValueError(f'gallery manifest scenario slugs must be unique; duplicate {slug!r}')
        seen_slugs.add(slug)
        title_text = _validate_non_empty_string(scenario_payload.get('title'), field_name=f'{slug}.title')
        description_text = _validate_non_empty_string(
            scenario_payload.get('description'),
            field_name=f'{slug}.description',
        )
        source = _validate_non_empty_string(scenario_payload.get('source'), field_name=f'{slug}.source')
        baseline_graph = _resolve_manifest_path(
            base_dir,
            scenario_payload.get('baseline_graph'),
            field_name=f'{slug}.baseline_graph',
        )
        candidate_graph = _resolve_manifest_path(
            base_dir,
            scenario_payload.get('candidate_graph'),
            field_name=f'{slug}.candidate_graph',
        )
        if not baseline_graph.exists():
            raise ValueError(f'gallery manifest baseline graph does not exist: {baseline_graph}')
        if not candidate_graph.exists():
            raise ValueError(f'gallery manifest candidate graph does not exist: {candidate_graph}')
        artifacts = _load_gallery_artifacts(base_dir, scenario_payload.get('artifacts', []), scenario_slug=slug)
        scenarios.append(
            GalleryScenario(
                slug=slug,
                title=title_text,
                description=description_text,
                baseline_graph=baseline_graph,
                candidate_graph=candidate_graph,
                source=source,
                artifacts=artifacts,
            )
        )

    return RoutingGallery(
        title=title,
        description=description,
        manifest_path=manifest_path,
        scenarios=tuple(scenarios),
    )


def _scenario_story_label(
    comparison: RoutingComparison,
    *,
    same_cost_reroutes: int,
    cost_changes: int,
    status_changes: int,
) -> str:
    if comparison.baseline_negative_cycle is None and comparison.candidate_negative_cycle is not None:
        return 'candidate introduces a reachable negative cycle'
    if comparison.baseline_negative_cycle is not None and comparison.candidate_negative_cycle is None:
        return 'candidate clears the reachable negative cycle'
    if status_changes:
        return 'reachability or route status changes'
    if same_cost_reroutes:
        return 'same-cost reroutes with path churn'
    if cost_changes:
        return 'cost-changing route regression or improvement'
    return 'edge changes without route-table movement'


def summarize_gallery_scenario(scenario: GalleryScenario) -> GalleryScenarioSummary:
    baseline_graph_name, baseline_nodes, baseline_edges = load_graph(scenario.baseline_graph)
    candidate_graph_name, candidate_nodes, candidate_edges = load_graph(scenario.candidate_graph)
    baseline_report = build_report(
        baseline_graph_name,
        baseline_nodes,
        baseline_edges,
        source=scenario.source,
        mode='bellman-ford',
    )
    candidate_report = build_report(
        candidate_graph_name,
        candidate_nodes,
        candidate_edges,
        source=scenario.source,
        mode='bellman-ford',
    )
    comparison = compare_reports(baseline_report, candidate_report)
    metrics = summarize_comparison_metrics(comparison)
    same_cost_reroutes = metrics.same_cost_reroutes
    cost_changes = metrics.cost_changes
    predecessor_changes = metrics.predecessor_changes
    status_changes = metrics.status_changes
    changed_nodes = tuple(diff.node for diff in metrics.changed_diffs[:4])
    return GalleryScenarioSummary(
        scenario=scenario,
        comparison=comparison,
        baseline_graph_name=baseline_graph_name,
        candidate_graph_name=candidate_graph_name,
        same_cost_reroutes=same_cost_reroutes,
        cost_changes=cost_changes,
        predecessor_changes=predecessor_changes,
        status_changes=status_changes,
        changed_nodes=changed_nodes,
        story_label=_scenario_story_label(
            comparison,
            same_cost_reroutes=same_cost_reroutes,
            cost_changes=cost_changes,
            status_changes=status_changes,
        ),
    )


def build_gallery_summaries(gallery: RoutingGallery) -> tuple[GalleryScenarioSummary, ...]:
    return tuple(summarize_gallery_scenario(scenario) for scenario in gallery.scenarios)


def render_markdown_gallery(gallery: RoutingGallery, *, output_path: str | Path) -> str:
    summaries = build_gallery_summaries(gallery)
    total_changed_routes = sum(summary.comparison.changed_route_count for summary in summaries)
    negative_cycle_scenarios = sum(1 for summary in summaries if summary.comparison.candidate_negative_cycle)
    same_cost_reroute_scenarios = sum(1 for summary in summaries if summary.same_cost_reroutes)
    lines = [
        f'# {gallery.title}',
        '',
        gallery.description,
        '',
        '## Gallery summary',
        '| metric | value |',
        '| --- | --- |',
        f'| scenario count | {len(summaries)} |',
        f'| total changed routes | {total_changed_routes} |',
        f'| scenarios with candidate negative cycles | {negative_cycle_scenarios} |',
        f'| scenarios featuring same-cost reroutes | {same_cost_reroute_scenarios} |',
        '',
        '## Scenario overview',
        '| Scenario | Source | Story | Changed edges | Changed routes | Linked artifacts |',
        '| --- | --- | --- | ---: | ---: | --- |',
    ]
    for summary in summaries:
        artifact_links = ', '.join(
            f'[{artifact.label}]({relative_output_path(artifact.path, output_path)})'
            for artifact in summary.scenario.artifacts
        ) or '—'
        lines.append(
            '| ' + ' | '.join(
                [
                    f'[{summary.scenario.title}](#{summary.scenario.slug})',
                    summary.scenario.source,
                    summary.story_label,
                    str(len(summary.comparison.edge_changes)),
                    str(summary.comparison.changed_route_count),
                    artifact_links,
                ]
            ) + ' |'
        )

    lines.append('')
    lines.append('## Scenario cards')
    for summary in summaries:
        lines.extend(
            [
                '',
                f'<a id="{summary.scenario.slug}"></a>',
                f'### {summary.scenario.title}',
                summary.scenario.description,
                '',
                f'- Source: `{summary.scenario.source}`',
                f'- Baseline graph: `{summary.baseline_graph_name}`',
                f'- Candidate graph: `{summary.candidate_graph_name}`',
                f'- Story label: {summary.story_label}',
                f'- Changed edges: {len(summary.comparison.edge_changes)}',
                f'- Changed route entries: {summary.comparison.changed_route_count}',
                f'- Same-cost reroutes: {summary.same_cost_reroutes}',
                f'- Cost-changing routes: {summary.cost_changes}',
                f'- Predecessor changes: {summary.predecessor_changes}',
                f'- Status changes: {summary.status_changes}',
                '- Baseline negative cycle: '
                + (
                    ' -> '.join(summary.comparison.baseline_negative_cycle)
                    if summary.comparison.baseline_negative_cycle
                    else 'none'
                ),
                '- Candidate negative cycle: '
                + (
                    ' -> '.join(summary.comparison.candidate_negative_cycle)
                    if summary.comparison.candidate_negative_cycle
                    else 'none'
                ),
                '- Changed nodes preview: ' + (', '.join(summary.changed_nodes) if summary.changed_nodes else 'none'),
            ]
        )
        if summary.scenario.artifacts:
            lines.extend(['', '#### Linked artifacts'])
            for artifact in summary.scenario.artifacts:
                lines.append(
                    f'- [{artifact.label}]({relative_output_path(artifact.path, output_path)}) — {artifact.description}'
                )
    return "\n".join(lines) + "\n"


def render_html_gallery(gallery: RoutingGallery, *, output_path: str | Path) -> str:
    summaries = build_gallery_summaries(gallery)
    total_changed_routes = sum(summary.comparison.changed_route_count for summary in summaries)
    negative_cycle_scenarios = sum(1 for summary in summaries if summary.comparison.candidate_negative_cycle)
    same_cost_reroute_scenarios = sum(1 for summary in summaries if summary.same_cost_reroutes)
    summary_cards_html = ''.join(
        f'''<article class="summary-card">
      <p class="eyebrow">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description in (
            ('Scenario count', str(len(summaries)), 'Distinct graph-to-graph routing stories bundled into one landing page.'),
            ('Changed routes', str(total_changed_routes), 'Total changed route-table entries across the committed scenarios.'),
            ('Candidate negative cycles', str(negative_cycle_scenarios), 'Scenarios where the candidate graph makes shortest paths unstable.'),
            ('Scenarios featuring same-cost reroutes', str(same_cost_reroute_scenarios), 'Scenarios containing at least one path shift without a headline distance change.'),
        )
    )
    scenario_cards_html = ''.join(
        f'''<article class="scenario-card" id="{_html_escape(summary.scenario.slug)}">
      <div class="scenario-card__header">
        <div>
          <p class="eyebrow">{_html_escape(summary.scenario.slug)}</p>
          <h2><a class="scenario-link" href="#{_html_escape(summary.scenario.slug)}">{_html_escape(summary.scenario.title)}</a></h2>
        </div>
        <span class="pill">source {_html_escape(summary.scenario.source)}</span>
      </div>
      <p class="lede">{_html_escape(summary.scenario.description)}</p>
      <p class="story-label">{_html_escape(summary.story_label)}</p>
      <dl class="metric-list">
        <div><dt>Baseline</dt><dd><code>{_html_escape(summary.baseline_graph_name)}</code></dd></div>
        <div><dt>Candidate</dt><dd><code>{_html_escape(summary.candidate_graph_name)}</code></dd></div>
        <div><dt>Changed edges</dt><dd>{len(summary.comparison.edge_changes)}</dd></div>
        <div><dt>Changed routes</dt><dd>{summary.comparison.changed_route_count}</dd></div>
        <div><dt>Same-cost reroutes</dt><dd>{summary.same_cost_reroutes}</dd></div>
        <div><dt>Status changes</dt><dd>{summary.status_changes}</dd></div>
      </dl>
      <p class="cycle-note"><strong>Baseline cycle:</strong> {_html_escape(' -> '.join(summary.comparison.baseline_negative_cycle) if summary.comparison.baseline_negative_cycle else 'none')}<br><strong>Candidate cycle:</strong> {_html_escape(' -> '.join(summary.comparison.candidate_negative_cycle) if summary.comparison.candidate_negative_cycle else 'none')}</p>
      <p class="changed-nodes"><strong>Changed nodes:</strong> {_html_escape(', '.join(summary.changed_nodes) if summary.changed_nodes else 'none')}</p>
      <section class="artifact-list">
        <h3>Linked artifacts</h3>
        {''.join(
            f'''<article class="artifact-card"><h4><a href="{_html_escape(relative_output_path(artifact.path, output_path))}">{_html_escape(artifact.label)}</a></h4><p>{_html_escape(artifact.description)}</p></article>'''
            for artifact in summary.scenario.artifacts
        ) or '<p class="empty-state">No linked artifacts were supplied for this scenario.</p>'}
      </section>
    </article>'''
        for summary in summaries
    )
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(gallery.title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --border: #dbe3ef;
        --text: #10233d;
        --muted: #51627a;
        --accent: #2563eb;
        --accent-soft: #dbeafe;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: linear-gradient(180deg, #eff6ff 0%, var(--bg) 18rem); color: var(--text); }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
      .hero, .summary-card, .scenario-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 20px; box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06); }}
      .hero {{ padding: 28px; margin-bottom: 20px; }}
      .eyebrow {{ margin: 0 0 8px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); }}
      h1, h2, h3, h4 {{ margin: 0; }}
      .hero p, .lede, .summary-card p, .artifact-card p {{ color: var(--muted); line-height: 1.6; }}
      .summary-grid, .scenario-grid {{ display: grid; gap: 16px; }}
      .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); margin-bottom: 20px; }}
      .scenario-grid {{ grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); }}
      .summary-card, .scenario-card {{ padding: 20px; }}
      .summary-card strong {{ display: block; margin-top: 6px; font-size: 1.9rem; }}
      .scenario-card__header {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; }}
      .pill {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 5px 12px; font-size: 0.82rem; font-weight: 700; background: var(--accent-soft); color: var(--accent); }}
      .story-label {{ font-weight: 700; color: #1d4ed8; }}
      .scenario-link {{ color: inherit; text-decoration: none; }}
      .scenario-link:hover {{ text-decoration: underline; }}
      .metric-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
      .metric-list div {{ padding: 10px 12px; background: rgba(255,255,255,0.8); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.25); }}
      .metric-list dt {{ margin: 0 0 4px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
      .metric-list dd {{ margin: 0; font-size: 1rem; font-weight: 600; }}
      .cycle-note, .changed-nodes {{ color: var(--muted); }}
      code {{ font-family: "SFMono-Regular", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: rgba(15, 23, 42, 0.05); padding: 2px 6px; border-radius: 8px; }}
      .artifact-list {{ display: grid; gap: 12px; margin-top: 16px; }}
      .artifact-card {{ border: 1px solid var(--border); border-radius: 14px; padding: 14px; background: #fcfdff; }}
      .artifact-card a {{ color: #1d4ed8; text-decoration: none; }}
      .artifact-card a:hover {{ text-decoration: underline; }}
      .empty-state {{ color: var(--muted); }}
      @media (max-width: 820px) {{
        main {{ padding-inline: 14px; }}
        .hero, .summary-card, .scenario-card {{ border-radius: 16px; }}
        .scenario-card__header {{ flex-direction: column; align-items: start; }}
        .metric-list {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Graph routing negative-cycle lab</p>
        <h1>{_html_escape(gallery.title)}</h1>
        <p>{_html_escape(gallery.description)}</p>
      </section>
      <section class="summary-grid">
        {summary_cards_html}
      </section>
      <section class="scenario-grid">
        {scenario_cards_html}
      </section>
    </main>
  </body>
</html>
'''


def export_gallery_markdown(gallery: RoutingGallery, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_gallery(gallery, output_path=output), encoding='utf-8')
    return output


def export_gallery_html(gallery: RoutingGallery, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html_gallery(gallery, output_path=output), encoding='utf-8')
    return output


def build_report(
    graph_name: str,
    nodes: Iterable[str],
    edges: Iterable[Edge],
    *,
    source: str | None,
    mode: str,
) -> RoutingReport:
    ordered_nodes = tuple(nodes)
    ordered_edges = tuple(edges)
    bf = None
    johnson_result = None
    if mode in {"bellman-ford", "full"}:
        if not source:
            raise ValueError("--source is required for bellman-ford/full mode")
        bf = bellman_ford(ordered_nodes, ordered_edges, source)
    if mode in {"johnson", "full"}:
        johnson_result = johnson(ordered_nodes, ordered_edges)
    return RoutingReport(graph_name=graph_name, nodes=ordered_nodes, edges=ordered_edges, bellman_ford=bf, johnson=johnson_result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore Bellman-Ford, Johnson's algorithm, and negative cycles.")
    parser.add_argument("graph", nargs="?", help="Path to a graph JSON file")
    parser.add_argument("--source", help="Bellman-Ford source node")
    parser.add_argument(
        "--mode",
        choices=("bellman-ford", "johnson", "full"),
        default="full",
        help="Which analysis to run",
    )
    parser.add_argument("--format", choices=("json", "pretty"), default="pretty")
    parser.add_argument("--compare-graph", help="Path to a second graph JSON file for route-table comparison")
    parser.add_argument("--export-mermaid", help="Write a Mermaid flowchart artifact for the selected report")
    parser.add_argument("--export-dot", help="Write a Graphviz DOT artifact for the selected report")
    parser.add_argument("--export-markdown", help="Write a Markdown routing report artifact for the selected report")
    parser.add_argument(
        "--export-compare-markdown",
        help="Write a Markdown route-table diff artifact comparing the main graph to --compare-graph",
    )
    parser.add_argument(
        "--export-compare-html",
        help="Write a static HTML route-table diff dashboard comparing the main graph to --compare-graph",
    )
    parser.add_argument(
        "--export-compare-svg",
        help="Write a compact SVG route-table diff summary card comparing the main graph to --compare-graph",
    )
    parser.add_argument(
        "--gallery-manifest",
        help="Path to a JSON manifest that describes several route-diff scenarios for a gallery landing page",
    )
    parser.add_argument(
        "--export-gallery-markdown",
        help="Write a Markdown gallery landing page from --gallery-manifest",
    )
    parser.add_argument(
        "--export-gallery-html",
        help="Write a static HTML gallery landing page from --gallery-manifest",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gallery_mode = bool(args.gallery_manifest or args.export_gallery_markdown or args.export_gallery_html)
    if gallery_mode:
        if args.graph is not None:
            raise ValueError('gallery exports do not use the graph positional argument')
        if not args.gallery_manifest:
            if args.export_gallery_markdown:
                raise ValueError('--export-gallery-markdown requires --gallery-manifest')
            raise ValueError('--export-gallery-html requires --gallery-manifest')
        if not args.export_gallery_markdown and not args.export_gallery_html:
            raise ValueError('--gallery-manifest requires --export-gallery-markdown and/or --export-gallery-html')
        gallery = load_routing_gallery_manifest(args.gallery_manifest)
        if args.export_gallery_markdown:
            export_gallery_markdown(gallery, args.export_gallery_markdown)
        if args.export_gallery_html:
            export_gallery_html(gallery, args.export_gallery_html)
        print(
            json.dumps(
                {
                    'gallery': gallery.title,
                    'scenario_count': len(gallery.scenarios),
                    'markdown_output': args.export_gallery_markdown,
                    'html_output': args.export_gallery_html,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    if not args.graph:
        raise ValueError('graph is required unless --gallery-manifest is used')
    graph_name, nodes, edges = load_graph(args.graph)
    report = build_report(graph_name, nodes, edges, source=args.source, mode=args.mode)
    if args.export_mermaid:
        export_mermaid(report, args.export_mermaid)
    if args.export_dot:
        export_dot(report, args.export_dot)
    if args.export_markdown:
        export_markdown(report, args.export_markdown)
    if args.export_compare_markdown and not args.compare_graph:
        raise ValueError('--export-compare-markdown requires --compare-graph')
    if args.export_compare_html and not args.compare_graph:
        raise ValueError('--export-compare-html requires --compare-graph')
    if args.export_compare_svg and not args.compare_graph:
        raise ValueError('--export-compare-svg requires --compare-graph')
    if args.compare_graph:
        if args.mode not in {'bellman-ford', 'full'} or not args.source:
            raise ValueError('--compare-graph requires --mode bellman-ford/full with --source')
        candidate_graph_name, candidate_nodes, candidate_edges = load_graph(args.compare_graph)
        candidate_report = build_report(
            candidate_graph_name,
            candidate_nodes,
            candidate_edges,
            source=args.source,
            mode=args.mode,
        )
        comparison = compare_reports(report, candidate_report)
        if args.export_compare_markdown:
            export_compare_markdown(comparison, args.export_compare_markdown)
        if args.export_compare_html:
            export_compare_html(comparison, args.export_compare_html)
        if args.export_compare_svg:
            export_compare_svg(comparison, args.export_compare_svg)
        if args.format == 'json':
            print(
                json.dumps(
                    {
                        'baseline': report.to_dict(),
                        'candidate': candidate_report.to_dict(),
                        'comparison': comparison.to_dict(),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return
        print(render_pretty_comparison(comparison))
        return
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    print(render_pretty(report))


if __name__ == "__main__":
    main()
