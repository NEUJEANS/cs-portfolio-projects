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

from splay_tree_lab import SplayTree, benchmark_csv_rows, benchmark_series, benchmark_series_csv_rows, benchmark_trees, export_trace_step_snapshots


class SplayTreeBehaviorTests(unittest.TestCase):
    def test_insert_makes_latest_key_root(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7])
        self.assertEqual(tree.root.key, 7)
        inserted = tree.insert(12)
        self.assertTrue(inserted)
        self.assertEqual(tree.root.key, 12)
        self.assertEqual(tree.inorder(), [2, 4, 7, 10, 12, 15])

    def test_access_sequence_tracks_hits_and_misses(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        summary = tree.access_sequence([7, 7, 18, 99])
        self.assertEqual(summary["hits"], 3)
        self.assertEqual(summary["misses"], 1)
        self.assertEqual(summary["requested_keys"], [7, 7, 18, 99])
        self.assertGreaterEqual(summary["rotations_used"], 1)
        self.assertEqual(tree.root.key, 18)

    def test_trace_access_sequence_includes_step_metrics(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        trace = tree.trace_access_sequence([7, 18, 99])
        self.assertEqual(trace["hits"], 2)
        self.assertEqual(trace["misses"], 1)
        self.assertEqual([step["key"] for step in trace["steps"]], [7, 18, 99])
        self.assertEqual(trace["steps"][0]["root_before"], 18)
        self.assertEqual(trace["steps"][0]["root_after"], 7)
        self.assertFalse(trace["steps"][-1]["found"])
        self.assertGreaterEqual(trace["steps"][-1]["comparisons_used"], 1)

    def test_trace_access_sequence_can_capture_structured_snapshots(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        trace = tree.trace_access_sequence([7, 18], capture_tree_snapshots=True)
        frames = trace["tree_snapshots"]
        self.assertEqual([frame["step_index"] for frame in frames], [0, 1, 2])
        self.assertEqual(frames[0]["label"], "initial")
        self.assertEqual(frames[1]["access_key"], 7)
        self.assertTrue(frames[1]["found"])
        self.assertEqual(frames[1]["trace_step"]["root_after"], 7)
        self.assertEqual(frames[1]["structure"]["key"], 7)
        self.assertEqual(frames[2]["structure"]["key"], 18)

    def test_export_trace_step_snapshots_writes_manifest(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        summary = tree.trace_access_sequence([7, 18, 99], capture_tree_snapshots=True)
        with tempfile.TemporaryDirectory() as tmp_dir:
            exported = export_trace_step_snapshots(summary, Path(tmp_dir))
            self.assertEqual(exported["step_snapshot_count"], 4)
            manifest = json.loads((Path(tmp_dir) / "manifest.json").read_text())
            self.assertEqual(manifest["snapshot_count"], 4)
            self.assertEqual(manifest["snapshots"][0]["path"], "00-initial.json")
            self.assertEqual(manifest["snapshots"][1]["path"], "01-after-access-7.json")
            self.assertTrue((Path(tmp_dir) / "03-after-access-99.json").exists())
            final_snapshot = json.loads((Path(tmp_dir) / "03-after-access-99.json").read_text())
            self.assertEqual(final_snapshot["trace_step"]["root_after"], 18)
            self.assertEqual(final_snapshot["structure"]["key"], 18)

    def test_to_dot_marks_root_and_highlighted_keys(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        dot = tree.to_dot(highlight_keys=[7, 18], title="demo")
        self.assertIn('label="demo"', dot)
        self.assertIn('n18 [label="18", penwidth=2, style="filled,bold", fillcolor="lightgoldenrod1"]', dot)
        self.assertIn('n7 -> n10;', dot)

    def test_to_mermaid_marks_root_and_highlighted_keys(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        mermaid = tree.to_mermaid(highlight_keys=[7, 18, 99], title="demo")
        self.assertIn("flowchart TD", mermaid)
        self.assertIn("%% demo", mermaid)
        self.assertIn('n18["18"]', mermaid)
        self.assertIn("n12 --> n7", mermaid)
        self.assertIn("class n18 root;", mermaid)
        self.assertIn("class n7,n18 highlight;", mermaid)

    def test_delete_preserves_bst_order(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        deleted = tree.delete(10)
        self.assertTrue(deleted)
        self.assertEqual(tree.inorder(), [2, 4, 7, 12, 15, 18])
        self.assertEqual(tree.size, 6)

    def test_benchmark_reports_hotset_advantage(self) -> None:
        payload = benchmark_trees(size=63, hot_set_size=4, hot_queries=128, random_queries=128, seed=7)
        self.assertEqual(payload["size"], 63)
        self.assertEqual(payload["hot_set_size"], 4)
        self.assertEqual(len(payload["hot_keys"]), 4)
        self.assertGreater(payload["takeaway"]["hotset_comparison_gap"], 0)
        self.assertIn("uniform_random", payload["workloads"])
        self.assertIn("hotset", payload["workloads"])

    def test_benchmark_csv_rows_cover_both_workloads(self) -> None:
        payload = benchmark_trees(size=63, hot_set_size=4, hot_queries=64, random_queries=64, seed=11)
        rows = benchmark_csv_rows(payload)
        self.assertEqual([row["workload"] for row in rows], ["hotset", "uniform_random"])
        self.assertEqual(rows[0]["size"], 63)
        self.assertEqual(rows[0]["hot_set_size"], 4)
        self.assertEqual(rows[0]["query_count"], 64)
        self.assertIn("comparison_gap", rows[0])
        self.assertGreater(rows[0]["red_black_comparisons_used"], 0)

    def test_benchmark_series_summarizes_multiple_sizes(self) -> None:
        payload = benchmark_series(sizes=[31, 63, 127], hot_set_size=4, hot_queries=64, random_queries=64, seed=19)
        self.assertEqual(payload["sizes"], [31, 63, 127])
        self.assertEqual(len(payload["entries"]), 3)
        self.assertEqual([row["size"] for row in payload["summary"]], [31, 63, 127])
        self.assertEqual(payload["summary"][1]["seed"], 20)
        self.assertIn(payload["takeaway"]["best_hotset_gap"]["size"], payload["sizes"])
        self.assertIn(payload["takeaway"]["best_uniform_random_gap"]["size"], payload["sizes"])

    def test_benchmark_series_csv_rows_flatten_sizes_and_workloads(self) -> None:
        payload = benchmark_series(sizes=[31, 63], hot_set_size=4, hot_queries=64, random_queries=64, seed=23)
        rows = benchmark_series_csv_rows(payload)
        self.assertEqual(len(rows), 4)
        self.assertEqual([(row["series_index"], row["size"], row["workload"]) for row in rows], [
            (0, 31, "hotset"),
            (0, 31, "uniform_random"),
            (1, 63, "hotset"),
            (1, 63, "uniform_random"),
        ])
        self.assertAlmostEqual(rows[0]["hot_set_ratio"], round(4 / 31, 4))
        self.assertIn("comparison_gap", rows[-1])

    def test_benchmark_series_deduplicates_sizes_preserving_order(self) -> None:
        payload = benchmark_series(sizes=[63, 31, 63], hot_set_size=4, hot_queries=64, random_queries=64, seed=29)
        self.assertEqual(payload["sizes"], [63, 31])
        self.assertEqual([row["seed"] for row in payload["summary"]], [29, 30])

    def test_split_returns_values_around_missing_pivot(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        result = tree.split(11)
        self.assertFalse(result.found)
        self.assertEqual(result.left, [2, 4, 7, 10])
        self.assertEqual(result.right, [12, 15, 18])
        self.assertIn(result.left_root, result.left)
        self.assertIn(result.right_root, result.right)

    def test_split_tracks_empty_partition_roots(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        result = tree.split(2)
        self.assertTrue(result.found)
        self.assertEqual(result.left, [])
        self.assertEqual(result.left_root, None)
        self.assertEqual(result.right, [4, 7, 10, 12, 15, 18])
        self.assertIn(result.right_root, result.right)

    def test_join_from_values_rebuilds_valid_tree(self) -> None:
        tree = SplayTree.join_from_values([1, 3, 5], [8, 13, 21])
        self.assertEqual(tree.inorder(), [1, 3, 5, 8, 13, 21])
        self.assertEqual(tree.size, 6)


class SplayTreeCliTests(unittest.TestCase):
    def test_build_and_access_cli(self) -> None:
        project_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            build = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(project_dir / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            build_payload = json.loads(build.stdout)
            self.assertEqual(build_payload["size"], 7)

            updated = tmp_path / "accessed.json"
            access = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "access",
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(updated),
                    "7",
                    "18",
                    "99",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            access_payload = json.loads(access.stdout)
            self.assertEqual(access_payload["hits"], 2)
            self.assertEqual(access_payload["misses"], 1)
            updated_payload = json.loads(updated.read_text())
            self.assertEqual(updated_payload["size"], 7)

    def test_insert_and_delete_cli(self) -> None:
        project_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(project_dir / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            grown = tmp_path / "grown.json"
            insert = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "insert",
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(grown),
                    "11",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(json.loads(insert.stdout)["inserted"])

            pruned = tmp_path / "pruned.json"
            delete = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "delete",
                    "--snapshot",
                    str(grown),
                    "--output",
                    str(pruned),
                    "4",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            delete_payload = json.loads(delete.stdout)
            self.assertTrue(delete_payload["deleted"])
            self.assertNotIn(4, delete_payload["values"])

    def test_trace_cli_exports_diagrams(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            before_dot = tmp_path / "before.dot"
            after_dot = tmp_path / "after.dot"
            before_mermaid = tmp_path / "before.mmd"
            after_mermaid = tmp_path / "after.mmd"
            step_snapshots_dir = tmp_path / "step-snapshots"
            updated = tmp_path / "after.json"
            subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(PROJECT_DIR / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            traced = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "trace",
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(updated),
                    "--before-dot",
                    str(before_dot),
                    "--after-dot",
                    str(after_dot),
                    "--before-mermaid",
                    str(before_mermaid),
                    "--after-mermaid",
                    str(after_mermaid),
                    "--step-snapshots-dir",
                    str(step_snapshots_dir),
                    "7",
                    "18",
                    "99",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(traced.stdout)
            self.assertEqual(len(payload["steps"]), 3)
            self.assertEqual(payload["step_snapshot_count"], 4)
            self.assertTrue(before_dot.exists())
            self.assertTrue(after_dot.exists())
            self.assertTrue(before_mermaid.exists())
            self.assertTrue(after_mermaid.exists())
            self.assertIn('label="before access trace"', before_dot.read_text())
            self.assertIn('label="after access trace"', after_dot.read_text())
            self.assertIn('fillcolor="lightgoldenrod1"', after_dot.read_text())
            self.assertIn("flowchart TD", before_mermaid.read_text())
            self.assertIn("class n18 root;", after_mermaid.read_text())
            self.assertIn("class n7,n18 highlight;", after_mermaid.read_text())
            manifest = json.loads((step_snapshots_dir / "manifest.json").read_text())
            self.assertEqual(manifest["snapshot_count"], 4)
            self.assertEqual(manifest["snapshots"][2]["path"], "02-after-access-18.json")
            self.assertEqual(json.loads((step_snapshots_dir / "01-after-access-7.json").read_text())["structure"]["key"], 7)
            self.assertEqual(json.loads(updated.read_text())["size"], 7)

    def test_benchmark_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            json_output = tmp_path / "artifacts" / "benchmark.json"
            csv_output = tmp_path / "artifacts" / "benchmark.csv"
            benchmark = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "benchmark",
                    "--size",
                    "63",
                    "--hot-set-size",
                    "4",
                    "--hot-queries",
                    "128",
                    "--random-queries",
                    "128",
                    "--seed",
                    "7",
                    "--json-output",
                    str(json_output),
                    "--csv-output",
                    str(csv_output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(benchmark.stdout)
            self.assertEqual(payload["workloads"]["hotset"]["queries"], 128)
            self.assertGreater(payload["takeaway"]["hotset_comparison_gap"], 0)
            self.assertTrue(json_output.exists())
            self.assertTrue(csv_output.exists())
            self.assertEqual(json.loads(json_output.read_text()), payload)
            csv_lines = csv_output.read_text().strip().splitlines()
            self.assertEqual(len(csv_lines), 3)
            self.assertIn("workload", csv_lines[0])
            self.assertIn("hotset", csv_lines[1])
            self.assertIn("uniform_random", csv_lines[2])

    def test_benchmark_series_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            json_output = tmp_path / "artifacts" / "benchmark-series.json"
            csv_output = tmp_path / "artifacts" / "benchmark-series.csv"
            benchmark = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "benchmark-series",
                    "31",
                    "63",
                    "127",
                    "--hot-set-size",
                    "4",
                    "--hot-queries",
                    "64",
                    "--random-queries",
                    "64",
                    "--seed",
                    "5",
                    "--json-output",
                    str(json_output),
                    "--csv-output",
                    str(csv_output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(benchmark.stdout)
            self.assertEqual(payload["sizes"], [31, 63, 127])
            self.assertEqual(len(payload["entries"]), 3)
            self.assertEqual(payload["summary"][0]["seed"], 5)
            self.assertEqual(payload["summary"][2]["seed"], 7)
            self.assertTrue(json_output.exists())
            self.assertTrue(csv_output.exists())
            self.assertEqual(json.loads(json_output.read_text()), payload)
            csv_lines = csv_output.read_text().strip().splitlines()
            self.assertEqual(len(csv_lines), 7)
            self.assertIn("series_index", csv_lines[0])
            self.assertIn("hot_set_ratio", csv_lines[0])
            self.assertIn(",31,5,4,0.129", csv_lines[1])
            self.assertIn(",127,7,4,0.0315", csv_lines[-1])

    def test_split_and_join_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(PROJECT_DIR / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            left_snapshot = tmp_path / "split-left.json"
            right_snapshot = tmp_path / "split-right.json"
            split = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "split",
                    "--snapshot",
                    str(snapshot),
                    "--left-output",
                    str(left_snapshot),
                    "--right-output",
                    str(right_snapshot),
                    "11",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            split_payload = json.loads(split.stdout)
            self.assertEqual(split_payload["left"], [2, 4, 7, 10])
            self.assertEqual(split_payload["right"], [12, 15, 18])
            self.assertIn(split_payload["left_root"], split_payload["left"])
            self.assertIn(split_payload["right_root"], split_payload["right"])
            left_payload = json.loads(left_snapshot.read_text())
            right_payload = json.loads(right_snapshot.read_text())
            self.assertEqual(left_payload["root"], split_payload["left_root"])
            self.assertEqual(right_payload["root"], split_payload["right_root"])
            self.assertEqual(left_payload["values"], [2, 4, 7, 10])
            self.assertEqual(right_payload["values"], [12, 15, 18])

            left_input = tmp_path / "left.txt"
            right_input = tmp_path / "right.txt"
            joined_snapshot = tmp_path / "joined.json"
            left_input.write_text("1\n3\n5\n")
            right_input.write_text("8\n13\n21\n")
            join = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "join",
                    "--left-input",
                    str(left_input),
                    "--right-input",
                    str(right_input),
                    "--output",
                    str(joined_snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            join_payload = json.loads(join.stdout)
            self.assertEqual(join_payload["values"], [1, 3, 5, 8, 13, 21])
            self.assertEqual(json.loads(joined_snapshot.read_text())["size"], 6)

    def test_join_cli_rejects_overlapping_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            left_input = tmp_path / "left.txt"
            right_input = tmp_path / "right.txt"
            joined_snapshot = tmp_path / "joined.json"
            left_input.write_text("1\n5\n9\n")
            right_input.write_text("4\n8\n12\n")
            join = subprocess.run(
                [
                    "python3",
                    str(PROJECT_DIR / "splay_tree_lab.py"),
                    "join",
                    "--left-input",
                    str(left_input),
                    "--right-input",
                    str(right_input),
                    "--output",
                    str(joined_snapshot),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(join.returncode, 2)
            self.assertIn("left values must all be smaller", join.stderr)


if __name__ == "__main__":
    unittest.main()
