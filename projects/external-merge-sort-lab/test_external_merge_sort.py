from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from external_merge_sort import (
    chunked,
    create_sorted_runs,
    external_merge_sort,
    merge_runs,
    parse_numbers,
    read_numbers,
)


class ExternalMergeSortTests(unittest.TestCase):
    def test_parse_numbers_handles_comments_commas_and_spaces(self) -> None:
        text = """
        # header comment
        7, 1, 3
        9 4
        2 # trailing comment
        """
        self.assertEqual(parse_numbers(text), [7, 1, 3, 9, 4, 2])

    def test_chunked_rejects_invalid_size(self) -> None:
        with self.assertRaises(ValueError):
            list(chunked([1, 2, 3], 0))

    def test_create_sorted_runs_writes_sorted_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs = create_sorted_runs([9, 1, 4, 2, 7], 2, Path(tmp))
            self.assertEqual(len(runs), 3)
            self.assertEqual([read_numbers(path) for path in runs], [[1, 9], [2, 4], [7]])

    def test_merge_runs_handles_multiple_rounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            runs = create_sorted_runs([8, 3, 7, 1, 9, 4, 6, 2, 5], 2, temp_dir)
            merged_path, rounds = merge_runs(runs, 2, temp_dir)
            self.assertEqual(rounds, 3)
            self.assertEqual(read_numbers(merged_path), [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_external_merge_sort_sorts_duplicates_and_negatives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            input_path = temp_dir / "input.txt"
            output_path = temp_dir / "output.txt"
            input_path.write_text("5\n-1\n4\n5\n2\n0\n", encoding="utf-8")
            stats = external_merge_sort(input_path, output_path, chunk_size=2, fan_in=3)
            self.assertEqual(read_numbers(output_path), [-1, 0, 2, 4, 5, 5])
            self.assertEqual(stats.total_numbers, 6)
            self.assertEqual(stats.runs_created, 3)
            self.assertEqual(stats.merge_rounds, 1)

    def test_external_merge_sort_handles_empty_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            input_path = temp_dir / "empty.txt"
            output_path = temp_dir / "output.txt"
            input_path.write_text("", encoding="utf-8")
            stats = external_merge_sort(input_path, output_path, chunk_size=4, fan_in=2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "")
            self.assertEqual(stats.total_numbers, 0)
            self.assertEqual(stats.runs_created, 0)

    def test_cli_stats_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            input_path = temp_dir / "input.txt"
            output_path = temp_dir / "sorted.txt"
            input_path.write_text("10\n1\n8\n3\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "external_merge_sort.py",
                    str(input_path),
                    str(output_path),
                    "--chunk-size",
                    "2",
                    "--fan-in",
                    "2",
                    "--stats",
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )
            stats = json.loads(result.stdout)
            self.assertEqual(stats["runs_created"], 2)
            self.assertEqual(read_numbers(output_path), [1, 3, 8, 10])


if __name__ == "__main__":
    unittest.main()
