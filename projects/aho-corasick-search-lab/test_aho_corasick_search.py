from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from aho_corasick_search import AhoCorasickAutomaton, load_patterns, search_text


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

    def test_case_insensitive_counts_and_locations(self) -> None:
        result = search_text("Alpha\nbeta ALPHA", ["alpha", "beta"], case_sensitive=False)
        self.assertEqual(result["counts"], {"alpha": 2, "beta": 1})
        self.assertEqual(result["matches"][1]["line"], 2)
        self.assertEqual(result["matches"][1]["column"], 1)

    def test_pattern_file_loading_deduplicates(self) -> None:
        tmp_dir = Path(self.id().replace(".", "_"))
        tmp_dir.mkdir(exist_ok=True)
        try:
            pattern_file = tmp_dir / "patterns.txt"
            pattern_file.write_text("error\nwarning\nerror\n", encoding="utf-8")
            self.assertEqual(
                load_patterns(["warning", "critical"], str(pattern_file)),
                ["warning", "critical", "error"],
            )
        finally:
            if tmp_dir.exists():
                for path in tmp_dir.iterdir():
                    path.unlink()
                tmp_dir.rmdir()

    def test_cli_json_output(self) -> None:
        tmp_dir = Path(self.id().replace(".", "_"))
        tmp_dir.mkdir(exist_ok=True)
        try:
            input_file = tmp_dir / "sample.txt"
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
        finally:
            if tmp_dir.exists():
                for path in tmp_dir.iterdir():
                    path.unlink()
                tmp_dir.rmdir()

    def test_rejects_missing_patterns(self) -> None:
        with self.assertRaises(ValueError):
            load_patterns([], None)


if __name__ == "__main__":
    unittest.main()
