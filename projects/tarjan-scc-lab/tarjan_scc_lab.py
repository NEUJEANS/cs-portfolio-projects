import argparse
import csv
import json
import sys
from io import StringIO
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


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


def _sort_components(components: list[list[str]]) -> list[list[str]]:
    components.sort(key=lambda component: (len(component) == 1, -len(component), component))
    return components


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

    return _sort_components(components)


def transpose_graph(graph: DirectedGraph) -> DirectedGraph:
    transposed = {node: [] for node in graph.nodes}
    for src, neighbors in graph.adjacency.items():
        for dst in neighbors:
            transposed.setdefault(dst, []).append(src)
    normalized = {node: tuple(sorted(neighbors)) for node, neighbors in sorted(transposed.items())}
    return DirectedGraph(normalized)


def kosaraju_strongly_connected_components(graph: DirectedGraph) -> list[list[str]]:
    visited: set[str] = set()
    finish_order: list[str] = []

    def dfs_finish(node: str) -> None:
        visited.add(node)
        for neighbor in graph.adjacency[node]:
            if neighbor not in visited:
                dfs_finish(neighbor)
        finish_order.append(node)

    for node in graph.nodes:
        if node not in visited:
            dfs_finish(node)

    transposed = transpose_graph(graph)
    visited.clear()
    components: list[list[str]] = []

    def dfs_collect(node: str, component: list[str]) -> None:
        visited.add(node)
        component.append(node)
        for neighbor in transposed.adjacency[node]:
            if neighbor not in visited:
                dfs_collect(neighbor, component)

    for node in reversed(finish_order):
        if node in visited:
            continue
        component: list[str] = []
        dfs_collect(node, component)
        components.append(sorted(component))

    return _sort_components(components)


def compare_algorithms(graph: DirectedGraph, repeat: int = 5) -> dict[str, object]:
    repeats = max(1, repeat)
    tarjan_components = tarjan_strongly_connected_components(graph)
    kosaraju_components = kosaraju_strongly_connected_components(graph)
    algorithms_match = tarjan_components == kosaraju_components

    tarjan_timings_ms: list[float] = []
    kosaraju_timings_ms: list[float] = []
    for _ in range(repeats):
        started = perf_counter()
        tarjan_strongly_connected_components(graph)
        tarjan_timings_ms.append((perf_counter() - started) * 1000)

        started = perf_counter()
        kosaraju_strongly_connected_components(graph)
        kosaraju_timings_ms.append((perf_counter() - started) * 1000)

    return {
        'node_count': len(graph.nodes),
        'edge_count': graph.edge_count,
        'repeat': repeats,
        'algorithms_match': algorithms_match,
        'component_count': len(tarjan_components),
        'components': tarjan_components,
        'timings_ms': {
            'tarjan': tarjan_timings_ms,
            'kosaraju': kosaraju_timings_ms,
        },
        'average_ms': {
            'tarjan': round(sum(tarjan_timings_ms) / repeats, 6),
            'kosaraju': round(sum(kosaraju_timings_ms) / repeats, 6),
        },
        'faster_algorithm': (
            'tie'
            if round(sum(tarjan_timings_ms), 12) == round(sum(kosaraju_timings_ms), 12)
            else ('tarjan' if sum(tarjan_timings_ms) < sum(kosaraju_timings_ms) else 'kosaraju')
        ),
    }


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


def _component_degree_summaries(component_count: int, dag_edges: list[tuple[int, int]]) -> tuple[dict[int, int], dict[int, int]]:
    incoming = {index: 0 for index in range(component_count)}
    outgoing = {index: 0 for index in range(component_count)}
    for src, dst in dag_edges:
        outgoing[src] += 1
        incoming[dst] += 1
    return incoming, outgoing



def _bottleneck_role(incoming_count: int, outgoing_count: int) -> str:
    if incoming_count == 0 and outgoing_count == 0:
        return 'isolated'
    if incoming_count == 0:
        return 'source'
    if outgoing_count == 0:
        return 'sink'
    return 'bridge'



def _component_payloads(
    summaries: list[dict[str, object]],
    levels: dict[int, int],
    incoming: dict[int, int],
    outgoing: dict[int, int],
    *,
    include_self_loop: bool = False,
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for index, summary in enumerate(summaries):
        component_payload: dict[str, object] = {
            'id': summary['id'],
            'nodes': summary['nodes'],
            'size': summary['size'],
            'topology_level': levels[index],
            'incoming_component_count': incoming[index],
            'outgoing_component_count': outgoing[index],
            'bottleneck_role': _bottleneck_role(incoming[index], outgoing[index]),
        }
        if include_self_loop:
            component_payload['self_loop'] = summary['self_loop']
        payloads.append(component_payload)
    return payloads



def _topology_groups(component_payloads: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[int, list[dict[str, object]]] = {}
    for component in component_payloads:
        level = int(component['topology_level'])
        groups.setdefault(level, []).append(dict(component))
    return [
        {
            'level': level,
            'component_count': len(groups[level]),
            'component_ids': [component['id'] for component in groups[level]],
            'components': groups[level],
        }
        for level in sorted(groups)
    ]



def condensation_dag(graph: DirectedGraph, components: list[list[str]]) -> dict[str, object]:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    incoming, outgoing = _component_degree_summaries(len(summaries), dag_edges)
    component_payloads = _component_payloads(summaries, levels, incoming, outgoing)
    return {
        'components': component_payloads,
        'topology_groups': _topology_groups(component_payloads),
        'edges': [
            {'from': f'C{src}', 'to': f'C{dst}'}
            for src, dst in dag_edges
        ],
        'edge_count': len(dag_edges),
        'level_count': (max(levels.values()) + 1) if levels else 0,
    }


def _component_level_groups(levels: dict[int, int], summaries: list[dict[str, object]]) -> dict[int, list[str]]:
    level_groups: dict[int, list[str]] = {}
    for index, summary in enumerate(summaries):
        level_groups.setdefault(levels[index], []).append(summary['id'])
    return level_groups


def _mermaid_escape(text: str) -> str:
    return text.replace('"', '&#34;')


def condensation_dot(graph: DirectedGraph, components: list[list[str]]) -> str:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    level_groups = _component_level_groups(levels, summaries)

    lines = [
        'digraph condensation {',
        '  rankdir=LR;',
        '  node [shape=box, style="rounded,filled", fillcolor="#EAF2FF", color="#4C78A8"];',
    ]
    for index, summary in enumerate(summaries):
        label = f"{summary['id']}\nlevel={levels[index]} | size={summary['size']}\n" + ", ".join(summary['nodes'])
        lines.append(f'  {summary["id"]} [label={json.dumps(label)}];')

    for level in sorted(level_groups):
        members = '; '.join(level_groups[level])
        lines.append(f'  {{ rank=same; // topology level {level}')
        lines.append(f'    {members};')
        lines.append('  }')

    for src, dst in dag_edges:
        lines.append(f'  C{src} -> C{dst};')

    lines.append('}')
    return "\n".join(lines)


def condensation_mermaid(graph: DirectedGraph, components: list[list[str]]) -> str:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    level_groups = _component_level_groups(levels, summaries)
    summary_by_id = {summary['id']: summary for summary in summaries}

    lines = [
        'flowchart LR',
        '  classDef component fill:#EAF2FF,stroke:#4C78A8,stroke-width:1px,color:#0F172A;',
    ]

    for level in sorted(level_groups):
        lines.append(f'  subgraph level_{level}["topology level {level}"]')
        lines.append('    direction TB')
        for component_id in level_groups[level]:
            summary = summary_by_id[component_id]
            label = f"{component_id}<br/>level={level} | size={summary['size']}<br/>" + ', '.join(summary['nodes'])
            lines.append(f'    {component_id}["{_mermaid_escape(label)}"]')
        lines.append('  end')

    for summary in summaries:
        lines.append(f'  class {summary["id"]} component;')

    for src, dst in dag_edges:
        lines.append(f'  C{src} --> C{dst}')

    return "\n".join(lines)


def summarize_components(graph: DirectedGraph, components: list[list[str]]) -> dict[str, object]:
    summaries, dag_edges = build_component_graph(graph, components)
    levels = compute_component_levels(len(summaries), dag_edges)
    incoming, outgoing = _component_degree_summaries(len(summaries), dag_edges)
    component_payloads = _component_payloads(summaries, levels, incoming, outgoing, include_self_loop=True)
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
        'components': component_payloads,
        'topology_groups': _topology_groups(component_payloads),
    }


def _display_graph_path(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.as_posix() if not candidate.is_absolute() else candidate.name


def _comparison_trial_rows(comparison: dict[str, object]) -> list[dict[str, object]]:
    tarjan_timings = [float(value) for value in comparison['timings_ms']['tarjan']]
    kosaraju_timings = [float(value) for value in comparison['timings_ms']['kosaraju']]
    rows: list[dict[str, object]] = []
    for trial, (tarjan_ms, kosaraju_ms) in enumerate(zip(tarjan_timings, kosaraju_timings), start=1):
        winner = (
            'tie'
            if round(tarjan_ms, 12) == round(kosaraju_ms, 12)
            else ('tarjan' if tarjan_ms < kosaraju_ms else 'kosaraju')
        )
        rows.append(
            {
                'trial': trial,
                'tarjan_ms': round(tarjan_ms, 6),
                'kosaraju_ms': round(kosaraju_ms, 6),
                'delta_ms': round(abs(tarjan_ms - kosaraju_ms), 6),
                'winner': winner,
                'algorithms_match': bool(comparison['algorithms_match']),
                'node_count': int(comparison['node_count']),
                'edge_count': int(comparison['edge_count']),
                'component_count': int(comparison['component_count']),
            }
        )
    return rows


def render_compare_csv(comparison: dict[str, object]) -> str:
    rows = _comparison_trial_rows(comparison)
    fieldnames = [
        'trial',
        'tarjan_ms',
        'kosaraju_ms',
        'delta_ms',
        'winner',
        'algorithms_match',
        'node_count',
        'edge_count',
        'component_count',
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _markdown_escape(value: object) -> str:
    return str(value).replace('|', r'\|').replace('\n', '<br/>')


def render_compare_markdown(graph_path: str | Path, comparison: dict[str, object]) -> str:
    trial_rows = _comparison_trial_rows(comparison)
    component_preview = [', '.join(component) for component in comparison['components']]
    lines = [
        '# Tarjan vs Kosaraju benchmark report',
        '',
        '## Graph summary',
        '| metric | value |',
        '| --- | --- |',
        f"| graph file | `{_markdown_escape(_display_graph_path(graph_path))}` |",
        f"| node count | {comparison['node_count']} |",
        f"| edge count | {comparison['edge_count']} |",
        f"| strongly connected components | {comparison['component_count']} |",
        f"| repeated timing runs | {comparison['repeat']} |",
        f"| algorithms match | {'yes' if comparison['algorithms_match'] else 'no'} |",
        f"| faster algorithm | {comparison['faster_algorithm']} |",
        '',
        '## Average timings (ms)',
        '| algorithm | average_ms |',
        '| --- | ---: |',
        f"| tarjan | {comparison['average_ms']['tarjan']:.6f} |",
        f"| kosaraju | {comparison['average_ms']['kosaraju']:.6f} |",
        '',
        '## Per-run timings (ms)',
        '| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |',
        '| --- | ---: | ---: | ---: | --- |',
    ]
    for row in trial_rows:
        lines.append(
            f"| {row['trial']} | {row['tarjan_ms']:.6f} | {row['kosaraju_ms']:.6f} | {row['delta_ms']:.6f} | {row['winner']} |"
        )
    lines.extend(['', '## Component roster'])
    for index, component in enumerate(component_preview):
        lines.append(f'- C{index}: {component}')
    lines.extend(
        [
            '',
            '## Interview talking points',
            f"- Both algorithms {'agree' if comparison['algorithms_match'] else 'do not agree'} on the deterministic SCC grouping used by this lab.",
            f"- Tarjan averaged {comparison['average_ms']['tarjan']:.6f} ms while Kosaraju averaged {comparison['average_ms']['kosaraju']:.6f} ms on this graph.",
            '- The CSV export keeps one row per timing run so you can chart trial-by-trial variance in a spreadsheet or static portfolio page.',
        ]
    )
    return "\n".join(lines) + "\n"


def maybe_write_text(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze strongly connected components with Tarjan and Kosaraju workflows.")
    parser.add_argument('graph_path', help='Path to a JSON adjacency list or {nodes, edges} graph file')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('scc', help='Print SCC summary as JSON')
    subparsers.add_parser('condensation', help='Print SCC condensation DAG as JSON')
    subparsers.add_parser('dot', help='Print the condensation DAG as Graphviz DOT')
    subparsers.add_parser('mermaid', help='Print the condensation DAG as Mermaid flowchart markup')
    compare = subparsers.add_parser('compare', help='Compare Tarjan and Kosaraju SCC results and timings')
    compare.add_argument('--repeat', type=int, default=5, help='Number of timing runs to average per algorithm')
    compare.add_argument('--csv-output', type=Path, help='Optional CSV export path for per-run timing rows')
    compare.add_argument('--markdown-output', type=Path, help='Optional Markdown report path for a portfolio-ready summary')
    explain = subparsers.add_parser('explain', help='Print a concise text explanation')
    explain.add_argument('--limit', type=int, default=5, help='Maximum number of components to describe')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    graph = load_graph(args.graph_path)

    if args.command == 'compare':
        comparison = compare_algorithms(graph, repeat=args.repeat)
        maybe_write_text(args.csv_output, render_compare_csv(comparison))
        maybe_write_text(args.markdown_output, render_compare_markdown(args.graph_path, comparison))
        print(json.dumps(comparison, indent=2))
        return 0

    components = tarjan_strongly_connected_components(graph)

    if args.command == 'scc':
        print(json.dumps(summarize_components(graph, components), indent=2))
        return 0
    if args.command == 'condensation':
        print(json.dumps(condensation_dag(graph, components), indent=2))
        return 0
    if args.command == 'dot':
        print(condensation_dot(graph, components))
        return 0
    if args.command == 'mermaid':
        print(condensation_mermaid(graph, components))
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
                f"C{index} (level {component_summary['topology_level']}, role {component_summary['bottleneck_role']}, in={component_summary['incoming_component_count']}, out={component_summary['outgoing_component_count']}): {', '.join(component_summary['nodes'])}"
            )
        print("\n".join(lines))
        return 0
    parser.error(f'unsupported command: {args.command}')
    return 2


if __name__ == '__main__':
    sys.exit(main())
