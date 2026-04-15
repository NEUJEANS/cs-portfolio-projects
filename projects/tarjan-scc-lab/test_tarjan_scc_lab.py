import json
import subprocess
import sys
from pathlib import Path

import pytest

from tarjan_scc_lab import DirectedGraph, condensation_dag, condensation_dot, load_graph, main, summarize_components, tarjan_strongly_connected_components


FIXTURE_PATH = Path(__file__).with_name('sample_graph.json')


def test_tarjan_finds_multi_node_components_before_singletons():
    graph = load_graph(FIXTURE_PATH)
    components = tarjan_strongly_connected_components(graph)
    assert components[:3] == [['A', 'B', 'C'], ['D', 'E'], ['F', 'G']]
    assert components[3:] == [['H']]


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
        {'id': 'C0', 'nodes': ['A', 'B'], 'size': 2, 'topology_level': 0},
        {'id': 'C1', 'nodes': ['C', 'D'], 'size': 2, 'topology_level': 1},
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
        {'id': 'C0', 'nodes': ['A', 'B'], 'size': 2, 'topology_level': 0},
        {'id': 'C1', 'nodes': ['C', 'D'], 'size': 2, 'topology_level': 1},
        {'id': 'C2', 'nodes': ['E'], 'size': 1, 'topology_level': 1},
        {'id': 'C3', 'nodes': ['F'], 'size': 1, 'topology_level': 2},
    ]
    assert dag['level_count'] == 3


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
    assert 'C0 (level 0): A, B, C' in captured.out
    assert 'C1 (level 1): D, E' in captured.out
    assert 'C2:' not in captured.out
