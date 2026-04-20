import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from html import escape
from io import StringIO
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


def _html_escape(value: object) -> str:
    return escape(str(value), quote=True)


def relative_href(target: str | Path, html_output: str | Path) -> str:
    return Path(os.path.relpath(Path(target), start=Path(html_output).parent)).as_posix()


def _friendly_faster_algorithm(value: str) -> str:
    if value == 'tie':
        return 'Tie'
    return value.title()


def _trial_winner_heading(value: str) -> str:
    if value == 'tie':
        return 'Tie on timing'
    return f'{value.title()} wins'


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
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
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


def render_compare_html(
    graph_path: str | Path,
    comparison: dict[str, object],
    *,
    html_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    csv_output_path: str | Path | None = None,
    markdown_output_path: str | Path | None = None,
    png_output_path: str | Path | None = None,
) -> str:
    trial_rows = _comparison_trial_rows(comparison)
    component_cards = []
    largest_component_size = max((len(component) for component in comparison['components']), default=0)
    max_trial_ms = max(
        [row['tarjan_ms'] for row in trial_rows] + [row['kosaraju_ms'] for row in trial_rows],
        default=0.0,
    ) or 1.0

    summary_cards = [
        (
            'Graph footprint',
            f"{comparison['node_count']} nodes · {comparison['edge_count']} edges",
            'Quick sizing context for the SCC benchmark input.',
        ),
        (
            'Strongly connected components',
            str(comparison['component_count']),
            f'Largest SCC size is {largest_component_size}.',
        ),
        (
            'Repeated timings',
            str(comparison['repeat']),
            'Each trial reruns both linear-time SCC algorithms on the same graph.',
        ),
        (
            'Agreement',
            'Yes' if comparison['algorithms_match'] else 'No',
            'Checks whether Tarjan and Kosaraju produced the same deterministic SCC grouping.',
        ),
        (
            'Average winner',
            _friendly_faster_algorithm(str(comparison['faster_algorithm'])),
            'Average timing leader across all recorded trials.',
        ),
    ]
    summary_cards_html = ''.join(
        f'''<article class="summary-card">
      <p class="eyebrow">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description in summary_cards
    )

    average_rows_html = ''.join(
        f'''<tr>
        <th scope="row">{_html_escape(algorithm)}</th>
        <td>{average_ms:.6f}</td>
      </tr>'''
        for algorithm, average_ms in (
            ('Tarjan', float(comparison['average_ms']['tarjan'])),
            ('Kosaraju', float(comparison['average_ms']['kosaraju'])),
        )
    )

    trial_cards_html = []
    for row in trial_rows:
        tarjan_width = min(100.0, (float(row['tarjan_ms']) / max_trial_ms) * 100)
        kosaraju_width = min(100.0, (float(row['kosaraju_ms']) / max_trial_ms) * 100)
        trial_cards_html.append(
            f'''<article class="trial-card">
      <div class="trial-card__header">
        <div>
          <p class="eyebrow">Trial {row['trial']}</p>
          <h3>{_html_escape(_trial_winner_heading(str(row['winner'])))}</h3>
        </div>
        <span class="pill">Δ {float(row['delta_ms']):.6f} ms</span>
      </div>
      <div class="bar-row">
        <div class="bar-row__label"><span>Tarjan</span><code>{float(row['tarjan_ms']):.6f} ms</code></div>
        <div class="bar-track"><span class="bar bar--tarjan" style="width: {tarjan_width:.2f}%"></span></div>
      </div>
      <div class="bar-row">
        <div class="bar-row__label"><span>Kosaraju</span><code>{float(row['kosaraju_ms']):.6f} ms</code></div>
        <div class="bar-track"><span class="bar bar--kosaraju" style="width: {kosaraju_width:.2f}%"></span></div>
      </div>
    </article>'''
        )

    for index, component in enumerate(comparison['components']):
        component_cards.append(
            f'''<article class="component-card">
      <div class="component-card__header">
        <h3>C{index}</h3>
        <span class="pill">size {len(component)}</span>
      </div>
      <p>{_html_escape(', '.join(component))}</p>
    </article>'''
        )

    artifact_links = []
    if html_output_path is not None:
        for label, target in (
            ('JSON payload', json_output_path),
            ('CSV timings', csv_output_path),
            ('Markdown report', markdown_output_path),
            ('PNG snapshot', png_output_path),
        ):
            if target is None:
                continue
            artifact_links.append(
                f'<li><a href="{_html_escape(relative_href(target, html_output_path))}">{_html_escape(label)}</a></li>'
            )
    artifact_links_html = ''.join(artifact_links) or '<li>No sibling artifact links were supplied for this HTML export.</li>'

    graph_label = _display_graph_path(graph_path)
    average_winner = _friendly_faster_algorithm(str(comparison['faster_algorithm']))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tarjan vs Kosaraju benchmark dashboard</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2, h3 {{ line-height: 1.15; }}
    p, li, td, th {{ line-height: 1.55; }}
    code {{ font-family: "SFMono-Regular", ui-monospace, monospace; }}
    a {{ color: #1d4ed8; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.4rem; padding: 1.4rem; background: linear-gradient(135deg, rgba(224, 231, 255, 0.96), rgba(240, 253, 250, 0.96)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 74ch; }}
    .eyebrow {{ margin: 0; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #4338ca; }}
    .hero-meta, .artifact-links {{ display: flex; flex-wrap: wrap; gap: 0.65rem; }}
    .hero-meta {{ margin-top: 1rem; }}
    .chip, .pill {{ display: inline-flex; align-items: center; padding: 0.4rem 0.75rem; border-radius: 999px; font-size: 0.92rem; }}
    .chip {{ background: rgba(224, 231, 255, 0.85); border: 1px solid rgba(129, 140, 248, 0.28); color: #3730a3; }}
    .pill {{ background: rgba(219, 234, 254, 0.95); color: #1d4ed8; font-weight: 700; }}
    .summary-grid, .trial-grid, .component-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1.4rem; }}
    .summary-card, .trial-card, .component-card, .table-card {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.2rem; background: rgba(255, 255, 255, 0.92); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .summary-card, .trial-card, .component-card, .table-card {{ padding: 1rem; }}
    .summary-card strong {{ display: block; margin-top: 0.3rem; font-size: 1.18rem; }}
    .section-title {{ margin: 1.8rem 0 0.8rem; }}
    .table-card table {{ width: 100%; border-collapse: collapse; }}
    .table-card th, .table-card td {{ padding: 0.65rem 0.2rem; border-bottom: 1px solid rgba(148, 163, 184, 0.24); text-align: left; }}
    .table-card tr:last-child th, .table-card tr:last-child td {{ border-bottom: none; }}
    .trial-card__header, .component-card__header {{ display: flex; gap: 0.75rem; align-items: start; justify-content: space-between; }}
    .trial-card__header h3, .component-card__header h3 {{ margin: 0.15rem 0 0; }}
    .bar-row + .bar-row {{ margin-top: 0.8rem; }}
    .bar-row__label {{ display: flex; justify-content: space-between; gap: 0.75rem; font-size: 0.92rem; margin-bottom: 0.3rem; }}
    .bar-track {{ background: rgba(226, 232, 240, 0.95); border-radius: 999px; overflow: hidden; height: 0.85rem; }}
    .bar {{ display: block; height: 100%; border-radius: 999px; }}
    .bar--tarjan {{ background: linear-gradient(90deg, #2563eb, #38bdf8); }}
    .bar--kosaraju {{ background: linear-gradient(90deg, #7c3aed, #c084fc); }}
    .artifact-card ul {{ margin: 0.8rem 0 0; padding-left: 1.15rem; }}
    @media (max-width: 760px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Tarjan SCC lab</p>
      <h1>Tarjan vs. Kosaraju benchmark dashboard</h1>
      <p>Static HTML artifact for portfolio screenshots and GitHub Pages demos. It reuses the same benchmark payload that powers the JSON, CSV, and Markdown exports, then turns the SCC comparison into summary cards, trial-level timing bars, and a quick component gallery.</p>
      <div class="hero-meta">
        <span class="chip">Graph {_html_escape(graph_label)}</span>
        <span class="chip">Algorithms match {'yes' if comparison['algorithms_match'] else 'no'}</span>
        <span class="chip">Average winner {_html_escape(average_winner)}</span>
        <span class="chip">Trials {_html_escape(comparison['repeat'])}</span>
      </div>
    </section>
    <section class="summary-grid">
{summary_cards_html}
    </section>
    <h2 class="section-title">Average timings</h2>
    <section class="summary-grid">
      <article class="table-card">
        <table>
          <thead>
            <tr><th>Algorithm</th><th>Average time (ms)</th></tr>
          </thead>
          <tbody>
{average_rows_html}
          </tbody>
        </table>
      </article>
      <article class="table-card artifact-card">
        <p class="eyebrow">Artifact bundle</p>
        <h3>Linked companions</h3>
        <p>Use the sibling exports for spreadsheet charts, Markdown embeds, or raw machine-readable analysis.</p>
        <ul>
          {artifact_links_html}
        </ul>
      </article>
    </section>
    <h2 class="section-title">Per-trial timing gallery</h2>
    <section class="trial-grid">
{''.join(trial_cards_html)}
    </section>
    <h2 class="section-title">Component roster</h2>
    <section class="component-grid">
{''.join(component_cards)}
    </section>
  </main>
</body>
</html>
'''


def maybe_write_text(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def resolve_chrome_binary(preferred: str | Path | None = None) -> str:
    candidates: list[str] = []
    if preferred is not None:
        candidates.append(str(preferred))
    candidates.extend(['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'])
    for candidate in candidates:
        candidate_path = Path(candidate).expanduser()
        if candidate_path.is_absolute() and candidate_path.exists():
            return str(candidate_path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        'Could not find a Chrome/Chromium binary for PNG capture. Pass --chrome-binary or install google-chrome/chromium.'
    )


def default_compare_png_height(comparison: dict[str, object], width: int) -> int:
    normalized_width = max(720, width)
    trial_count = int(comparison['repeat'])
    component_count = int(comparison['component_count'])
    if normalized_width >= 1280:
        trial_columns = 3
        component_columns = 4
    elif normalized_width >= 900:
        trial_columns = 2
        component_columns = 3
    else:
        trial_columns = 1
        component_columns = 1
    trial_rows = max(1, (trial_count + trial_columns - 1) // trial_columns)
    component_rows = max(1, (component_count + component_columns - 1) // component_columns)
    estimated_height = 840 + (trial_rows * 320) + (component_rows * 180)
    return max(1100, min(estimated_height, 2600))


def build_compare_png_command(
    html_output_path: str | Path,
    png_output_path: str | Path,
    *,
    width: int,
    height: int,
    capture_ms: int,
    chrome_binary: str | Path | None = None,
) -> list[str]:
    resolved_html = Path(html_output_path).resolve()
    resolved_png = Path(png_output_path).resolve()
    return [
        resolve_chrome_binary(chrome_binary),
        '--headless',
        '--disable-gpu',
        '--hide-scrollbars',
        f'--window-size={width},{height}',
        f'--virtual-time-budget={capture_ms}',
        f'--screenshot={resolved_png}',
        resolved_html.as_uri(),
    ]


def render_compare_png(
    html_output_path: str | Path,
    png_output_path: str | Path,
    comparison: dict[str, object],
    *,
    width: int = 1440,
    height: int | None = None,
    capture_ms: int = 1500,
    chrome_binary: str | Path | None = None,
) -> Path:
    html_path = Path(html_output_path)
    if not html_path.exists():
        raise RuntimeError(f'HTML dashboard not found for PNG capture: {html_path}')
    png_path = Path(png_output_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    effective_width = max(720, width)
    effective_height = height if height is not None else default_compare_png_height(comparison, effective_width)
    command = build_compare_png_command(
        html_path,
        png_path,
        width=effective_width,
        height=max(900, effective_height),
        capture_ms=max(0, capture_ms),
        chrome_binary=chrome_binary,
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or 'unknown Chrome headless error'
        raise RuntimeError(f'PNG capture failed: {detail}')
    if not png_path.exists():
        raise RuntimeError(f'PNG capture did not create the expected output file: {png_path}')
    return png_path


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
    compare.add_argument('--json-output', type=Path, help='Optional JSON artifact path for the compare payload')
    compare.add_argument('--csv-output', type=Path, help='Optional CSV export path for per-run timing rows')
    compare.add_argument('--markdown-output', type=Path, help='Optional Markdown report path for a portfolio-ready summary')
    compare.add_argument('--html-output', type=Path, help='Optional HTML dashboard path for a portfolio-ready benchmark card/gallery')
    compare.add_argument('--png-output', type=Path, help='Optional PNG screenshot path captured from the HTML dashboard for slide decks or chat uploads')
    compare.add_argument('--png-width', type=int, default=1440, help='Viewport width in pixels for PNG capture (default: 1440)')
    compare.add_argument('--png-height', type=int, help='Optional viewport height override for PNG capture; defaults to an auto-sized dashboard height')
    compare.add_argument('--png-capture-ms', type=int, default=1500, help='Virtual time budget in milliseconds before capturing the PNG screenshot')
    compare.add_argument('--chrome-binary', type=Path, help='Optional Chrome/Chromium binary for PNG capture')
    explain = subparsers.add_parser('explain', help='Print a concise text explanation')
    explain.add_argument('--limit', type=int, default=5, help='Maximum number of components to describe')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    graph = load_graph(args.graph_path)

    if args.command == 'compare':
        if args.png_output is not None and args.html_output is None:
            parser.error('--png-output requires --html-output because the PNG is captured from the generated HTML dashboard')
        comparison = compare_algorithms(graph, repeat=args.repeat)
        json_text = json.dumps(comparison, indent=2)
        maybe_write_text(args.json_output, json_text + '\n')
        maybe_write_text(args.csv_output, render_compare_csv(comparison))
        maybe_write_text(args.markdown_output, render_compare_markdown(args.graph_path, comparison))
        if args.html_output is not None:
            maybe_write_text(
                args.html_output,
                render_compare_html(
                    args.graph_path,
                    comparison,
                    html_output_path=args.html_output,
                    json_output_path=args.json_output,
                    csv_output_path=args.csv_output,
                    markdown_output_path=args.markdown_output,
                    png_output_path=args.png_output,
                ),
            )
        if args.png_output is not None:
            render_compare_png(
                args.html_output,
                args.png_output,
                comparison,
                width=args.png_width,
                height=args.png_height,
                capture_ms=args.png_capture_ms,
                chrome_binary=args.chrome_binary,
            )
        compare_payload = dict(comparison)
        for field_name in ('json_output', 'csv_output', 'markdown_output', 'html_output', 'png_output'):
            field_value = getattr(args, field_name)
            if field_value is not None:
                compare_payload[field_name] = str(field_value)
        return_png_height = args.png_height
        if args.png_output is not None and return_png_height is None:
            return_png_height = default_compare_png_height(comparison, args.png_width)
        if args.png_output is not None:
            compare_payload['png_width'] = max(720, args.png_width)
            compare_payload['png_height'] = max(900, return_png_height)
        print(json.dumps(compare_payload, indent=2))
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
