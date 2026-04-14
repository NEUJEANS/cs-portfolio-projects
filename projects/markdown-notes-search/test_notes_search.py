import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from notes_search import index_notes, search_notes


class NotesSearchTests(unittest.TestCase):
    def test_index_notes_merges_inline_and_front_matter_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'algorithms.md').write_text(
                '---\ntags: [graphs, cli]\n---\n# Search Notes\nStudy #graphs and #ranking ideas.',
                encoding='utf-8',
            )

            notes = index_notes(root)

            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]['path'], 'algorithms.md')
            self.assertEqual(notes[0]['tags'], ['cli', 'graphs', 'ranking'])

    def test_search_notes_ranks_exact_tag_and_filename_matches_highest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'graphs.md').write_text('#graphs shortest path notes', encoding='utf-8')
            (root / 'algorithms.md').write_text('Graphs appear here in the body only.', encoding='utf-8')
            (root / 'references.md').write_text('A graphs comparison and more graphs.', encoding='utf-8')

            results = search_notes(index_notes(root), 'graphs')

            self.assertEqual([result['path'] for result in results], ['graphs.md', 'references.md', 'algorithms.md'])
            self.assertIn('#graphs', ' '.join('#' + tag for tag in results[0]['tags']))
            self.assertTrue(results[1]['score'] >= results[2]['score'])

    def test_front_matter_is_not_included_in_search_snippets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'scheduler.md').write_text(
                '---\ntags: [os, planning]\n---\nRound robin scheduling notes for exams.',
                encoding='utf-8',
            )

            result = search_notes(index_notes(root), 'round')[0]

            self.assertIn('Round robin', result['snippet'])
            self.assertNotIn('tags:', result['snippet'])

    def test_recursive_search_and_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / 'school' / 'systems'
            nested.mkdir(parents=True)
            (nested / 'scheduler.md').write_text('round robin #os', encoding='utf-8')
            (root / 'root.md').write_text('round robin introduction', encoding='utf-8')

            notes = index_notes(root, recursive=True)
            results = search_notes(notes, 'round', limit=1)

            self.assertEqual({note['path'] for note in notes}, {'root.md', 'school/systems/scheduler.md'})
            self.assertEqual(len(results), 1)
            self.assertIn('round', results[0]['snippet'].lower())

    def test_search_notes_rejects_non_positive_limit_and_empty_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'db.md').write_text('Index tuning for #sql search.', encoding='utf-8')
            notes = index_notes(root)

            self.assertEqual(search_notes(notes, '   '), [])
            with self.assertRaises(ValueError):
                search_notes(notes, 'sql', limit=0)

    def test_boolean_and_phrase_queries_filter_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text('distributed systems lecture notes with quorum reads', encoding='utf-8')
            (root / 'databases.md').write_text('distributed databases and consensus patterns', encoding='utf-8')
            (root / 'reading.md').write_text('systems design reading list', encoding='utf-8')

            results = search_notes(index_notes(root), 'distributed AND systems')
            phrase_results = search_notes(index_notes(root), '"systems design"')

            self.assertEqual([result['path'] for result in results], ['systems.md'])
            self.assertEqual([result['path'] for result in phrase_results], ['reading.md'])
            self.assertIn('systems design', phrase_results[0]['snippet'].lower())

    def test_boolean_parentheses_and_not_work_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'graphs.md').write_text('graph shortest path notes', encoding='utf-8')
            (root / 'trees.md').write_text('tree traversal notes', encoding='utf-8')
            (root / 'draft.md').write_text('graph draft and archived notes', encoding='utf-8')

            results = search_notes(index_notes(root), '(graph OR tree) AND NOT archived')

            self.assertEqual([result['path'] for result in results], ['graphs.md', 'trees.md'])

    def test_invalid_boolean_query_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'notes.md').write_text('hello world', encoding='utf-8')
            notes = index_notes(root)

            with self.assertRaises(ValueError):
                search_notes(notes, 'graph AND (tree OR')

    def test_negative_only_query_returns_non_excluded_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'active.md').write_text('systems notes', encoding='utf-8')
            (root / 'archived.md').write_text('archived systems notes', encoding='utf-8')

            results = search_notes(index_notes(root), 'NOT archived')

            self.assertEqual([result['path'] for result in results], ['active.md'])
            self.assertGreaterEqual(results[0]['score'], 1)

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'db.md').write_text('Index tuning for #sql search.', encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    'notes_search.py',
                    str(root),
                    'sql',
                    '--json',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload[0]['path'], 'db.md')
            self.assertEqual(payload[0]['tags'], ['sql'])
            self.assertIn('sql', payload[0]['snippet'].lower())

    def test_plain_cli_output_includes_score_tags_and_snippet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'planner.md').write_text('Use #planning notes for semester planning.', encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    'notes_search.py',
                    str(root),
                    'planning',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            output = completed.stdout.strip()
            self.assertIn('planner.md', output)
            self.assertIn('score=', output)
            self.assertIn('#planning', output)
            self.assertIn('semester planning', output)


if __name__ == '__main__':
    unittest.main()
