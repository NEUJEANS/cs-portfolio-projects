import json
import subprocess
import sys
from pathlib import Path

import pytest

from kd_tree_spatial_search import KDTree, Point, load_points, main


FIXTURE_PATH = Path(__file__).with_name("sample_points.json")


def sample_tree() -> KDTree:
    return KDTree(load_points(FIXTURE_PATH))


def test_range_query_returns_points_inside_rectangle_in_sorted_order():
    matches = sample_tree().range_query(1, 2, 6, 7)
    assert matches == [Point(2.0, 3.0, "a"), Point(4.0, 7.0, "d"), Point(5.0, 4.0, "b")]


def test_nearest_neighbor_finds_closest_point():
    nearest = sample_tree().nearest_neighbor(8.2, 1.1)
    assert nearest == Point(8.0, 1.0, "e")


def test_nearest_neighbor_breaks_distance_ties_deterministically():
    tree = KDTree([Point(0, 0, "left"), Point(2, 0, "right")])
    assert tree.nearest_neighbor(1, 0) == Point(0, 0, "left")


def test_invalid_range_query_raises():
    with pytest.raises(ValueError):
        sample_tree().range_query(5, 1, 4, 2)


def test_load_points_rejects_non_list_json(tmp_path: Path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"x": 1}')
    with pytest.raises(ValueError):
        load_points(bad_path)


def test_cli_nearest_outputs_json():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("kd_tree_spatial_search.py")), str(FIXTURE_PATH), "nearest", "7.8", "1.2"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["nearest"]["label"] == "e"


def test_cli_range_outputs_match_count(capsys):
    exit_code = main([str(FIXTURE_PATH), "range", "0", "0", "5", "5"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["count"] == 2
    assert [item["label"] for item in payload["matches"]] == ["a", "b"]
