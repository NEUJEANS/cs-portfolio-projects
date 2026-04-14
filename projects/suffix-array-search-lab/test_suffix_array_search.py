from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from suffix_array_search import SuffixArrayIndex


SAMPLE_TEXT = "banana\nbandana\nBanana band\n"


class SuffixArraySearchTests(unittest.TestCase):
    def test_build_orders_suffixes_lexicographically(self) -> None:
        index = SuffixArrayIndex.build("banana")
        ordered_suffixes = [index.text[i:] for i in index.suffix_array]
        self.assertEqual(ordered_suffixes, sorted(ordered_suffixes))

    def test_find_positions_returns_all_substring_hits(self) -> None:
        index = SuffixArrayIndex.build(SAMPLE_TEXT)
        self.assertEqual(index.find_positions("ana"), [1, 3, 11, 16, 18])

    def test_line_number_lookup(self) -> None:
        index = SuffixArrayIndex.build(SAMPLE_TEXT)
        self.assertEqual(index.line_number_for(0), 1)
        self.assertEqual(index.line_number_for(7), 2)
        self.assertEqual(index.line_number_for(16), 3)

    def test_keyword_in_context_validates_and_highlights(self) -> None:
        index = SuffixArrayIndex.build(SAMPLE_TEXT)
        hit = index.keyword_in_context("band", context_chars=3, limit=1)[0]
        self.assertIn("[band]", hit.context)
        with self.assertRaises(ValueError):
            index.keyword_in_context("band", context_chars=-1)
        with self.assertRaises(ValueError):
            index.keyword_in_context("band", limit=0)

    def test_save_load_and_stats_shape(self) -> None:
        index = SuffixArrayIndex.build(SAMPLE_TEXT)
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.json"
            index.save(index_path)
            loaded = SuffixArrayIndex.load(index_path)
            self.assertEqual(loaded.text, SAMPLE_TEXT)
            self.assertEqual(loaded.suffix_array, index.suffix_array)
            self.assertEqual(loaded.line_starts, [0, 7, 15])

    def test_cli_build_search_and_stats(self) -> None:
        project_dir = PROJECT_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            text_path = Path(tmpdir) / "sample.txt"
            index_path = Path(tmpdir) / "sample_index.json"
            text_path.write_text(SAMPLE_TEXT, encoding="utf-8")

            build = subprocess.run(
                ["python3", "suffix_array_search.py", "build", "--input", str(text_path), "--output", str(index_path)],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("built suffix-array index", build.stdout)

            search = subprocess.run(
                [
                    "python3",
                    "suffix_array_search.py",
                    "search",
                    "--index",
                    str(index_path),
                    "--show-line-numbers",
                    "--ignore-case",
                    "band",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(search.returncode, 0)
            self.assertIn("line 2, pos 7", search.stdout)
            self.assertIn("line 3, pos 22", search.stdout)
            self.assertIn("[band]", search.stdout)

            stats = subprocess.run(
                ["python3", "suffix_array_search.py", "stats", "--index", str(index_path)],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(stats.stdout)
            self.assertEqual(payload["lines"], 3)
            self.assertEqual(payload["suffixes"], len(SAMPLE_TEXT))


if __name__ == "__main__":
    unittest.main()
