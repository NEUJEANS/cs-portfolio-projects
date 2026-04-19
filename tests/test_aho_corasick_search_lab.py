from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "aho-corasick-search-lab" / "aho_corasick_search.py"
SCRIPT_PATH = MODULE_PATH

spec = importlib.util.spec_from_file_location("aho_corasick_search_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

AhoCorasickAutomaton = module.AhoCorasickAutomaton
search_chunks = module.search_chunks
search_file = module.search_file
search_text = module.search_text


class AhoCorasickSearchLabTests(unittest.TestCase):
    def test_search_text_finds_suffix_and_overlap_matches(self) -> None:
        result = search_text("ushers", ["he", "she", "hers"])
        self.assertEqual(result["match_count"], 3)
        self.assertEqual(
            [(match["pattern"], match["start"], match["end"]) for match in result["matches"]],
            [("she", 1, 4), ("he", 2, 4), ("hers", 2, 6)],
        )

    def test_streaming_search_preserves_boundary_matches_and_locations(self) -> None:
        result = search_chunks(["error wa", "rning\ncri", "tical"], ["warning", "critical"], chunk_size=8)
        self.assertEqual(result["counts"], {"warning": 1, "critical": 1})
        self.assertEqual(result["input"]["mode"], "stream")
        self.assertEqual(result["input"]["chunk_count"], 3)
        self.assertEqual(result["matches"][0]["line"], 1)
        self.assertEqual(result["matches"][0]["column"], 7)
        self.assertEqual(result["matches"][1]["line"], 2)
        self.assertEqual(result["matches"][1]["column"], 1)

    def test_search_file_streaming_matches_memory_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.txt"
            path.write_text("alpha\nbeta\nalpha beta\n", encoding="utf-8")
            memory_text, memory_result = search_file(path, ["alpha", "beta"])
            stream_text, stream_result = search_file(path, ["alpha", "beta"], chunk_size=4)
            self.assertEqual(memory_text, "alpha\nbeta\nalpha beta\n")
            self.assertIsNone(stream_text)
            self.assertEqual(memory_result["matches"], stream_result["matches"])
            self.assertEqual(stream_result["input"]["characters_processed"], len(memory_text))

    def test_automaton_chunk_scan_matches_single_pass_scan(self) -> None:
        automaton = AhoCorasickAutomaton(["aba", "bab"])
        single_pass = [(match.pattern, match.start, match.end) for match in automaton.find_matches("ababa")]
        chunked = [
            (match.pattern, match.start, match.end)
            for match in automaton.find_matches_in_chunks(["ab", "ab", "a"])
        ]
        self.assertEqual(single_pass, chunked)

    def test_chunked_context_windows_are_sampled_without_full_text(self) -> None:
        result = search_chunks(
            ["error wa", "rning\ncr", "itical"],
            ["warning", "critical"],
            chunk_size=8,
            context_chars=2,
        )
        self.assertEqual(result["input"]["context_mode"], "sampled")
        self.assertEqual(result["matches"][0]["context"]["excerpt"], "r ⟦warning⟧\nc")
        self.assertEqual(result["matches"][1]["context"]["excerpt"], "g\n⟦critical⟧")

    def test_direct_api_rejects_negative_context(self) -> None:
        with self.assertRaises(ValueError):
            search_text("warning", ["warning"], context_chars=-1)

    def test_cli_chunked_json_output_exposes_stream_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.txt"
            path.write_text("warning\ncritical\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "warning",
                    "critical",
                    "--input",
                    str(path),
                    "--chunk-size",
                    "4",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["counts"], {"warning": 1, "critical": 1})
            self.assertEqual(payload["input"]["mode"], "stream")
            self.assertEqual(payload["input"]["chunk_size"], 4)
            self.assertEqual(payload["input"]["boundary_overlap"], len("critical") - 1)

    def test_cli_chunked_context_is_available_in_text_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.txt"
            path.write_text("before warning after", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "warning",
                    "--input",
                    str(path),
                    "--chunk-size",
                    "3",
                    "--context",
                    "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("context chars: 2 (sampled around matches)", completed.stdout)
            self.assertIn("context='e ⟦warning⟧ a'", completed.stdout)

    def test_inline_text_context_still_uses_shared_context_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "warning",
                "--text",
                "before warning after",
                "--context",
                "2",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("context chars: 2", completed.stdout)
        self.assertIn("context='e ⟦warning⟧ a'", completed.stdout)


if __name__ == "__main__":
    unittest.main()
