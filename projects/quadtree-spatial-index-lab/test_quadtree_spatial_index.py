import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from quadtree_spatial_index import Point, Quadtree, Rectangle, build_quadtree, load_points

SCRIPT_PATH = PROJECT_DIR / "quadtree_spatial_index.py"
SAMPLE_PATH = PROJECT_DIR / "sample_points.json"


def make_tree() -> Quadtree:
    points = [
        Point(2, 8, "library"),
        Point(6, 7, "lab"),
        Point(8, 9, "cafe"),
        Point(1, 2, "gym"),
        Point(4, 4, "dorm"),
        Point(7, 3, "bus-stop"),
        Point(9, 1, "park"),
    ]
    return build_quadtree(points, Rectangle(0, 0, 10, 10), capacity=2, max_depth=6)


class QuadtreeSpatialIndexTests(unittest.TestCase):
    def test_insert_rejects_points_outside_boundary(self) -> None:
        tree = Quadtree(Rectangle(0, 0, 5, 5))
        self.assertTrue(tree.insert(Point(2, 2, "inside")))
        self.assertFalse(tree.insert(Point(10, 10, "outside")))

    def test_range_query_returns_expected_points(self) -> None:
        tree = make_tree()
        labels = sorted(point.label for point in tree.range_query(Rectangle(0, 0, 5, 5)))
        self.assertEqual(labels, ["dorm", "gym"])

    def test_range_query_handles_split_boundaries_without_duplicates(self) -> None:
        tree = build_quadtree(
            [Point(5, 5, "center"), Point(5, 8, "north"), Point(8, 5, "east")],
            Rectangle(0, 0, 10, 10),
            capacity=1,
            max_depth=4,
        )
        labels = [point.label for point in tree.range_query(Rectangle(5, 5, 8, 8))]
        self.assertEqual(sorted(labels), ["center", "east", "north"])
        self.assertEqual(len(labels), len(set(labels)))

    def test_nearest_neighbor_returns_closest_point(self) -> None:
        tree = make_tree()
        nearest = tree.nearest_neighbor(Point(6.2, 2.5))
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.label, "bus-stop")

    def test_nearest_neighbor_returns_none_for_empty_tree(self) -> None:
        tree = Quadtree(Rectangle(0, 0, 10, 10))
        self.assertIsNone(tree.nearest_neighbor(Point(1, 1)))

    def test_stats_report_counts_after_subdivision(self) -> None:
        tree = make_tree()
        self.assertEqual(tree.point_count(), 7)
        self.assertGreaterEqual(tree.node_count(), 5)
        self.assertGreaterEqual(tree.max_observed_depth(), 1)

    def test_build_quadtree_raises_for_out_of_bounds_points(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside boundary"):
            build_quadtree([Point(11, 0)], Rectangle(0, 0, 10, 10))

    def test_load_points_requires_json_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = Path(temp_dir) / "bad.json"
            payload.write_text(json.dumps({"x": 1, "y": 2}))
            with self.assertRaisesRegex(ValueError, "JSON list"):
                load_points(payload)

    def test_cli_range_query_outputs_matches(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(SAMPLE_PATH),
                "--boundary",
                "0",
                "0",
                "10",
                "10",
                "range",
                "--area",
                "0",
                "0",
                "5",
                "5",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        labels = sorted(item["label"] for item in payload["matches"])
        self.assertEqual(labels, ["dorm", "gym"])

    def test_cli_nearest_query_outputs_point(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(SAMPLE_PATH),
                "--boundary",
                "0",
                "0",
                "10",
                "10",
                "nearest",
                "--target",
                "8.4",
                "8.5",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["nearest"]["label"], "cafe")

    def test_cli_stats_outputs_tree_shape(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(SAMPLE_PATH),
                "--boundary",
                "0",
                "0",
                "10",
                "10",
                "--capacity",
                "2",
                "stats",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["points"], 7)
        self.assertGreaterEqual(payload["nodes"], 5)


if __name__ == "__main__":
    unittest.main()
