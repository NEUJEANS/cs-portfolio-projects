from __future__ import annotations

import argparse
import json
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
            predecessor = report.bellman_ford.predecessors[node]
            lines.append(f"- {node}: dist={distance} predecessor={predecessor}")
        if report.bellman_ford.negative_cycle:
            lines.append("Negative cycle: " + " -> ".join(report.bellman_ford.negative_cycle))
    if report.johnson:
        lines.append("")
        lines.append("Johnson all-pairs shortest paths:")
        for source, targets in sorted(report.johnson.paths.items()):
            lines.append(f"[{source}]")
            for target, result in sorted(targets.items()):
                path_text = " -> ".join(result.path) if result.path else "unreachable"
                lines.append(f"  {target}: cost={result.cost} path={path_text}")
    return "\n".join(lines)


def _sanitize_identifier(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


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
    parser.add_argument("--export-mermaid", help="Write a Mermaid flowchart artifact for the selected report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph_name, nodes, edges = load_graph(args.graph)
    report = build_report(graph_name, nodes, edges, source=args.source, mode=args.mode)
    if args.export_mermaid:
        export_mermaid(report, args.export_mermaid)
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    print(render_pretty(report))


if __name__ == "__main__":
    main()
