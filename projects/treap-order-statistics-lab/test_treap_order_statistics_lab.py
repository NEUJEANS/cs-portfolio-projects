import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from treap_order_statistics_lab import Treap, benchmark_trees, build_treap

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

    def test_contains_with_stats_reports_comparisons(self) -> None:
        treap = build_treap([40, 10, 60, 5, 20, 50, 70], seed=7)
        found = treap.contains_with_stats(50)
        missing = treap.contains_with_stats(99)
        self.assertTrue(found["found"])
        self.assertGreaterEqual(found["comparisons"], 1)
        self.assertFalse(missing["found"])
        self.assertGreaterEqual(missing["comparisons"], 1)

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

    def test_mermaid_export_includes_nodes_edges_and_nulls(self) -> None:
        treap = build_treap([40, 10, 60, 5, 20], seed=7)
        diagram = treap.to_mermaid()
        self.assertTrue(diagram.startswith("flowchart TD"))
        self.assertIn("key=40", diagram)
        self.assertIn("priority=p", diagram)
        self.assertIn("size=", diagram)
        self.assertIn("-->|L|", diagram)
        self.assertIn("-.->|R|", diagram)
        self.assertIn("((∅))", diagram)

    def test_empty_treap_mermaid_export_is_explicit(self) -> None:
        treap = Treap(seed=9)
        diagram = treap.to_mermaid()
        self.assertEqual(diagram, 'flowchart TD\n    empty["empty treap"]')

    def test_benchmark_summary_reports_cross_tree_comparison(self) -> None:
        payload = benchmark_trees(count=15, start=1, build_seed=7, query_seed=13, queries=24)
        self.assertEqual(set(payload["cases"].keys()), {"ascending", "descending", "shuffled"})
        ascending = payload["cases"]["ascending"]
        self.assertEqual(ascending["input_size"], 15)
        self.assertEqual(ascending["query_count"], 24)
        self.assertIn("treap", ascending)
        self.assertIn("avl", ascending)
        self.assertIn("red_black", ascending)
        self.assertIn("splay", ascending)
        self.assertIn("height_gap_treap_minus_avl", payload["summary"])
        self.assertIn("lookup_gap_treap_minus_red_black", payload["summary"])
        self.assertIn("Treap height stays close", payload["takeaway"])
        self.assertIn("case,input_size,query_count,treap_height", payload["csv"])

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

    def test_cli_benchmark_outputs_cross_tree_cases(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--seed",
                "7",
                "benchmark",
                "--count",
                "15",
                "--queries",
                "24",
                "--query-seed",
                "13",
            ],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["count"], 15)
        self.assertEqual(payload["query_count"], 24)
        self.assertNotIn("csv", payload)
        self.assertIn("shuffled", payload["cases"])
        self.assertIn("red_black", payload["cases"]["shuffled"])
        self.assertIn("lookup_gap_treap_minus_avl", payload["summary"])

    def test_cli_benchmark_can_embed_and_write_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "artifacts" / "treap-benchmark.csv"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--seed",
                    "7",
                    "benchmark",
                    "--count",
                    "11",
                    "--queries",
                    "18",
                    "--query-seed",
                    "5",
                    "--csv",
                    "--csv-file",
                    str(csv_path),
                ],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["csv_file"], str(csv_path))
            self.assertIn("case,input_size,query_count,treap_height", payload["csv"])
            self.assertTrue(csv_path.exists())
            self.assertIn("ascending,11,18", csv_path.read_text(encoding="utf-8"))

    def test_cli_export_mermaid_can_write_diagram_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "docs" / "artifacts" / "treap.mmd"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--seed",
                    "12",
                    "export-mermaid",
                    "40",
                    "10",
                    "60",
                    "5",
                    "20",
                    "50",
                    "70",
                    "--output",
                    str(output_path),
                ],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "export-mermaid")
            self.assertEqual(payload["output_file"], str(output_path))
            self.assertTrue(payload["validation"]["is_valid"])
            self.assertIn("flowchart TD", payload["mermaid"])
            self.assertTrue(output_path.exists())
            written = output_path.read_text(encoding="utf-8")
            self.assertTrue(written.endswith("\n"))
            self.assertIn("key=40", written)

    def test_cli_benchmark_rejects_non_positive_count(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "benchmark", "--count", "0"],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("benchmark count must be positive", payload["error"])

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
