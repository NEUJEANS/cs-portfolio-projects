import csv
import subprocess
import sys
from pathlib import Path

import pytest

from suffix_tree_lab import SuffixTree, benchmark_results_to_csv, parse_patterns


def test_contains_and_find_for_repeated_patterns():
    tree = SuffixTree("banana")
    assert tree.contains("ana") is True
    assert tree.find("ana") == [1, 3]
    assert tree.count("na") == 2
    assert tree.find("banana") == [0]
    assert tree.find("apple") == []


def test_longest_repeated_substring_and_min_occurrences():
    tree = SuffixTree("mississippi")
    assert tree.longest_repeated_substring() == "issi"
    assert tree.longest_repeated_substring(min_occurrences=3) == "i"


def test_edge_labels_are_compact_and_search_trace_explains_progress():
    tree = SuffixTree("banana")
    labels = tree.edge_labels()
    assert any(label.startswith("banana$") for label in labels)
    steps = tree.explain_find("ana")
    assert any("follow edge" in step for step in steps)
    assert steps[-1].startswith("matched 'ana'")


def test_dot_export_is_graphviz_friendly_and_can_show_suffix_starts():
    tree = SuffixTree("banana")
    dot = tree.to_dot()
    assert dot.startswith("digraph suffix_tree {")
    assert 'rankdir=LR;' in dot
    assert 'label="root"' in dot
    assert 'label="banana$"' in dot

    annotated = tree.to_dot(show_suffix_starts=True)
    assert '[0, 1, 2, 3, 4, 5, 6]' in annotated
    assert 'shape=doublecircle' in annotated


def test_benchmark_matches_baselines_and_csv_export_is_structured():
    tree = SuffixTree("banana bandana banana")
    results = tree.benchmark_search(["ana", "ban", "na"], iterations=3)
    assert len(results) == 9

    grouped = {(result.method, result.pattern): result.matches for result in results}
    for pattern in ["ana", "ban", "na"]:
        expected = grouped[("suffix_tree", pattern)]
        assert grouped[("python_find", pattern)] == expected
        assert grouped[("regex_lookahead", pattern)] == expected

    csv_output = benchmark_results_to_csv(results)
    reader = csv.DictReader(csv_output.splitlines())
    rows = list(reader)
    assert reader.fieldnames == ["method", "pattern", "matches", "total_seconds", "avg_seconds"]
    assert rows[0]["method"] == "suffix_tree"
    assert rows[-1]["pattern"] == "na"


def test_parse_patterns_and_benchmark_reject_invalid_input():
    assert parse_patterns("ana, na,ban") == ["ana", "na", "ban"]
    with pytest.raises(ValueError):
        parse_patterns(" , , ")

    tree = SuffixTree("abcabc")
    with pytest.raises(ValueError):
        tree.benchmark_search([], iterations=2)
    with pytest.raises(ValueError):
        tree.benchmark_search(["abc"], iterations=0)
    with pytest.raises(ValueError):
        tree.benchmark_search(["abc", ""], iterations=2)


def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        SuffixTree("")
    with pytest.raises(ValueError):
        SuffixTree("abc$def")
    tree = SuffixTree("abcabc")
    with pytest.raises(ValueError):
        tree.find("")
    with pytest.raises(ValueError):
        tree.explain_find("")
    with pytest.raises(ValueError):
        tree.longest_repeated_substring(1)


def test_cli_find_repeat_explain_export_and_benchmark_commands(tmp_path: Path):
    script = Path(__file__).with_name("suffix_tree_lab.py")

    result = subprocess.run(
        [sys.executable, str(script), "banana", "find", "ana"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "matches=[1, 3]" in result.stdout

    repeat = subprocess.run(
        [sys.executable, str(script), "banana", "repeat"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert repeat.returncode == 0
    assert repeat.stdout.strip() == "ana"

    explain = subprocess.run(
        [sys.executable, str(script), "banana", "explain", "band"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert explain.returncode == 0
    assert "mismatch" in explain.stdout or "No outgoing edge" in explain.stdout

    export = subprocess.run(
        [sys.executable, str(script), "banana", "export-dot", "--show-suffix-starts"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert export.returncode == 0
    assert export.stdout.startswith("digraph suffix_tree {")
    assert '[0, 1, 2, 3, 4, 5, 6]' in export.stdout

    csv_path = tmp_path / "benchmark.csv"
    benchmark = subprocess.run(
        [
            sys.executable,
            str(script),
            "banana bandana banana",
            "benchmark",
            "--patterns",
            "ana,ban,na",
            "--iterations",
            "2",
            "--csv",
            "--output",
            str(csv_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert benchmark.returncode == 0
    assert benchmark.stdout.startswith("method,pattern,matches,total_seconds,avg_seconds")
    assert csv_path.exists() is True
    assert csv_path.read_text(encoding="utf-8").startswith("method,pattern,matches,total_seconds,avg_seconds")
