import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from autocomplete import DatasetError, build_trie, format_suggestions, load_entries, normalize_query


class AutocompleteTests(unittest.TestCase):
    def test_load_entries_rejects_invalid_word(self):
        with self.assertRaises(DatasetError):
            load_entries(['hello-world,5'])


    def test_load_entries_skips_comment_lines(self):
        entries = load_entries(['# sample dictionary', 'apple,10', '', 'apply,8'])
        self.assertEqual(entries, [('apple', 10), ('apply', 8)])

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

    def test_fuzzy_search_ranks_distance_before_weight(self):
        trie = build_trie([
            ('apple', 100),
            ('apply', 90),
            ('ape', 95),
        ])
        result = trie.fuzzy_search('aple', limit=3, max_distance=1)
        self.assertEqual(result[0].word, 'apple')
        self.assertEqual(result[0].distance, 1)

    def test_format_suggestions_handles_empty_sections(self):
        rendered = format_suggestions([], [])
        self.assertIn('exact_prefix_matches:', rendered)
        self.assertIn('fuzzy_matches:', rendered)
        self.assertIn('- none', rendered)

    def test_cli_outputs_prefix_and_fuzzy_sections(self):
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
        self.assertIn('exact_prefix_matches:', completed.stdout)
        self.assertIn('fuzzy_matches:', completed.stdout)
        self.assertIn('apple', completed.stdout)


if __name__ == '__main__':
    unittest.main()
