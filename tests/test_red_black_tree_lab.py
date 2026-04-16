from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "red-black-tree-lab" / "red_black_tree.py"

spec = importlib.util.spec_from_file_location("red_black_tree_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

BLACK = module.BLACK
build_tree = module.build_tree
RedBlackTree = module.RedBlackTree


class RedBlackTreeLabTests(unittest.TestCase):
    def test_sorted_insertions_stay_valid_and_balanced(self) -> None:
        tree = build_tree([10, 20, 30, 40, 50, 60, 70])
        valid, black_height, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.root.key, 20)
        self.assertEqual(tree.root.color, BLACK)
        self.assertEqual(tree.root.subtree_size, tree.size)
        self.assertEqual(tree.inorder(), [10, 20, 30, 40, 50, 60, 70])
        self.assertLessEqual(tree.height(), 4)
        self.assertGreaterEqual(black_height, 2)

    def test_duplicate_insertions_are_rejected_without_size_growth(self) -> None:
        tree = build_tree([7, 3, 18, 10])
        self.assertFalse(tree.insert(10))
        self.assertEqual(tree.size, 4)
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)

    def test_contains_queries_existing_and_missing_keys(self) -> None:
        tree = build_tree([11, 2, 14, 1, 7, 15, 5, 8])
        self.assertTrue(tree.contains(7))
        self.assertTrue(tree.contains(15))
        self.assertFalse(tree.contains(6))

    def test_rank_counts_smaller_keys_for_present_and_missing_queries(self) -> None:
        tree = build_tree([20, 10, 30, 5, 15, 25, 35])
        self.assertEqual(tree.rank(5), 0)
        self.assertEqual(tree.rank(15), 2)
        self.assertEqual(tree.rank(17), 3)
        self.assertEqual(tree.rank(40), 7)

    def test_select_returns_zero_based_kth_smallest_key(self) -> None:
        tree = build_tree([20, 10, 30, 5, 15, 25, 35])
        self.assertEqual(tree.select(0), 5)
        self.assertEqual(tree.select(3), 20)
        self.assertEqual(tree.select(6), 35)
        with self.assertRaises(IndexError):
            tree.select(7)

    def test_delete_leaf_preserves_invariants(self) -> None:
        tree = build_tree([20, 10, 30, 5, 15, 25, 35])
        self.assertTrue(tree.delete(5))
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), [10, 15, 20, 25, 30, 35])
        self.assertEqual(tree.size, 6)
        self.assertEqual(tree.rank(20), 2)

    def test_delete_node_with_one_child_preserves_invariants(self) -> None:
        tree = build_tree([10, 5, 20, 15])
        self.assertTrue(tree.delete(20))
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), [5, 10, 15])
        self.assertEqual(tree.size, 3)

    def test_delete_node_with_two_children_preserves_order_statistics(self) -> None:
        tree = build_tree([20, 10, 30, 5, 15, 25, 35, 12, 18])
        self.assertTrue(tree.delete(10))
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), [5, 12, 15, 18, 20, 25, 30, 35])
        self.assertEqual(tree.select(3), 18)
        self.assertEqual(tree.rank(20), 4)

    def test_delete_missing_key_reports_false_without_mutation(self) -> None:
        tree = build_tree([9, 4, 12])
        self.assertFalse(tree.delete(7))
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), [4, 9, 12])
        self.assertEqual(tree.size, 3)

    def test_trace_records_insert_and_delete_fixup_events(self) -> None:
        tree = build_tree([10, 20, 30, 15, 25, 5], trace_enabled=True)
        self.assertTrue(any(event["event"] == "rotate_left" for event in tree.trace))
        self.assertTrue(any(event["event"] == "insert_fixup_line" for event in tree.trace))
        tree.trace.clear()
        self.assertTrue(tree.delete(10))
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertTrue(any(event["event"] == "delete_case_two_children" for event in tree.trace))
        self.assertTrue(any(event["event"] == "delete_complete" for event in tree.trace))

    def test_trace_can_be_enabled_after_construction(self) -> None:
        tree = RedBlackTree()
        tree.enable_trace()
        tree.insert(10)
        tree.insert(20)
        tree.insert(30)
        self.assertTrue(tree.trace)
        summary = tree.summary(include_trace=True)
        self.assertIn("trace", summary)
        self.assertTrue(any(event["event"] == "rotate_left" for event in summary["trace"]))

    def test_delete_sequence_to_empty_tree_stays_valid(self) -> None:
        values = [41, 38, 31, 12, 19, 8]
        tree = build_tree(values)
        for value in [8, 12, 19, 31, 38, 41]:
            self.assertTrue(tree.delete(value))
            valid, _, errors = tree.validate()
            self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), [])
        self.assertEqual(tree.size, 0)
        self.assertIsNone(tree.root)

    def test_summary_reports_validation_state(self) -> None:
        tree = build_tree([41, 38, 31, 12, 19, 8])
        summary = tree.summary()
        self.assertTrue(summary["valid"], summary["errors"])
        self.assertEqual(summary["root"]["color"], BLACK)
        self.assertEqual(summary["root"]["subtree_size"], tree.size)
        self.assertEqual(summary["inorder"], [8, 12, 19, 31, 38, 41])

    def test_to_dot_includes_colors_edges_and_nil_leaves(self) -> None:
        tree = build_tree([20, 10, 30, 5])
        dot = tree.to_dot()
        self.assertIn('digraph RedBlackTree {', dot)
        self.assertIn('label="20\\nsize=4"', dot)
        self.assertIn('label="L"', dot)
        self.assertIn('label="R"', dot)
        self.assertIn('label="NIL"', dot)
        self.assertIn('fillcolor="#24292f"', dot)
        self.assertIn('fillcolor="#d73a49"', dot)

    def test_to_dot_can_omit_nil_leaves(self) -> None:
        tree = build_tree([20, 10, 30, 5])
        dot = tree.to_dot(include_nil=False)
        self.assertNotIn('label="NIL"', dot)

    def test_validate_catches_parent_pointer_corruption(self) -> None:
        tree = build_tree([10, 5, 15])
        tree.root.left.parent = None
        valid, _, errors = tree.validate()
        self.assertFalse(valid)
        self.assertTrue(any("parent pointer mismatch" in error for error in errors))

    def test_validate_catches_subtree_size_corruption(self) -> None:
        tree = build_tree([10, 5, 15])
        tree.root.subtree_size = 99
        valid, _, errors = tree.validate()
        self.assertFalse(valid)
        self.assertTrue(any("subtree_size mismatch" in error for error in errors))

    def test_cli_demo_outputs_expected_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertTrue(payload["valid"], payload["errors"])
        self.assertEqual(payload["contains"], {"8": True, "15": False})
        self.assertEqual(payload["rank"], {"8": 2, "15": 5})
        self.assertEqual(payload["select"], {"0": 3, "3": 10})

    def test_cli_contains_command_respects_query(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "contains", "25", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "contains")
        self.assertEqual(payload["query"], 25)
        self.assertTrue(payload["found"])
        self.assertTrue(payload["valid"], payload["errors"])

    def test_cli_rank_and_select_commands(self) -> None:
        rank_completed = subprocess.run(
            ["python3", str(MODULE_PATH), "rank", "16", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        rank_payload = json.loads(rank_completed.stdout)
        self.assertEqual(rank_payload["command"], "rank")
        self.assertEqual(rank_payload["rank"], 3)

        select_completed = subprocess.run(
            ["python3", str(MODULE_PATH), "select", "4", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        select_payload = json.loads(select_completed.stdout)
        self.assertEqual(select_payload["command"], "select")
        self.assertEqual(select_payload["selected"], 25)
        self.assertTrue(select_payload["valid"], select_payload["errors"])

    def test_cli_delete_command_reports_updated_tree(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "delete", "10", "20", "10", "30", "5", "15", "25", "35"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "delete")
        self.assertTrue(payload["deleted"])
        self.assertEqual(payload["inorder"], [5, 15, 20, 25, 30, 35])
        self.assertTrue(payload["valid"], payload["errors"])

    def test_cli_trace_flag_includes_rotation_and_fixup_events(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "delete", "--trace", "10", "20", "10", "30", "5", "15", "25", "35"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn("trace", payload)
        self.assertTrue(any(event["event"] == "delete_case_two_children" for event in payload["trace"]))
        self.assertTrue(any(event["event"] == "delete_complete" for event in payload["trace"]))

    def test_cli_dot_command_returns_graphviz_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "dot", "20", "10", "30", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "dot")
        self.assertTrue(payload["include_nil"])
        self.assertIn('digraph RedBlackTree {', payload["dot"])
        self.assertIn('label="NIL"', payload["dot"])
        self.assertTrue(payload["valid"], payload["errors"])

    def test_cli_explain_trace_build_returns_markdown_walkthrough(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "explain-trace", "build", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "explain-trace")
        self.assertEqual(payload["operation"], "build")
        self.assertIn("# Red-Black Tree Trace Walkthrough (build)", payload["markdown"])
        self.assertIn("## Tree snapshots", payload["markdown"])
        self.assertIn("### Initial DOT", payload["markdown"])
        self.assertIn("### Final DOT", payload["markdown"])
        self.assertIn('digraph RedBlackTree {', payload["initial_dot"])
        self.assertIn('label="∅"', payload["initial_dot"])
        self.assertIn('digraph RedBlackTree {', payload["final_dot"])
        self.assertNotEqual(payload["initial_dot"], payload["final_dot"])
        self.assertIn("Rotated left around pivot `10`", payload["markdown"])
        self.assertTrue(payload["valid"], payload["errors"])

    def test_cli_explain_trace_delete_can_write_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "trace.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "explain-trace",
                    "delete",
                    "20",
                    "10",
                    "30",
                    "5",
                    "15",
                    "25",
                    "35",
                    "--query",
                    "10",
                    "--output",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["operation"], "delete")
            self.assertTrue(payload["deleted"])
            self.assertEqual(payload["output"], str(output_path))
            self.assertIn('digraph RedBlackTree {', payload["initial_dot"])
            self.assertIn('digraph RedBlackTree {', payload["final_dot"])
            markdown = output_path.read_text(encoding="utf-8")
            self.assertIn("delete query: `10`", markdown)
            self.assertIn("### Initial DOT", markdown)
            self.assertIn("### Final DOT", markdown)
            self.assertIn("Node `10` had two children", markdown)
            self.assertIn("Finished deletion for key `10`", markdown)
            self.assertTrue(payload["valid"], payload["errors"])

    def test_cli_dot_command_can_omit_nil_leaves(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "dot", "--no-nil", "20", "10", "30", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["include_nil"])
        self.assertNotIn('label="NIL"', payload["dot"])

    def test_benchmark_sequence_reports_valid_red_black_and_avl_metrics(self) -> None:
        summary = module._benchmark_sequence([1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(summary["input_size"], 7)
        self.assertIn("black_height", summary["red_black"])
        self.assertGreaterEqual(summary["red_black"]["height"], 1)
        self.assertGreaterEqual(summary["avl"]["height"], 1)
        self.assertGreaterEqual(summary["red_black"]["rotation_count"], 0)
        self.assertGreaterEqual(summary["avl"]["rotation_count"], 0)

    def test_benchmark_rows_and_csv_export_are_chart_ready(self) -> None:
        cases = {
            "ascending": module._benchmark_sequence([1, 2, 3, 4, 5]),
            "descending": module._benchmark_sequence([5, 4, 3, 2, 1]),
        }
        rows = module._benchmark_rows(cases)
        self.assertEqual([row["case"] for row in rows], ["ascending", "descending"])
        self.assertIn("height_gap_avl_minus_red_black", rows[0])
        csv_text = module._benchmark_csv(rows)
        self.assertIn("case,input_size,red_black_height", csv_text)
        self.assertIn("ascending,5", csv_text)
        self.assertIn("descending,5", csv_text)

    def test_benchmark_series_reports_runs_rows_and_aggregate_metrics(self) -> None:
        series = module._benchmark_series([7, 15], start=1, seed=11)
        self.assertEqual([run["count"] for run in series["runs"]], [7, 15])
        self.assertEqual(series["aggregate"]["run_count"], 2)
        self.assertEqual(series["aggregate"]["count_min"], 7)
        self.assertEqual(series["aggregate"]["count_max"], 15)
        self.assertEqual(len(series["rows"]), 6)
        self.assertEqual(series["rows"][0]["series_count"], 7)
        self.assertIn("rotation_gap_avl_minus_red_black", series["aggregate"])

    def test_cli_benchmark_outputs_comparison_cases(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "benchmark", "--count", "9", "--seed", "11"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["count"], 9)
        self.assertEqual(set(payload["cases"].keys()), {"ascending", "descending", "shuffled"})
        self.assertIn("height_gap_avl_minus_red_black", payload["summary"])
        self.assertIn("rotation_gap_avl_minus_red_black", payload["summary"])

    def test_cli_benchmark_can_embed_csv_output(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "benchmark", "--count", "9", "--seed", "11", "--csv"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn("csv", payload)
        self.assertIn("case,input_size,red_black_height", payload["csv"])
        self.assertIn("ascending,9", payload["csv"])

    def test_cli_benchmark_can_write_csv_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "artifacts" / "red-black-benchmark.csv"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--count",
                    "9",
                    "--seed",
                    "11",
                    "--csv-file",
                    str(csv_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["csv_file"], str(csv_path))
            self.assertTrue(csv_path.exists())
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("case,input_size,red_black_height", csv_text)
            self.assertIn("shuffled,9", csv_text)

    def test_cli_benchmark_rejects_non_positive_count(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "benchmark", "--count", "0"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("benchmark count must be positive", completed.stderr)

    def test_cli_benchmark_series_outputs_runs_and_aggregate(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "benchmark-series", "7", "15", "--seed", "11"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark-series")
        self.assertEqual(payload["counts"], [7, 15])
        self.assertEqual(len(payload["runs"]), 2)
        self.assertEqual(payload["aggregate"]["run_count"], 2)
        self.assertIn("height_gap_avl_minus_red_black", payload["aggregate"])

    def test_cli_benchmark_series_can_write_csv_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "artifacts" / "red-black-benchmark-series.csv"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark-series",
                    "7",
                    "15",
                    "--seed",
                    "11",
                    "--csv-file",
                    str(csv_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["csv_file"], str(csv_path))
            self.assertTrue(csv_path.exists())
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("series_count,case,input_size", csv_text)
            self.assertIn("7,ascending,7", csv_text)
            self.assertIn("15,shuffled,15", csv_text)

    def test_cli_benchmark_series_rejects_non_positive_counts(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "benchmark-series", "7", "0"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("benchmark series counts must be positive", completed.stderr)

    def test_cli_select_reports_out_of_range_index(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "select", "9", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("out of range", completed.stderr)


if __name__ == "__main__":
    unittest.main()
