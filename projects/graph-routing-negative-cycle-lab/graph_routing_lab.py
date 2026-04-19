from __future__ import annotations

import argparse
import json
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


def export_compare_markdown(comparison: RoutingComparison, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_comparison(comparison), encoding='utf-8')
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
    parser.add_argument("graph", help="Path to a graph JSON file")
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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
