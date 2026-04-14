from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from mapreduce import execute_job


class MiniMapReduceTests(unittest.TestCase):
    def test_wordcount_across_multiple_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a = Path(tmpdir) / "a.txt"
            b = Path(tmpdir) / "b.txt"
            a.write_text("Red fish blue fish\nred bird\n", encoding="utf-8")
            b.write_text("blue bird bird\n", encoding="utf-8")

            result = execute_job("wordcount", [a, b], shard_size=2)

            self.assertEqual(result.shard_count, 2)
            self.assertEqual(result.output["bird"], 3)
            self.assertEqual(result.output["blue"], 2)
            self.assertEqual(result.output["fish"], 2)
            self.assertEqual(result.output["red"], 2)

    def test_json_group_count_handles_missing_and_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = Path(tmpdir) / "events.jsonl"
            data.write_text(
                "\n".join(
                    [
                        '{"status":"ok"}',
                        '{"status":"ok"}',
                        '{"status":null}',
                        '{"other":1}',
                        '{"status":"error"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = execute_job("json-group-count", [data], shard_size=2, group_field="status")

            self.assertEqual(result.output["ok"], 2)
            self.assertEqual(result.output["error"], 1)
            self.assertEqual(result.output["<null>"], 1)
            self.assertEqual(result.output["<missing>"], 1)

    def test_cli_writes_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            output = Path(tmpdir) / "result.json"
            source.write_text("alpha beta alpha\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "wordcount",
                    str(source),
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["output"], {"alpha": 2, "beta": 1})
            self.assertEqual(payload["job"], "wordcount")

    def test_cli_requires_group_field_for_json_group_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "events.jsonl"
            source.write_text('{"status":"ok"}\n', encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "json-group-count",
                    str(source),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--group-field is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
