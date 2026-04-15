import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DirectedGraph:
    adjacency: dict[str, tuple[str, ...]]

    @property
    def nodes(self) -> tuple[str, ...]:
        return tuple(self.adjacency.keys())

    @property
    def edge_count(self) -> int:
        return sum(len(neighbors) for neighbors in self.adjacency.values())


def _normalize_node(value: object) -> str:
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"node identifiers must be strings or numbers, got {value!r}")
    text = str(value)
    if not text:
        raise ValueError('node identifiers must not be empty')
    return text


def load_graph(path: str | Path) -> DirectedGraph:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict) and 'edges' in payload:
        nodes = [_normalize_node(node) for node in payload.get('nodes', [])]
        adjacency: dict[str, list[str]] = {node: [] for node in nodes}
        edges = payload['edges']
        if not isinstance(edges, list):
            raise ValueError('edges must be a list')
        for edge in edges:
            if not isinstance(edge, dict) or 'from' not in edge or 'to' not in edge:
                raise ValueError('each edge must be an object with from/to fields')
            src = _normalize_node(edge['from'])
            dst = _normalize_node(edge['to'])
            adjacency.setdefault(src, [])
            adjacency.setdefault(dst, [])
            adjacency[src].append(dst)
    elif isinstance(payload, dict):
        adjacency = {}
        for raw_node, raw_neighbors in payload.items():
            node = _normalize_node(raw_node)
            if not isinstance(raw_neighbors, list):
                raise ValueError('adjacency-list values must be lists')
            adjacency[node] = [_normalize_node(neighbor) for neighbor in raw_neighbors]
        for neighbors in list(adjacency.values()):
            for neighbor in neighbors:
                adjacency.setdefault(neighbor, [])
    else:
        raise ValueError('graph JSON must be an adjacency object or {nodes, edges} object')
    normalized = {node: tuple(neighbors) for node, neighbors in sorted(adjacency.items())}
    return DirectedGraph(normalized)


def tarjan_strongly_connected_components(graph: DirectedGraph) -> list[list[str]]:
    index = 0
    index_for: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        index_for[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in graph.adjacency[node]:
            if neighbor not in index_for:
                visit(neighbor)
                lowlink[node] = min(lowlink[node], lowlink[neighbor])
            elif neighbor in on_stack:
                lowlink[node] = min(lowlink[node], index_for[neighbor])

        if lowlink[node] == index_for[node]:
            component: list[str] = []
            while True:
                popped = stack.pop()
                on_stack.remove(popped)
                component.append(popped)
                if popped == node:
                    break
            components.append(sorted(component))

    for node in graph.nodes:
        if node not in index_for:
            visit(node)

    components.sort(key=lambda component: (len(component) == 1, -len(component), component))
    return components


def build_component_graph(graph: DirectedGraph, components: list[list[str]]) -> tuple[list[dict[str, object]], list[tuple[int, int]]]:
    component_for: dict[str, int] = {}
    summaries = []
    for index, component in enumerate(components):
        component_id = f'C{index}'
        for node in component:
            component_for[node] = index
        has_self_loop = any(neighbor == node for node in component for neighbor in graph.adjacency[node])
        summaries.append({'id': component_id, 'nodes': component, 'size': len(component), 'self_loop': has_self_loop})

    dag_edges: set[tuple[int, int]] = set()
    for src, neighbors in graph.adjacency.items():
        for dst in neighbors:
            src_index = component_for[src]
            dst_index = component_for[dst]
            if src_index != dst_index:
                dag_edges.add((src_index, dst_index))

    return summaries, sorted(dag_edges)


def compute_component_levels(component_count: int, dag_edges: list[tuple[int, int]]) -> dict[int, int]:
    incoming_counts = {index: 0 for index in range(component_count)}
    outgoing: dict[int, list[int]] = {index: [] for index in range(component_count)}
    for src, dst in dag_edges:
        outgoing[src].append(dst)
        incoming_counts[dst] += 1

    frontier = deque(sorted(index for index, count in incoming_counts.items() if count == 0))
    levels = {index: 0 for index in frontier}

    while frontier:
        current = frontier.popleft()
        for neighbor in outgoing[current]:
            levels[neighbor] = max(levels.get(neighbor, 0), levels[current] + 1)
            incoming_counts[neighbor] -= 1
            if incoming_counts[neighbor] == 0:
                frontier.append(neighbor)

    for index in range(component_count):
        levels.setdefault(index, 0)
    return levels


def condensation_dag(graph: DirectedGraph, components: list[list[str]]) -> dict[str, object]:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    return {
        'components': [
            {
                'id': summary['id'],
                'nodes': summary['nodes'],
                'size': summary['size'],
                'topology_level': levels[index],
            }
            for index, summary in enumerate(summaries)
        ],
        'edges': [
            {'from': f'C{src}', 'to': f'C{dst}'}
            for src, dst in dag_edges
        ],
        'edge_count': len(dag_edges),
        'level_count': (max(levels.values()) + 1) if levels else 0,
    }


def summarize_components(graph: DirectedGraph, components: list[list[str]]) -> dict[str, object]:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    sizes = sorted((summary['size'] for summary in summaries), reverse=True)
    source_components = {index for index, _ in dag_edges}
    sink_components = {index for _, index in dag_edges}
    cyclic_components = sum(1 for summary in summaries if summary['size'] > 1 or summary['self_loop'])
    return {
        'node_count': len(graph.nodes),
        'edge_count': graph.edge_count,
        'component_count': len(components),
        'largest_component_size': sizes[0] if sizes else 0,
        'acyclic': cyclic_components == 0,
        'cyclic_component_count': cyclic_components,
        'source_component_count': len(components) - len(sink_components),
        'sink_component_count': len(components) - len(source_components),
        'condensation_edge_count': len(dag_edges),
        'condensation_level_count': (max(levels.values()) + 1) if levels else 0,
        'components': [
            {
                'id': summary['id'],
                'size': summary['size'],
                'nodes': summary['nodes'],
                'self_loop': summary['self_loop'],
                'topology_level': levels[index],
            }
            for index, summary in enumerate(summaries)
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze strongly connected components with Tarjan's algorithm.")
    parser.add_argument('graph_path', help='Path to a JSON adjacency list or {nodes, edges} graph file')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('scc', help='Print SCC summary as JSON')
    subparsers.add_parser('condensation', help='Print SCC condensation DAG as JSON')
    explain = subparsers.add_parser('explain', help='Print a concise text explanation')
    explain.add_argument('--limit', type=int, default=5, help='Maximum number of components to describe')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    graph = load_graph(args.graph_path)
    components = tarjan_strongly_connected_components(graph)

    if args.command == 'scc':
        print(json.dumps(summarize_components(graph, components), indent=2))
        return 0
    if args.command == 'condensation':
        print(json.dumps(condensation_dag(graph, components), indent=2))
        return 0
    if args.command == 'explain':
        limit = max(1, args.limit)
        summary = summarize_components(graph, components)
        lines = [
            f"Graph has {len(graph.nodes)} nodes, {graph.edge_count} directed edges, and {len(components)} strongly connected components.",
            f"Largest component size: {max((len(component) for component in components), default=0)}.",
            f"Condensation DAG spans {summary['condensation_level_count']} topological level(s).",
        ]
        for index, component_summary in enumerate(summary['components'][:limit]):
            lines.append(
                f"C{index} (level {component_summary['topology_level']}): {', '.join(component_summary['nodes'])}"
            )
        print("\n".join(lines))
        return 0
    parser.error(f'unsupported command: {args.command}')
    return 2


if __name__ == '__main__':
    sys.exit(main())
