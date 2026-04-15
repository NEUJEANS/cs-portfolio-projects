import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from treap_order_statistics_lab import Treap, build_treap

SCRIPT = PROJECT_DIR / "treap_order_statistics_lab.py"


class TreapOrderStatisticsLabTests(unittest.TestCase):
    def test_inorder_stays_sorted_after_inserts(self) -> None:
        treap = build_treap([40, 10, 60, 5, 20, 50, 70], seed=7)
        self.assertEqual(treap.inorder(), [5, 10, 20, 40, 50, 60, 70])
        self.assertTrue(treap.validate()["is_valid"])

    def test_delete_keeps_structure_valid(self) -> None:
        treap = build_treap([40, 10, 60, 5, 20, 50, 70, 65], seed=11)
        treap.delete(60)
        self.assertEqual(treap.inorder(), [5, 10, 20, 40, 50, 65, 70])
        self.assertTrue(treap.validate()["is_valid"])

    def test_rank_select_and_range_count(self) -> None:
        treap = build_treap([40, 10, 60, 5, 20, 50, 70, 65], seed=3)
        self.assertEqual(treap.rank(50), 4)
        self.assertEqual(treap.select(3), 40)
        self.assertEqual(treap.range_count(15, 65), 5)

    def test_duplicates_are_rejected(self) -> None:
        treap = Treap(seed=1)
        treap.insert(10)
        with self.assertRaises(ValueError):
            treap.insert(10)

    def test_missing_delete_raises(self) -> None:
        treap = build_treap([1, 2, 3], seed=4)
        with self.assertRaises(KeyError):
            treap.delete(99)

    def test_validate_catches_size_corruption(self) -> None:
        treap = build_treap([30, 10, 40, 5], seed=13)
        assert treap.root is not None
        treap.root.size = 999
        report = treap.validate()
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("size mismatch" in issue for issue in report["issues"]))

    def test_trace_logs_insert_and_delete(self) -> None:
        treap = build_treap([10, 20, 30], seed=2, trace=True)
        treap.delete(20)
        self.assertTrue(any("insert key=10" in event for event in treap.events))
        self.assertTrue(any("delete key=20" in event for event in treap.events))

    def test_cli_demo_outputs_valid_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--seed", "5", "demo", "--trace"],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["validation"]["is_valid"])
        self.assertEqual(payload["rank_50"], 5)
        self.assertEqual(payload["select_3"], 20)
        self.assertTrue(payload["trace"])

    def test_cli_error_is_reported_as_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "select", "99", "1", "2", "3"],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
