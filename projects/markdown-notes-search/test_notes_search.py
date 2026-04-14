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
