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

from page_replacement_lab import compare_algorithms, simulate, study_frame_counts


REFERENCE = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "page_replacement_lab.py"


class PageReplacementSimulationTests(unittest.TestCase):
    def test_classic_reference_fault_counts(self) -> None:
        self.assertEqual(simulate("fifo", REFERENCE, 3).page_faults, 9)
        self.assertEqual(simulate("lru", REFERENCE, 3).page_faults, 10)
        self.assertEqual(simulate("opt", REFERENCE, 3).page_faults, 7)

    def test_compare_algorithms_orders_all_strategies(self) -> None:
        results = compare_algorithms(REFERENCE, 4)
        self.assertEqual([result.algorithm for result in results], ["fifo", "lru", "opt"])
        self.assertEqual([result.page_faults for result in results], [10, 8, 6])

    def test_study_detects_fifo_belady_anomaly(self) -> None:
        study = study_frame_counts(REFERENCE, 2, 5)
        self.assertIn(
            {
                "algorithm": "fifo",
                "from_frames": 3,
                "to_frames": 4,
                "faults_before": 9,
                "faults_after": 10,
                "fault_delta": 1,
            },
            study["fifo_belady_anomalies"],
        )

    def test_cli_compare_json_works_with_pages_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(REFERENCE, handle)
            handle.flush()
            page_path = handle.name

        self.addCleanup(lambda: Path(page_path).unlink(missing_ok=True))
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "3",
                "--pages-file",
                page_path,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["frame_count"], 3)
        self.assertEqual(payload["reference_string"], REFERENCE)
        self.assertEqual(payload["results"][0]["algorithm"], "fifo")
        self.assertEqual(payload["results"][2]["page_faults"], 7)

    def test_cli_rejects_missing_reference(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "simulate", "fifo", "--frames", "3"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("provide at least one --page", completed.stderr)


if __name__ == "__main__":
    unittest.main()
