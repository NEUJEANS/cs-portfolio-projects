import json
import subprocess
import sys
from pathlib import Path

import pytest

from kd_tree_spatial_search import (
    KDTree,
    Point,
    benchmark_nearest_search,
    brute_force_k_nearest,
    brute_force_radius,
    load_points,
    main,
)


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


def test_k_nearest_neighbors_match_brute_force_ordering():
    points = load_points(FIXTURE_PATH)
    tree = KDTree(points)
    assert tree.k_nearest_neighbors(7.0, 2.0, 3) == brute_force_k_nearest(points, 7.0, 2.0, 3)


def test_k_nearest_neighbor_caps_at_dataset_size():
    points = [Point(0, 0, "a"), Point(3, 4, "b")]
    tree = KDTree(points)
    assert tree.k_nearest_neighbors(0, 0, 10) == [Point(0, 0, "a"), Point(3, 4, "b")]


def test_radius_query_matches_brute_force_ordering():
    points = load_points(FIXTURE_PATH)
    tree = KDTree(points)
    assert tree.radius_query(7.0, 2.0, 3.0) == brute_force_radius(points, 7.0, 2.0, 3.0)


def test_radius_query_supports_optional_limit():
    matches = sample_tree().radius_query(7.0, 2.0, 3.0, limit=2)
    assert matches == [Point(7.0, 2.0, "f"), Point(8.0, 1.0, "e")]


def test_k_nearest_supports_duplicate_points_without_heap_comparison_errors():
    points = [Point(1, 1, "dup"), Point(1, 1, "dup"), Point(2, 2, "other")]
    tree = KDTree(points)
    matches = tree.k_nearest_neighbors(1, 1, 2)
    assert matches == [Point(1, 1, "dup"), Point(1, 1, "dup")]


def test_invalid_range_query_raises():
    with pytest.raises(ValueError):
        sample_tree().range_query(5, 1, 4, 2)


def test_radius_query_rejects_negative_radius_and_non_positive_limit():
    tree = sample_tree()
    with pytest.raises(ValueError):
        tree.radius_query(7.0, 2.0, -0.1)
    with pytest.raises(ValueError):
        tree.radius_query(7.0, 2.0, 1.0, limit=0)


def test_load_points_rejects_non_list_json(tmp_path: Path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"x": 1}')
    with pytest.raises(ValueError):
        load_points(bad_path)


def test_k_nearest_rejects_non_positive_k():
    with pytest.raises(ValueError):
        sample_tree().k_nearest_neighbors(1, 1, 0)


def test_benchmark_matches_brute_force_and_reports_speedup():
    report = benchmark_nearest_search(load_points(FIXTURE_PATH), query_count=12, k=2, seed=7)
    assert report["query_count"] == 12
    assert report["k"] == 2
    assert report["speedup"] is None or report["speedup"] > 0


def test_cli_nearest_outputs_json():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("kd_tree_spatial_search.py")), str(FIXTURE_PATH), "nearest", "7.8", "1.2"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["nearest"]["label"] == "e"


def test_cli_knearest_outputs_ranked_matches():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("kd_tree_spatial_search.py")), str(FIXTURE_PATH), "knearest", "7", "2", "3"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["count"] == 3
    assert [item["label"] for item in payload["matches"]] == ["f", "e", "b"]


def test_cli_range_outputs_match_count(capsys):
    exit_code = main([str(FIXTURE_PATH), "range", "0", "0", "5", "5"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["count"] == 2
    assert [item["label"] for item in payload["matches"]] == ["a", "b"]


def test_cli_radius_outputs_distance_sorted_matches(capsys):
    exit_code = main([str(FIXTURE_PATH), "radius", "7", "2", "3", "--limit", "2"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["count"] == 2
    assert [item["label"] for item in payload["matches"]] == ["f", "e"]
    assert payload["matches"][0]["distance"] == 0.0


def test_cli_benchmark_outputs_summary(capsys):
    exit_code = main([str(FIXTURE_PATH), "benchmark", "--queries", "8", "--k", "2", "--seed", "5"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["query_count"] == 8
    assert payload["k"] == 2
