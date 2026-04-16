import json
import subprocess
import sys
from pathlib import Path

import pytest

from tarjan_scc_lab import (
    DirectedGraph,
    compare_algorithms,
    condensation_dag,
    condensation_dot,
    condensation_mermaid,
    kosaraju_strongly_connected_components,
    load_graph,
    main,
    summarize_components,
    tarjan_strongly_connected_components,
    transpose_graph,
)


FIXTURE_PATH = Path(__file__).with_name('sample_graph.json')


def test_tarjan_finds_multi_node_components_before_singletons():
    graph = load_graph(FIXTURE_PATH)
    components = tarjan_strongly_connected_components(graph)
    assert components[:3] == [['A', 'B', 'C'], ['D', 'E'], ['F', 'G']]
    assert components[3:] == [['H']]


def test_kosaraju_matches_tarjan_component_ordering():
    graph = load_graph(FIXTURE_PATH)
    assert kosaraju_strongly_connected_components(graph) == tarjan_strongly_connected_components(graph)


def test_transpose_graph_reverses_edges_and_keeps_singletons():
    graph = DirectedGraph({'A': ('B',), 'B': ('C',), 'C': (), 'D': ('D',)})
    transposed = transpose_graph(graph)
    assert transposed.adjacency == {
        'A': (),
        'B': ('A',),
        'C': ('B',),
        'D': ('D',),
    }


def test_load_graph_accepts_adjacency_object_and_adds_missing_leaf_nodes(tmp_path: Path):
    path = tmp_path / 'graph.json'
    path.write_text(json.dumps({'1': ['2'], '2': ['3']}))
    graph = load_graph(path)
    assert graph.adjacency == {'1': ('2',), '2': ('3',), '3': ()}


def test_load_graph_rejects_bad_edge_payload(tmp_path: Path):
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps({'nodes': ['A'], 'edges': [{'from': 'A'}]}))
    with pytest.raises(ValueError):
        load_graph(path)


def test_condensation_dag_collapses_internal_component_edges():
    graph = DirectedGraph({
        'A': ('B',),
        'B': ('A', 'C'),
        'C': ('D',),
        'D': ('C',),
    })
    components = tarjan_strongly_connected_components(graph)
    dag = condensation_dag(graph, components)
    assert dag['components'] == [
        {
            'id': 'C0',
            'nodes': ['A', 'B'],
            'size': 2,
            'topology_level': 0,
            'incoming_component_count': 0,
            'outgoing_component_count': 1,
            'bottleneck_role': 'source',
        },
        {
            'id': 'C1',
            'nodes': ['C', 'D'],
            'size': 2,
            'topology_level': 1,
            'incoming_component_count': 1,
            'outgoing_component_count': 0,
            'bottleneck_role': 'sink',
        },
    ]
    assert dag['edge_count'] == 1
    assert dag['level_count'] == 2
    assert dag['edges'] == [{'from': 'C0', 'to': 'C1'}]


def test_condensation_dag_assigns_levels_by_longest_source_path():
    graph = DirectedGraph({
        'A': ('B',),
        'B': ('A', 'C', 'E'),
        'C': ('D',),
        'D': ('C', 'F'),
        'E': ('F',),
        'F': (),
    })
    components = tarjan_strongly_connected_components(graph)
    dag = condensation_dag(graph, components)
    assert dag['components'] == [
        {
            'id': 'C0', 'nodes': ['A', 'B'], 'size': 2, 'topology_level': 0,
            'incoming_component_count': 0, 'outgoing_component_count': 2, 'bottleneck_role': 'source',
        },
        {
            'id': 'C1', 'nodes': ['C', 'D'], 'size': 2, 'topology_level': 1,
            'incoming_component_count': 1, 'outgoing_component_count': 1, 'bottleneck_role': 'bridge',
        },
        {
            'id': 'C2', 'nodes': ['E'], 'size': 1, 'topology_level': 1,
            'incoming_component_count': 1, 'outgoing_component_count': 1, 'bottleneck_role': 'bridge',
        },
        {
            'id': 'C3', 'nodes': ['F'], 'size': 1, 'topology_level': 2,
            'incoming_component_count': 2, 'outgoing_component_count': 0, 'bottleneck_role': 'sink',
        },
    ]
    assert dag['level_count'] == 3


def test_compare_algorithms_reports_matching_components_and_average_timings():
    graph = load_graph(FIXTURE_PATH)
    comparison = compare_algorithms(graph, repeat=2)
    assert comparison['algorithms_match'] is True
    assert comparison['component_count'] == 4
    assert comparison['components'][0] == ['A', 'B', 'C']
    assert comparison['repeat'] == 2
    assert len(comparison['timings_ms']['tarjan']) == 2
    assert len(comparison['timings_ms']['kosaraju']) == 2
    assert comparison['average_ms']['tarjan'] >= 0
    assert comparison['average_ms']['kosaraju'] >= 0
    assert comparison['faster_algorithm'] in {'tarjan', 'kosaraju', 'tie'}


def test_condensation_mermaid_groups_components_by_topology_level():
    graph = DirectedGraph({
        'A': ('B',),
        'B': ('A', 'C', 'E'),
        'C': ('D',),
        'D': ('C', 'F'),
        'E': ('F',),
        'F': (),
    })
    components = tarjan_strongly_connected_components(graph)
    mermaid = condensation_mermaid(graph, components)
    assert 'flowchart LR' in mermaid
    assert 'subgraph level_1["topology level 1"]' in mermaid
    assert 'C0["C0<br/>level=0 | size=2<br/>A, B"]' in mermaid
    assert 'C1 --> C3' in mermaid
    assert 'class C2 component;' in mermaid


def test_condensation_mermaid_escapes_double_quotes_in_node_labels():
    graph = DirectedGraph({'A"1': ('B',), 'B': ('A"1',)})
    components = tarjan_strongly_connected_components(graph)
    mermaid = condensation_mermaid(graph, components)
    assert '&#34;' in mermaid
    assert 'A"1' not in mermaid


def test_condensation_dot_groups_components_by_topology_level():
    graph = DirectedGraph({
        'A': ('B',),
        'B': ('A', 'C', 'E'),
        'C': ('D',),
        'D': ('C', 'F'),
        'E': ('F',),
        'F': (),
    })
    components = tarjan_strongly_connected_components(graph)
    dot = condensation_dot(graph, components)
    assert 'digraph condensation {' in dot
    assert 'C0 [label="C0\\nlevel=0 | size=2\\nA, B"]' in dot
    assert '{ rank=same; // topology level 1' in dot
    assert 'C1; C2;' in dot
    assert 'C1 -> C3;' in dot


def test_summary_marks_acyclic_graph_when_all_components_are_singletons():
    graph = DirectedGraph({'A': ('B',), 'B': ('C',), 'C': ()})
    summary = summarize_components(graph, tarjan_strongly_connected_components(graph))
    assert summary['acyclic'] is True
    assert summary['largest_component_size'] == 1
    assert summary['source_component_count'] == 1
    assert summary['sink_component_count'] == 1


def test_summary_treats_singleton_self_loop_as_cyclic():
    graph = DirectedGraph({'A': ('A',)})
    summary = summarize_components(graph, tarjan_strongly_connected_components(graph))
    assert summary['acyclic'] is False
    assert summary['cyclic_component_count'] == 1
    assert summary['condensation_level_count'] == 1
    assert summary['components'][0]['self_loop'] is True
    assert summary['components'][0]['topology_level'] == 0
    assert summary['components'][0]['bottleneck_role'] == 'isolated'


def test_summary_reports_component_bottleneck_roles_and_degrees():
    graph = DirectedGraph({
        'A': ('B',),
        'B': ('A', 'C', 'E'),
        'C': ('D',),
        'D': ('C', 'F'),
        'E': ('F',),
        'F': (),
    })
    summary = summarize_components(graph, tarjan_strongly_connected_components(graph))
    assert summary['source_component_count'] == 1
    assert summary['sink_component_count'] == 1
    assert summary['components'][0]['bottleneck_role'] == 'source'
    assert summary['components'][0]['outgoing_component_count'] == 2
    assert summary['components'][1]['bottleneck_role'] == 'bridge'
    assert summary['components'][3]['bottleneck_role'] == 'sink'
    assert summary['components'][3]['incoming_component_count'] == 2


def test_cli_scc_outputs_json_summary():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name('tarjan_scc_lab.py')), str(FIXTURE_PATH), 'scc'],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['component_count'] == 4
    assert payload['components'][0]['nodes'] == ['A', 'B', 'C']


def test_cli_condensation_outputs_component_graph():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name('tarjan_scc_lab.py')), str(FIXTURE_PATH), 'condensation'],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['edges'] == [
        {'from': 'C0', 'to': 'C1'},
        {'from': 'C1', 'to': 'C2'},
        {'from': 'C2', 'to': 'C3'},
    ]


def test_cli_compare_outputs_matching_algorithms_and_timings():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name('tarjan_scc_lab.py')), str(FIXTURE_PATH), 'compare', '--repeat', '2'],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['algorithms_match'] is True
    assert payload['repeat'] == 2
    assert len(payload['timings_ms']['tarjan']) == 2
    assert len(payload['timings_ms']['kosaraju']) == 2


def test_cli_dot_outputs_graphviz_condensation_graph():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name('tarjan_scc_lab.py')), str(FIXTURE_PATH), 'dot'],
        check=True,
        capture_output=True,
        text=True,
    )
    assert 'digraph condensation {' in result.stdout
    assert 'C0 [label="C0\\nlevel=0 | size=3\\nA, B, C"]' in result.stdout
    assert 'C0 -> C1;' in result.stdout


def test_cli_explain_reports_requested_component_limit(capsys):
    exit_code = main([str(FIXTURE_PATH), 'explain', '--limit', '2'])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '4 strongly connected components' in captured.out
    assert 'Condensation DAG spans 4 topological level(s).' in captured.out
    assert 'C0 (level 0, role source, in=0, out=1): A, B, C' in captured.out
    assert 'C1 (level 1, role bridge, in=1, out=1): D, E' in captured.out
    assert 'C2:' not in captured.out
