import csv
import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

import tarjan_scc_lab
from tarjan_scc_lab import (
    DirectedGraph,
    build_compare_png_command,
    compare_algorithms,
    condensation_dag,
    condensation_dot,
    condensation_mermaid,
    default_compare_png_height,
    kosaraju_strongly_connected_components,
    load_graph,
    main,
    render_compare_csv,
    render_compare_html,
    render_compare_markdown,
    render_compare_png,
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
    assert dag['topology_groups'] == [
        {
            'level': 0,
            'component_count': 1,
            'component_ids': ['C0'],
            'components': [
                {
                    'id': 'C0',
                    'nodes': ['A', 'B'],
                    'size': 2,
                    'topology_level': 0,
                    'incoming_component_count': 0,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'source',
                }
            ],
        },
        {
            'level': 1,
            'component_count': 1,
            'component_ids': ['C1'],
            'components': [
                {
                    'id': 'C1',
                    'nodes': ['C', 'D'],
                    'size': 2,
                    'topology_level': 1,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 0,
                    'bottleneck_role': 'sink',
                }
            ],
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
    assert dag['topology_groups'] == [
        {
            'level': 0,
            'component_count': 1,
            'component_ids': ['C0'],
            'components': [
                {
                    'id': 'C0', 'nodes': ['A', 'B'], 'size': 2, 'topology_level': 0,
                    'incoming_component_count': 0, 'outgoing_component_count': 2, 'bottleneck_role': 'source',
                }
            ],
        },
        {
            'level': 1,
            'component_count': 2,
            'component_ids': ['C1', 'C2'],
            'components': [
                {
                    'id': 'C1', 'nodes': ['C', 'D'], 'size': 2, 'topology_level': 1,
                    'incoming_component_count': 1, 'outgoing_component_count': 1, 'bottleneck_role': 'bridge',
                },
                {
                    'id': 'C2', 'nodes': ['E'], 'size': 1, 'topology_level': 1,
                    'incoming_component_count': 1, 'outgoing_component_count': 1, 'bottleneck_role': 'bridge',
                },
            ],
        },
        {
            'level': 2,
            'component_count': 1,
            'component_ids': ['C3'],
            'components': [
                {
                    'id': 'C3', 'nodes': ['F'], 'size': 1, 'topology_level': 2,
                    'incoming_component_count': 2, 'outgoing_component_count': 0, 'bottleneck_role': 'sink',
                }
            ],
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


def test_render_compare_csv_outputs_one_row_per_timing_run():
    graph = load_graph(FIXTURE_PATH)
    comparison = compare_algorithms(graph, repeat=3)
    rows = list(csv.DictReader(render_compare_csv(comparison).splitlines()))
    assert len(rows) == 3
    assert rows[0]['trial'] == '1'
    assert rows[0]['algorithms_match'] == 'True'
    assert rows[0]['node_count'] == '8'
    assert rows[0]['component_count'] == '4'
    assert rows[0]['winner'] in {'tarjan', 'kosaraju', 'tie'}


def test_render_compare_markdown_includes_tables_and_component_roster():
    graph = load_graph(FIXTURE_PATH)
    comparison = compare_algorithms(graph, repeat=2)
    report = render_compare_markdown(FIXTURE_PATH, comparison)
    assert '# Tarjan vs Kosaraju benchmark report' in report
    assert '| metric | value |' in report
    assert '`sample_graph.json`' in report
    assert '## Per-run timings (ms)' in report
    assert '| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |' in report
    assert '- C0: A, B, C' in report
    assert '## Interview talking points' in report


def test_render_compare_html_includes_trial_gallery_component_cards_and_relative_links(tmp_path: Path):
    graph = load_graph(FIXTURE_PATH)
    comparison = compare_algorithms(graph, repeat=2)
    html_output = tmp_path / 'site' / 'reports' / 'benchmark.html'
    json_output = tmp_path / 'artifacts' / 'benchmark.json'
    csv_output = tmp_path / 'artifacts' / 'benchmark.csv'
    markdown_output = tmp_path / 'artifacts' / 'benchmark.md'
    png_output = tmp_path / 'artifacts' / 'benchmark.png'
    html = render_compare_html(
        FIXTURE_PATH,
        comparison,
        html_output_path=html_output,
        json_output_path=json_output,
        csv_output_path=csv_output,
        markdown_output_path=markdown_output,
        png_output_path=png_output,
    )
    assert '<h1>Tarjan vs. Kosaraju benchmark dashboard</h1>' in html
    assert 'Per-trial timing gallery' in html
    assert 'Component roster' in html
    assert 'Trial 1' in html
    assert 'href="../../artifacts/benchmark.json"' in html
    assert 'href="../../artifacts/benchmark.csv"' in html
    assert 'href="../../artifacts/benchmark.md"' in html
    assert 'href="../../artifacts/benchmark.png"' in html
    assert 'PNG snapshot' in html
    assert 'C0' in html
    assert 'A, B, C' in html


def test_default_compare_png_height_grows_with_more_dashboard_cards():
    graph = load_graph(FIXTURE_PATH)
    compact = compare_algorithms(graph, repeat=2)
    dense = compare_algorithms(graph, repeat=7)
    dense['components'] = dense['components'] + [['I'], ['J'], ['K'], ['L'], ['M']]
    dense['component_count'] = len(dense['components'])
    compact_height = default_compare_png_height(compact, 1440)
    dense_height = default_compare_png_height(dense, 1440)
    assert compact_height >= 1100
    assert dense_height > compact_height


def test_build_compare_png_command_uses_headless_chrome_and_file_uri(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(tarjan_scc_lab, 'resolve_chrome_binary', lambda preferred=None: '/usr/bin/google-chrome')
    html_path = tmp_path / 'benchmark.html'
    png_path = tmp_path / 'benchmark.png'
    command = build_compare_png_command(
        html_path,
        png_path,
        width=1600,
        height=1700,
        capture_ms=2200,
    )
    assert command[0] == '/usr/bin/google-chrome'
    assert '--headless' in command
    assert '--window-size=1600,1700' in command
    assert '--virtual-time-budget=2200' in command
    assert f'--screenshot={png_path.resolve()}' in command
    assert command[-1] == html_path.resolve().as_uri()


def test_render_compare_png_invokes_chrome_and_returns_output_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    graph = load_graph(FIXTURE_PATH)
    comparison = compare_algorithms(graph, repeat=2)
    html_path = tmp_path / 'benchmark.html'
    html_path.write_text('<!doctype html><title>benchmark</title>', encoding='utf-8')
    png_path = tmp_path / 'captures' / 'benchmark.png'

    def fake_run(command: list[str], capture_output: bool, text: bool, check: bool):
        assert '--headless' in command
        assert f'--screenshot={png_path.resolve()}' in command
        png_path.parent.mkdir(parents=True, exist_ok=True)
        png_path.write_bytes(b'fake-png')
        return SimpleNamespace(returncode=0, stderr='', stdout='')

    monkeypatch.setattr(tarjan_scc_lab, 'resolve_chrome_binary', lambda preferred=None: '/usr/bin/google-chrome')
    monkeypatch.setattr(tarjan_scc_lab.subprocess, 'run', fake_run)
    output_path = render_compare_png(html_path, png_path, comparison, width=1500, capture_ms=900)
    assert output_path == png_path
    assert png_path.read_bytes() == b'fake-png'


def test_cli_compare_requires_html_output_when_png_is_requested(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(FIXTURE_PATH), 'compare', '--png-output', 'benchmark.png'])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert '--png-output requires --html-output' in captured.err


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
    assert summary['topology_groups'] == [
        {
            'level': 0,
            'component_count': 1,
            'component_ids': ['C0'],
            'components': [
                {
                    'id': 'C0',
                    'size': 2,
                    'nodes': ['A', 'B'],
                    'self_loop': False,
                    'topology_level': 0,
                    'incoming_component_count': 0,
                    'outgoing_component_count': 2,
                    'bottleneck_role': 'source',
                }
            ],
        },
        {
            'level': 1,
            'component_count': 2,
            'component_ids': ['C1', 'C2'],
            'components': [
                {
                    'id': 'C1',
                    'size': 2,
                    'nodes': ['C', 'D'],
                    'self_loop': False,
                    'topology_level': 1,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'bridge',
                },
                {
                    'id': 'C2',
                    'size': 1,
                    'nodes': ['E'],
                    'self_loop': False,
                    'topology_level': 1,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'bridge',
                },
            ],
        },
        {
            'level': 2,
            'component_count': 1,
            'component_ids': ['C3'],
            'components': [
                {
                    'id': 'C3',
                    'size': 1,
                    'nodes': ['F'],
                    'self_loop': False,
                    'topology_level': 2,
                    'incoming_component_count': 2,
                    'outgoing_component_count': 0,
                    'bottleneck_role': 'sink',
                }
            ],
        },
    ]


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
    assert payload['topology_groups'][0]['level'] == 0
    assert payload['topology_groups'][0]['component_ids'] == ['C0']
    assert payload['topology_groups'][0]['components'][0]['id'] == 'C0'


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
    assert payload['topology_groups'] == [
        {
            'level': 0,
            'component_count': 1,
            'component_ids': ['C0'],
            'components': [
                {
                    'id': 'C0',
                    'nodes': ['A', 'B', 'C'],
                    'size': 3,
                    'topology_level': 0,
                    'incoming_component_count': 0,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'source',
                }
            ],
        },
        {
            'level': 1,
            'component_count': 1,
            'component_ids': ['C1'],
            'components': [
                {
                    'id': 'C1',
                    'nodes': ['D', 'E'],
                    'size': 2,
                    'topology_level': 1,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'bridge',
                }
            ],
        },
        {
            'level': 2,
            'component_count': 1,
            'component_ids': ['C2'],
            'components': [
                {
                    'id': 'C2',
                    'nodes': ['F', 'G'],
                    'size': 2,
                    'topology_level': 2,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 1,
                    'bottleneck_role': 'bridge',
                }
            ],
        },
        {
            'level': 3,
            'component_count': 1,
            'component_ids': ['C3'],
            'components': [
                {
                    'id': 'C3',
                    'nodes': ['H'],
                    'size': 1,
                    'topology_level': 3,
                    'incoming_component_count': 1,
                    'outgoing_component_count': 0,
                    'bottleneck_role': 'sink',
                }
            ],
        },
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


def test_cli_compare_can_write_json_csv_markdown_and_html_artifacts(tmp_path: Path):
    json_path = tmp_path / 'benchmark.json'
    csv_path = tmp_path / 'benchmark.csv'
    markdown_path = tmp_path / 'benchmark.md'
    html_path = tmp_path / 'benchmark.html'
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name('tarjan_scc_lab.py')),
            str(FIXTURE_PATH),
            'compare',
            '--repeat',
            '2',
            '--json-output',
            str(json_path),
            '--csv-output',
            str(csv_path),
            '--markdown-output',
            str(markdown_path),
            '--html-output',
            str(html_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['repeat'] == 2
    assert payload['json_output'] == str(json_path)
    assert payload['html_output'] == str(html_path)
    assert json_path.exists()
    assert csv_path.exists()
    assert markdown_path.exists()
    assert html_path.exists()
    json_payload = json.loads(json_path.read_text())
    assert json_payload['repeat'] == 2
    csv_rows = list(csv.DictReader(csv_path.read_text().splitlines()))
    assert len(csv_rows) == 2
    assert csv_rows[0]['trial'] == '1'
    markdown_text = markdown_path.read_text()
    assert '# Tarjan vs Kosaraju benchmark report' in markdown_text
    assert '## Component roster' in markdown_text
    html_text = html_path.read_text()
    assert 'Tarjan vs. Kosaraju benchmark dashboard' in html_text
    assert 'href="benchmark.json"' in html_text
    assert 'href="benchmark.csv"' in html_text
    assert 'href="benchmark.md"' in html_text


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
