from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aho_corasick_search import AhoCorasickAutomaton, load_patterns, search_chunks, search_file, search_text


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "aho_corasick_search.py"


class AhoCorasickSearchTests(unittest.TestCase):
    def test_finds_overlapping_and_suffix_matches(self) -> None:
        automaton = AhoCorasickAutomaton(["he", "she", "hers", "his"])
        matches = automaton.find_matches("ushers")
        self.assertEqual(
            [(match.pattern, match.start, match.end) for match in matches],
            [("she", 1, 4), ("he", 2, 4), ("hers", 2, 6)],
        )

    def test_find_matches_in_chunks_preserves_boundary_matches(self) -> None:
        automaton = AhoCorasickAutomaton(["beta", "ta g", "gamma"])
        matches = automaton.find_matches_in_chunks(["alpha be", "ta gam", "ma"])
        self.assertEqual(
            [(match.pattern, match.start, match.end, match.line, match.column) for match in matches],
            [("beta", 6, 10, 1, 7), ("ta g", 8, 12, 1, 9), ("gamma", 11, 16, 1, 12)],
        )

    def test_case_insensitive_counts_and_locations(self) -> None:
        result = search_text("Alpha\nbeta ALPHA", ["alpha", "beta"], case_sensitive=False)
        self.assertEqual(result["counts"], {"alpha": 2, "beta": 1})
        self.assertEqual(result["matches"][1]["line"], 2)
        self.assertEqual(result["matches"][1]["column"], 1)
        self.assertEqual(result["input"]["mode"], "memory")

    def test_search_chunks_tracks_stream_metadata(self) -> None:
        result = search_chunks(["warn", "ing\ncri", "tical warning"], ["warning", "critical"], chunk_size=4)
        self.assertEqual(result["match_count"], 3)
        self.assertEqual(result["counts"], {"warning": 2, "critical": 1})
        self.assertEqual(result["input"]["mode"], "stream")
        self.assertEqual(result["input"]["chunk_count"], 3)
        self.assertEqual(result["input"]["characters_processed"], len("warning\ncritical warning"))
        self.assertEqual(result["matches"][1]["line"], 2)
        self.assertEqual(result["matches"][1]["column"], 1)

    def test_search_file_streaming_matches_whole_file_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "sample.txt"
            text = "alpha\nher beta\nhers again\n"
            input_file.write_text(text, encoding="utf-8")
            memory_text, memory_result = search_file(input_file, ["her", "hers"])
            stream_text, stream_result = search_file(input_file, ["her", "hers"], chunk_size=3)
            self.assertEqual(memory_text, text)
            self.assertIsNone(stream_text)
            self.assertEqual(memory_result["matches"], stream_result["matches"])
            self.assertEqual(stream_result["input"]["chunk_size"], 3)

    def test_streaming_context_windows_capture_before_and_after_samples(self) -> None:
        result = search_chunks(
            ["alpha wa", "rning! b", "eta warning?"],
            ["warning"],
            chunk_size=8,
            context_chars=2,
        )
        self.assertEqual(result["input"]["context_chars"], 2)
        self.assertEqual(result["input"]["context_mode"], "sampled")
        self.assertEqual(
            [match["context"]["excerpt"] for match in result["matches"]],
            ["a ⟦warning⟧! ", "a ⟦warning⟧?"],
        )
        self.assertEqual(result["matches"][0]["context"]["before"], "a ")
        self.assertEqual(result["matches"][0]["context"]["match"], "warning")
        self.assertEqual(result["matches"][0]["context"]["after"], "! ")

    def test_streaming_context_windows_truncate_cleanly_at_end_of_input(self) -> None:
        result = search_chunks(["tail warning"], ["warning"], chunk_size=32, context_chars=4)
        self.assertEqual(result["matches"][0]["context"]["before"], "ail ")
        self.assertEqual(result["matches"][0]["context"]["match"], "warning")
        self.assertEqual(result["matches"][0]["context"]["after"], "")

    def test_pattern_file_loading_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pattern_file = Path(tmpdir) / "patterns.txt"
            pattern_file.write_text("error\nwarning\nerror\n", encoding="utf-8")
            self.assertEqual(
                load_patterns(["warning", "critical"], str(pattern_file)),
                ["warning", "critical", "error"],
            )

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "sample.txt"
            input_file.write_text("fail fast\nwarn louder\nfail again\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "fail",
                    "warn",
                    "--input",
                    str(input_file),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["match_count"], 3)
            self.assertEqual(payload["counts"], {"fail": 2, "warn": 1})
            self.assertEqual(payload["input"]["mode"], "memory")

    def test_cli_chunked_json_output_reports_stream_metadata_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "sample.txt"
            input_file.write_text("error\nwarning\ncritical\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "warning",
                    "critical",
                    "--input",
                    str(input_file),
                    "--chunk-size",
                    "5",
                    "--context",
                    "2",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["counts"], {"warning": 1, "critical": 1})
            self.assertEqual(payload["input"]["mode"], "stream")
            self.assertEqual(payload["input"]["chunk_size"], 5)
            self.assertEqual(payload["input"]["context_mode"], "sampled")
            self.assertEqual(payload["matches"][0]["context"]["excerpt"], "r\n⟦warning⟧\nc")
            self.assertEqual(payload["matches"][0]["line"], 2)
            self.assertEqual(payload["matches"][1]["line"], 3)

    def test_cli_chunked_text_output_includes_sampled_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "sample.txt"
            input_file.write_text("alpha warning omega\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "warning",
                    "--input",
                    str(input_file),
                    "--chunk-size",
                    "4",
                    "--context",
                    "3",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("context chars: 3 (sampled around matches)", completed.stdout)
            self.assertIn("context='ha ⟦warning⟧ om'", completed.stdout)

    def test_cli_inline_text_output_still_includes_context(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "warning",
                "--text",
                "alpha warning omega",
                "--context",
                "3",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("context chars: 3", completed.stdout)
        self.assertIn("context='ha ⟦warning⟧ om'", completed.stdout)

    def test_cli_rejects_negative_context(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "warn",
                "--text",
                "warning",
                "--context",
                "-1",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--context must be non-negative", completed.stderr)

    def test_direct_api_rejects_negative_context(self) -> None:
        with self.assertRaises(ValueError):
            search_text("warning", ["warn"], context_chars=-1)

    def test_rejects_missing_patterns(self) -> None:
        with self.assertRaises(ValueError):
            load_patterns([], None)


if __name__ == "__main__":
    unittest.main()
