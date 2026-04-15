import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from autocomplete import (
    DatasetError,
    benchmark_to_dict,
    build_trie,
    format_benchmark_report,
    format_query_result,
    format_suggestions,
    load_entries,
    load_queries,
    normalize_query,
    run_query,
)


class AutocompleteTests(unittest.TestCase):
    def test_load_entries_rejects_invalid_word(self):
        with self.assertRaises(DatasetError):
            load_entries(['hello-world,5'])

    def test_load_entries_skips_comment_lines(self):
        entries = load_entries(['# sample dictionary', 'apple,10', '', 'apply,8'])
        self.assertEqual(entries, [('apple', 10), ('apply', 8)])

    def test_load_queries_skips_comment_lines(self):
        queries = load_queries(['# batch benchmark', 'apple', '', 'apply'])
        self.assertEqual(queries, ['apple', 'apply'])

    def test_normalize_query_rejects_non_letters(self):
        with self.assertRaises(DatasetError):
            normalize_query('app123')

    def test_prefix_search_returns_weighted_top_k(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
            ('aptitude', 61),
        ])
        result = trie.top_k_prefix('app', 2)
        self.assertEqual([item.word for item in result], ['apple', 'application'])

    def test_duplicate_words_keep_highest_weight(self):
        trie = build_trie([
            ('apple', 10),
            ('apple', 25),
            ('apply', 20),
        ])
        result = trie.top_k_prefix('app', 2)
        self.assertEqual([(item.word, item.weight) for item in result], [('apple', 25), ('apply', 20)])
        self.assertEqual(trie.word_count, 2)

    def test_prefix_search_explain_stats_capture_pruning(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
            ('aptitude', 61),
            ('banana', 40),
        ])
        result, stats = trie.top_k_prefix('a', 2, collect_stats=True)
        self.assertEqual([item.word for item in result], ['apple', 'application'])
        self.assertGreater(stats.nodes_visited, 0)
        self.assertGreater(stats.terminals_considered, 0)
        self.assertGreater(stats.candidate_updates, 0)
        self.assertGreaterEqual(stats.branches_pruned, 1)

    def test_fuzzy_search_ranks_distance_before_weight(self):
        trie = build_trie([
            ('apple', 100),
            ('apply', 90),
            ('ape', 95),
        ])
        result = trie.fuzzy_search('aple', limit=3, max_distance=1)
        self.assertEqual(result[0].word, 'apple')
        self.assertEqual(result[0].distance, 1)

    def test_run_query_records_timings_and_filters_duplicate_fuzzy_hits(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
        ])
        result = run_query(trie, 'app', limit=3, max_distance=1)
        self.assertTrue(result.prefix_time_ms >= 0)
        self.assertTrue(result.fuzzy_time_ms >= 0)
        self.assertEqual([item.word for item in result.prefix_matches], ['apple', 'application', 'apply'])
        self.assertEqual(result.fuzzy_matches, [])

    def test_run_query_explain_populates_stats(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
            ('banana', 40),
        ])
        result = run_query(trie, 'aple', limit=3, max_distance=1, explain=True)
        self.assertIsNotNone(result.prefix_stats)
        self.assertIsNotNone(result.fuzzy_stats)
        self.assertGreater(result.fuzzy_stats.dynamic_programming_rows, 0)
        self.assertGreaterEqual(result.fuzzy_stats.branches_pruned, 0)

    def test_format_suggestions_handles_empty_sections(self):
        rendered = format_suggestions([], [])
        self.assertIn('exact_prefix_matches:', rendered)
        self.assertIn('fuzzy_matches:', rendered)
        self.assertIn('- none', rendered)

    def test_format_query_result_includes_explain_block(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
        ])
        result = run_query(trie, 'aple', limit=3, max_distance=1, explain=True)
        rendered = format_query_result(result, explain=True)
        self.assertIn('search_explanation:', rendered)
        self.assertIn('branches_pruned_by_weight:', rendered)
        self.assertIn('branches_pruned_by_distance:', rendered)

    def test_benchmark_helpers_render_summary(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
            ('banana', 40),
        ])
        results = [run_query(trie, 'app', 3, 1), run_query(trie, 'aple', 3, 1)]
        report = format_benchmark_report(results, trie)
        self.assertIn('benchmark_summary:', report)
        self.assertIn('per_query_top_hits:', report)

        payload = benchmark_to_dict(results, trie)
        self.assertEqual(payload['query_count'], 2)
        self.assertEqual(payload['indexed_words'], 4)
        self.assertEqual(len(payload['results']), 2)

    def test_benchmark_helpers_include_aggregate_explain_stats(self):
        trie = build_trie([
            ('apple', 100),
            ('application', 92),
            ('apply', 87),
            ('banana', 40),
        ])
        results = [run_query(trie, 'app', 3, 1, explain=True), run_query(trie, 'aple', 3, 1, explain=True)]
        report = format_benchmark_report(results, trie, explain=True)
        self.assertIn('total_prefix_nodes_visited:', report)
        self.assertIn('total_fuzzy_dp_rows:', report)

        payload = benchmark_to_dict(results, trie)
        self.assertIn('aggregate_stats', payload)
        self.assertGreater(payload['aggregate_stats']['fuzzy_dynamic_programming_rows'], 0)

    def test_cli_outputs_query_sections(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as handle:
            handle.write(textwrap.dedent('''\
                apple,100
                application,92
                apply,87
                banana,40
            '''))
            dataset_path = handle.name

        completed = subprocess.run(
            [
                sys.executable,
                str(project_dir / 'autocomplete.py'),
                dataset_path,
                'aple',
                '--limit',
                '3',
                '--max-distance',
                '1',
            ],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('query: aple', completed.stdout)
        self.assertIn('exact_prefix_matches:', completed.stdout)
        self.assertIn('fuzzy_matches:', completed.stdout)
        self.assertIn('prefix_time_ms:', completed.stdout)

    def test_cli_explain_outputs_search_diagnostics(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as handle:
            handle.write(textwrap.dedent('''\
                apple,100
                application,92
                apply,87
                banana,40
            '''))
            dataset_path = handle.name

        completed = subprocess.run(
            [
                sys.executable,
                str(project_dir / 'autocomplete.py'),
                dataset_path,
                'aple',
                '--limit',
                '3',
                '--max-distance',
                '1',
                '--explain',
            ],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('search_explanation:', completed.stdout)
        self.assertIn('branches_pruned_by_distance:', completed.stdout)

    def test_cli_batch_json_mode_outputs_summary(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as dataset_handle:
            dataset_handle.write(textwrap.dedent('''\
                apple,100
                application,92
                apply,87
                banana,40
            '''))
            dataset_path = dataset_handle.name
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as query_handle:
            query_handle.write('app\naple\n')
            query_path = query_handle.name

        completed = subprocess.run(
            [
                sys.executable,
                str(project_dir / 'autocomplete.py'),
                dataset_path,
                '--batch-file',
                query_path,
                '--limit',
                '3',
                '--max-distance',
                '1',
                '--json',
            ],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload['query_count'], 2)
        self.assertEqual(payload['indexed_words'], 4)
        self.assertEqual(len(payload['results']), 2)

    def test_cli_batch_json_explain_mode_outputs_stats(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as dataset_handle:
            dataset_handle.write(textwrap.dedent('''\
                apple,100
                application,92
                apply,87
                banana,40
            '''))
            dataset_path = dataset_handle.name
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as query_handle:
            query_handle.write('app\naple\n')
            query_path = query_handle.name

        completed = subprocess.run(
            [
                sys.executable,
                str(project_dir / 'autocomplete.py'),
                dataset_path,
                '--batch-file',
                query_path,
                '--limit',
                '3',
                '--max-distance',
                '1',
                '--json',
                '--explain',
            ],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn('aggregate_stats', payload)
        self.assertIn('prefix_stats', payload['results'][0])
        self.assertIn('fuzzy_stats', payload['results'][0])

    def test_cli_rejects_query_and_batch_file_together(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as dataset_handle:
            dataset_handle.write('apple,10\n')
            dataset_path = dataset_handle.name
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as query_handle:
            query_handle.write('apple\n')
            query_path = query_handle.name

        completed = subprocess.run(
            [
                sys.executable,
                str(project_dir / 'autocomplete.py'),
                dataset_path,
                'apple',
                '--batch-file',
                query_path,
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn('provide exactly one of QUERY or --batch-file', completed.stderr)


if __name__ == '__main__':
    unittest.main()
