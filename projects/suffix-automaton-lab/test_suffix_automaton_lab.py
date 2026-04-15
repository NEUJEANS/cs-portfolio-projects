import json
import subprocess
import sys
from pathlib import Path

from suffix_automaton_lab import SuffixAutomaton

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "suffix_automaton_lab.py"


def run_cli(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_contains_and_occurrence_count():
    automaton = SuffixAutomaton.from_text("banana")

    assert automaton.contains("ana") is True
    assert automaton.contains("apple") is False
    assert automaton.occurrence_count("ana") == 2
    assert automaton.occurrence_count("na") == 2
    assert automaton.occurrence_count("apple") == 0


def test_distinct_and_longest_repeated_substring():
    automaton = SuffixAutomaton.from_text("banana")

    assert automaton.distinct_substring_count() == 15
    assert automaton.longest_repeated_substring() == "ana"




def test_longest_repeat_rejects_invalid_threshold():
    automaton = SuffixAutomaton.from_text("banana")
    try:
        automaton.longest_repeated_substring(1)
    except ValueError as error:
        assert "at least 2" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid threshold")

def test_longest_common_substring():
    automaton = SuffixAutomaton.from_text("abracadabra")
    assert automaton.longest_common_substring("cadabrac") == "cadabra"


def test_cli_stats_and_lcs_commands(tmp_path: Path):
    input_file = tmp_path / "sample.txt"
    input_file.write_text("banana", encoding="utf-8")

    stats = json.loads(run_cli("stats", "--file", str(input_file)))
    assert stats["text_length"] == 6
    assert stats["distinct_substrings"] == 15
    assert stats["longest_repeated_substring"] == "ana"

    assert run_cli("lcs", "--text", "mississippi", "--other", "sippy") == "sipp"


def test_cli_contains_and_count_commands():
    assert run_cli("contains", "--text", "banana", "ana") == "yes"
    assert run_cli("count", "--text", "banana", "ana") == "2"
    assert run_cli("longest-repeat", "--text", "banana", "--min-occurrences", "2") == "ana"
