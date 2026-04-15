import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from count_min_sketch_lab import CountMinSketch, SpaceSavingSummary, benchmark_memory, build_sketch, load_sketch, save_sketch


PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT = PROJECT_ROOT / 'count_min_sketch_lab.py'


def test_estimates_do_not_underestimate_exact_counts():
    sketch = build_sketch(['apple', 'banana', 'apple', 'carrot', 'apple', 'banana'], epsilon=0.05, delta=0.01)
    assert sketch.estimate('apple') >= 3
    assert sketch.estimate('banana') >= 2
    assert sketch.estimate('missing') == 0


def test_merge_combines_tables_and_observed_items():
    left = build_sketch(['a', 'b', 'a'], epsilon=0.05, delta=0.01, seed=11)
    right = build_sketch(['b', 'c'], epsilon=0.05, delta=0.01, seed=11)
    left.merge(right)
    assert left.total_count == 5
    assert left.estimate('a') >= 2
    assert left.estimate('b') >= 2
    assert {entry['item'] for entry in left.heavy_hitters(2)} == {'a', 'b'}


def test_merge_rejects_incompatible_sketches():
    left = build_sketch(['a'], epsilon=0.05, delta=0.01, seed=1)
    right = build_sketch(['a'], epsilon=0.02, delta=0.01, seed=1)
    with pytest.raises(ValueError):
        left.merge(right)


def test_merge_rejects_different_update_modes():
    left = build_sketch(['a'], epsilon=0.05, delta=0.01, seed=1, conservative_update=False)
    right = build_sketch(['a'], epsilon=0.05, delta=0.01, seed=1, conservative_update=True)
    with pytest.raises(ValueError):
        left.merge(right)


def test_round_trip_json_serialization(tmp_path: Path):
    sketch = build_sketch(
        ['alpha', 'beta', 'alpha'],
        epsilon=0.05,
        delta=0.01,
        seed=3,
        conservative_update=True,
        top_k_capacity=3,
    )
    output = tmp_path / 'sketch.json'
    save_sketch(output, sketch)
    loaded = load_sketch(output)
    assert loaded.total_count == 3
    assert loaded.config.conservative_update is True
    assert loaded.config.top_k_capacity == 3
    assert loaded.estimate('alpha') == sketch.estimate('alpha')
    assert loaded.heavy_hitters(2)[0]['item'] == 'alpha'
    assert loaded.top_k_candidates(1)[0]['item'] == 'alpha'


def test_cli_build_estimate_and_heavy_hitters(tmp_path: Path):
    tokens = tmp_path / 'tokens.txt'
    tokens.write_text('red blue red green red blue', encoding='utf-8')
    sketch_file = tmp_path / 'cms.json'

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            '--epsilon',
            '0.05',
            '--delta',
            '0.01',
            '--conservative-update',
            '--top-k-capacity',
            '3',
            'build',
            str(tokens),
            '--output',
            str(sketch_file),
        ],
        check=True,
    )
    estimate = subprocess.run([sys.executable, str(SCRIPT), 'estimate', str(sketch_file), 'red', 'blue'], check=True, capture_output=True, text=True)
    payload = json.loads(estimate.stdout)
    assert payload['conservative_update'] is True
    assert payload['top_k_capacity'] == 3
    assert payload['estimates']['red'] >= 3
    hitters = subprocess.run([sys.executable, str(SCRIPT), 'heavy-hitters', str(sketch_file), '--threshold', '2'], check=True, capture_output=True, text=True)
    hitters_payload = json.loads(hitters.stdout)
    assert hitters_payload['conservative_update'] is True
    assert hitters_payload['heavy_hitters'][0]['item'] == 'red'


def test_error_bound_tracks_total_count_growth():
    sketch = CountMinSketch(epsilon=0.1, delta=0.05)
    for _ in range(10):
        sketch.add('stream')
    assert sketch.error_bound() == pytest.approx(1.0)


def test_conservative_update_only_increments_minimum_cells():
    standard = CountMinSketch(epsilon=1.0, delta=0.2, conservative_update=False)
    conservative = CountMinSketch(epsilon=1.0, delta=0.2, conservative_update=True)

    standard._index_for = lambda item, row: 0
    conservative._index_for = lambda item, row: 0

    standard.tables = [[5], [1]]
    conservative.tables = [[5], [1]]
    standard.total_count = 6
    conservative.total_count = 6

    standard.add('anchor')
    conservative.add('anchor')

    assert [row[0] for row in standard.tables] == [6, 2]
    assert [row[0] for row in conservative.tables] == [5, 2]
    assert standard.estimate('anchor') == 2
    assert conservative.estimate('anchor') == 2


def test_benchmark_memory_reports_exact_and_sketch_sizes():
    payload = benchmark_memory(
        ['hot'] * 10 + ['warm'] * 5 + ['cold'] * 2,
        epsilon=0.05,
        delta=0.01,
        sample_size=2,
        conservative_update=True,
        top_k_capacity=2,
    )
    assert payload['stream_items'] == 17
    assert payload['unique_items'] == 3
    assert payload['conservative_update'] is True
    assert payload['top_k_capacity'] == 2
    assert payload['exact_counter_bytes'] > 0
    assert payload['sketch_core_bytes'] > 0
    assert len(payload['top_item_estimates']) == 2
    assert payload['top_item_estimates'][0]['item'] == 'hot'
    assert payload['top_item_estimates'][0]['estimate'] >= payload['top_item_estimates'][0]['exact_count']
    assert payload['top_k_candidates'][0]['item'] == 'hot'


def test_cli_benchmark_memory(tmp_path: Path):
    tokens = tmp_path / 'tokens.txt'
    tokens.write_text('alpha beta alpha gamma alpha beta delta', encoding='utf-8')
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            '--epsilon',
            '0.05',
            '--delta',
            '0.01',
            '--conservative-update',
            '--top-k-capacity',
            '3',
            'benchmark-memory',
            str(tokens),
            '--sample-size',
            '3',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['stream_items'] == 7
    assert payload['unique_items'] == 4
    assert payload['conservative_update'] is True
    assert payload['top_k_capacity'] == 3
    assert payload['top_item_estimates'][0]['item'] == 'alpha'
    assert payload['sketch_core_bytes'] <= payload['sketch_full_bytes']
    assert payload['top_k_candidates']


def test_space_saving_summary_replaces_minimum_entry_when_full():
    summary = SpaceSavingSummary(capacity=2)
    summary.add('alpha', 3)
    summary.add('beta', 1)
    summary.add('gamma', 1)

    entries = {entry['item']: entry for entry in summary.top_k()}
    assert 'alpha' in entries
    assert 'gamma' in entries
    assert entries['gamma']['estimate'] == 2
    assert entries['gamma']['error'] == 1


def test_top_k_candidates_track_stream_heavy_hitters():
    sketch = build_sketch(
        ['alpha'] * 8 + ['beta'] * 5 + ['gamma'] * 3 + ['delta'],
        epsilon=0.05,
        delta=0.01,
        top_k_capacity=3,
    )
    candidates = sketch.top_k_candidates(2)
    assert [entry['item'] for entry in candidates] == ['alpha', 'beta']
    assert candidates[0]['cms_estimate'] >= candidates[0]['exact_count']


def test_cli_top_k_reports_summary_candidates(tmp_path: Path):
    tokens = tmp_path / 'tokens.txt'
    tokens.write_text('alpha beta alpha gamma alpha beta alpha delta', encoding='utf-8')
    sketch_file = tmp_path / 'cms.json'

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            '--top-k-capacity',
            '3',
            'build',
            str(tokens),
            '--output',
            str(sketch_file),
        ],
        check=True,
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), 'top-k', str(sketch_file), '--limit', '2'],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload['top_k_capacity'] == 3
    assert [entry['item'] for entry in payload['candidates']] == ['alpha', 'beta']


def test_merge_rebuilds_top_k_summary_from_combined_observed_counts():
    left = build_sketch(['alpha'] * 4 + ['beta'] * 2, epsilon=0.05, delta=0.01, seed=1, top_k_capacity=2)
    right = build_sketch(['beta'] * 5 + ['gamma'], epsilon=0.05, delta=0.01, seed=1, top_k_capacity=2)
    left.merge(right)

    candidates = left.top_k_candidates(2)
    assert [entry['item'] for entry in candidates] == ['beta', 'alpha']
    assert candidates[0]['exact_count'] == 7


def test_merge_rejects_different_top_k_capacity():
    left = build_sketch(['a'], epsilon=0.05, delta=0.01, seed=1, top_k_capacity=2)
    right = build_sketch(['a'], epsilon=0.05, delta=0.01, seed=1, top_k_capacity=3)
    with pytest.raises(ValueError):
        left.merge(right)
