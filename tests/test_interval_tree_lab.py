import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

MODULE_PATH = pathlib.Path("projects/interval-tree-lab/interval_tree_lab.py")
spec = importlib.util.spec_from_file_location("interval_tree_lab", MODULE_PATH)
interval_tree_lab = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = interval_tree_lab
spec.loader.exec_module(interval_tree_lab)

Interval = interval_tree_lab.Interval
IntervalTree = interval_tree_lab.IntervalTree
parse_interval_spec = interval_tree_lab.parse_interval_spec


class IntervalTreeLabTests(unittest.TestCase):
    def test_build_balanced_tree_and_validate(self) -> None:
        tree = IntervalTree(
            [
                Interval(15, 23, "analytics"),
                Interval(5, 8, "backup"),
                Interval(17, 19, "alerts"),
                Interval(6, 10, "deploy"),
                Interval(8, 9, "qa"),
            ]
        )
        valid, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), sorted(tree.inorder()))
        self.assertEqual(tree.root.max_end, 23)
        self.assertLessEqual(tree.height(), 3)

    def test_find_any_and_all_overlaps(self) -> None:
        tree = IntervalTree(
            [
                Interval(0, 3, "warmup"),
                Interval(5, 8, "backup"),
                Interval(6, 10, "deploy"),
                Interval(8, 9, "qa"),
                Interval(15, 23, "analytics"),
                Interval(17, 19, "alerts"),
            ]
        )
        query = Interval(7, 18)
        any_hit = tree.find_any_overlap(query)
        self.assertIsNotNone(any_hit)
        overlaps = tree.find_overlaps(query)
        self.assertEqual(
            [interval.label for interval in overlaps],
            ["backup", "deploy", "qa", "analytics", "alerts"],
        )

    def test_point_query_and_insert_reject_duplicate(self) -> None:
        tree = IntervalTree([Interval(25, 30, "etl"), Interval(26, 26, "ping")])
        self.assertTrue(tree.insert(Interval(19, 20, "maintenance")))
        self.assertFalse(tree.insert(Interval(19, 20, "maintenance")))
        hits = tree.find_point(26)
        self.assertEqual([interval.label for interval in hits], ["etl", "ping"])
        valid, errors = tree.validate()
        self.assertTrue(valid, errors)

    def test_parse_interval_spec(self) -> None:
        parsed = parse_interval_spec("5-8:backup")
        self.assertEqual(parsed, Interval(5, 8, "backup"))
        without_label = parse_interval_spec("3-3")
        self.assertEqual(without_label, Interval(3, 3, None))
        with self.assertRaises(ValueError):
            parse_interval_spec("9-4:broken")

    def test_cli_overlap_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "overlap",
                "7-18",
                "0-3:warmup",
                "5-8:backup",
                "6-10:deploy",
                "15-23:analytics",
                "17-19:alerts",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["query"], {"start": 7, "end": 18})
        self.assertEqual(
            [entry.get("label") for entry in payload["all_overlaps"]],
            ["backup", "deploy", "analytics", "alerts"],
        )


if __name__ == "__main__":
    unittest.main()
