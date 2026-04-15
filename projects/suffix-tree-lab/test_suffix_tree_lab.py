import subprocess
import sys
from pathlib import Path

import pytest

from suffix_tree_lab import SuffixTree


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


def test_cli_find_repeat_and_explain_commands():
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
