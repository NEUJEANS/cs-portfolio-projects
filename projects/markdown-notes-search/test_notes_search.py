import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from notes_search import (
    DEFAULT_INDEX_FILENAME,
    INDEX_VERSION,
    build_editor_command,
    build_preview_lines,
    export_results,
    index_notes,
    search_notes,
    selected_or_current_results,
    selection_label,
    summarize_result_line,
    truncate_for_width,
)


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
            self.assertEqual(notes[0]['headings'], ['Search Notes'])

    def test_index_notes_writes_and_reuses_persistent_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note_path = root / 'algorithms.md'
            note_path.write_text('Graph search #graphs', encoding='utf-8')

            notes = index_notes(root, index_file='index.json')
            cache_path = root / 'index.json'
            cache_payload = json.loads(cache_path.read_text(encoding='utf-8'))

            self.assertEqual(notes[0]['path'], 'algorithms.md')
            self.assertEqual(cache_payload['version'], INDEX_VERSION)
            self.assertIn('algorithms.md', cache_payload['entries'])

            cached_entry = cache_payload['entries']['algorithms.md']
            time.sleep(0.002)
            note_path.unlink()
            note_path.write_text('Updated graph search #graphs #updated', encoding='utf-8')
            os.utime(note_path, None)

            refreshed_notes = index_notes(root, index_file='index.json')
            refreshed_payload = json.loads(cache_path.read_text(encoding='utf-8'))

            self.assertEqual(refreshed_notes[0]['tags'], ['graphs', 'updated'])
            self.assertNotEqual(cached_entry['source']['mtime_ns'], refreshed_payload['entries']['algorithms.md']['source']['mtime_ns'])

    def test_index_notes_removes_deleted_files_from_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / 'keep.md'
            drop = root / 'drop.md'
            keep.write_text('keep me', encoding='utf-8')
            drop.write_text('remove me', encoding='utf-8')

            index_notes(root, index_file='index.json')
            drop.unlink()
            notes = index_notes(root, index_file='index.json')
            payload = json.loads((root / 'index.json').read_text(encoding='utf-8'))

            self.assertEqual([note['path'] for note in notes], ['keep.md'])
            self.assertEqual(sorted(payload['entries']), ['keep.md'])

    def test_rebuild_index_discards_stale_cache_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text('distributed systems', encoding='utf-8')
            cache_path = root / 'index.json'
            cache_path.write_text(
                json.dumps({'version': 1, 'entries': {'ghost.md': {'path': 'ghost.md', 'source': {'mtime_ns': 1, 'size': 1}}}}),
                encoding='utf-8',
            )

            notes = index_notes(root, index_file='index.json', rebuild_index=True)
            payload = json.loads(cache_path.read_text(encoding='utf-8'))

            self.assertEqual([note['path'] for note in notes], ['systems.md'])
            self.assertEqual(sorted(payload['entries']), ['systems.md'])
            self.assertEqual(payload['version'], INDEX_VERSION)

    def test_invalid_cache_json_is_treated_as_empty_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text('distributed systems', encoding='utf-8')
            (root / 'index.json').write_text('{not valid json', encoding='utf-8')

            notes = index_notes(root, index_file='index.json')
            payload = json.loads((root / 'index.json').read_text(encoding='utf-8'))

            self.assertEqual([note['path'] for note in notes], ['systems.md'])
            self.assertEqual(sorted(payload['entries']), ['systems.md'])

    def test_index_notes_can_write_nested_index_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text('distributed systems', encoding='utf-8')

            index_notes(root, index_file='cache/index.json')

            self.assertTrue((root / 'cache' / 'index.json').exists())

    def test_section_indexing_builds_unique_heading_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text(
                '# Distributed Systems\nOverview\n## Failure Detection\nTimeout notes\n## Failure Detection\nPhi accrual',
                encoding='utf-8',
            )

            notes = index_notes(root)

            self.assertEqual(
                notes[0]['sections'],
                [
                    {'level': 1, 'heading': 'Distributed Systems', 'anchor': 'distributed-systems', 'start_line': 1, 'content': 'Overview'},
                    {'level': 2, 'heading': 'Failure Detection', 'anchor': 'failure-detection', 'start_line': 3, 'content': 'Timeout notes'},
                    {'level': 2, 'heading': 'Failure Detection', 'anchor': 'failure-detection-1', 'start_line': 5, 'content': 'Phi accrual'},
                ],
            )

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

    def test_heading_matches_rank_above_body_only_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'distributed-overview.md').write_text('# Distributed Systems\nQuick notes.', encoding='utf-8')
            (root / 'reference.md').write_text('distributed systems appear here in the body only', encoding='utf-8')

            results = search_notes(index_notes(root), 'distributed systems')

            self.assertEqual([result['path'] for result in results], ['distributed-overview.md', 'reference.md'])
            self.assertEqual(results[0]['snippet'], 'Heading: Distributed Systems')

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

    def test_search_results_include_best_matching_section_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text(
                '# Distributed Systems\nOverview\n## Failure Detection\nHeartbeat timeout and phi accrual notes.',
                encoding='utf-8',
            )

            result = search_notes(index_notes(root), 'phi accrual')[0]

            self.assertEqual(result['section_match']['path_with_anchor'], 'systems.md#failure-detection')
            self.assertEqual(result['section_match']['line_number'], 3)
            self.assertIn('Failure Detection (#failure-detection)', result['snippet'])

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

    def test_index_notes_builds_backlinks_for_wikilinks_and_markdown_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'hub.md').write_text('See [[topic]] and [details](topic.md).', encoding='utf-8')
            (root / 'topic.md').write_text('# Topic\nKnowledge base entry.', encoding='utf-8')

            notes = {note['path']: note for note in index_notes(root)}
            results = search_notes(list(notes.values()), 'hub')

            self.assertEqual(notes['hub.md']['outgoing_links'], ['topic'])
            self.assertEqual(notes['topic.md']['backlinks'], ['hub.md'])
            self.assertEqual(results[0]['path'], 'hub.md')
            self.assertEqual(results[1]['path'], 'topic.md')
            self.assertEqual(results[1]['snippet'], 'Backlinked from: hub.md')

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'db.md').write_text('# SQL\nIndex tuning for #sql search.', encoding='utf-8')
            (root / 'hub.md').write_text('See [[db]].', encoding='utf-8')

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
            self.assertEqual(payload[0]['headings'], ['SQL'])
            self.assertIn('sql', payload[0]['snippet'].lower())

    def test_cli_json_output_includes_section_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'db.md').write_text('# SQL\n## Covering Indexes\nIndex tuning for #sql search.', encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    'notes_search.py',
                    str(root),
                    'covering',
                    '--json',
                ],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload[0]['section_match']['path_with_anchor'], 'db.md#covering-indexes')
            self.assertEqual(payload[0]['sections'][1]['anchor'], 'covering-indexes')

    def test_build_editor_command_uses_line_aware_presets(self):
        note = {
            'path': 'systems.md',
            'section_match': {'path': 'systems.md', 'path_with_anchor': 'systems.md#failure-detection', 'line_number': 12},
        }

        vscode_command = build_editor_command(note, editor='code --reuse-window', base_directory='/tmp/notes')
        vim_command = build_editor_command(note, editor='vim', base_directory='/tmp/notes')

        self.assertEqual(vscode_command[:2], ['code', '--reuse-window'])
        self.assertEqual(vscode_command[2], '--goto')
        self.assertTrue(vscode_command[3].endswith('/tmp/notes/systems.md:12'))
        self.assertEqual(vim_command[0], 'vim')
        self.assertEqual(vim_command[1], '+12')
        self.assertTrue(vim_command[2].endswith('/tmp/notes/systems.md'))

    def test_cli_json_output_includes_editor_command_and_line_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text(
                '# Distributed Systems\nOverview\n## Failure Detection\nHeartbeat timeout and phi accrual notes.',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    'notes_search.py',
                    str(root),
                    'phi accrual',
                    '--json',
                    '--editor',
                    'code',
                ],
                cwd=Path(__file__).resolve().parent,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)

            self.assertEqual(payload[0]['section_match']['line_number'], 3)
            self.assertEqual(payload[0]['open_command'][0], 'code')
            self.assertEqual(payload[0]['open_command'][1], '--goto')
            self.assertTrue(payload[0]['open_command'][2].endswith('systems.md:3'))

    def test_tui_helpers_build_preview_and_result_summary(self):
        note = {
            'path': 'systems/distributed.md',
            'score': 166,
            'tags': ['distributed', 'systems', 'review'],
            'snippet': 'Failure Detection (#failure-detection): Heartbeat timeout and phi accrual notes.',
            'backlinks': ['hub.md'],
            'section_match': {
                'heading': 'Failure Detection',
                'path_with_anchor': 'systems/distributed.md#failure-detection',
                'line_number': 7,
            },
        }

        summary = summarize_result_line(note, 48)
        preview_lines = build_preview_lines(note, 32)

        self.assertLessEqual(len(summary), 48)
        self.assertIn('systems/distributed.md', summary)
        self.assertTrue(any('section:' in line for line in preview_lines))
        self.assertTrue(any('backlinks:' in line for line in preview_lines))
        self.assertTrue(any('phi accrual' in line.lower() for line in preview_lines))

    def test_truncate_for_width_uses_ellipsis(self):
        self.assertEqual(truncate_for_width('abcdef', 4), 'abc…')
        self.assertEqual(truncate_for_width('abcdef', 1), '…')
        self.assertEqual(truncate_for_width('abc', 5), 'abc')


    def test_export_results_writes_markdown_bundle_with_open_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = {
                'path': 'systems.md',
                'score': 120,
                'tags': ['systems'],
                'snippet': 'Failure detection notes.',
                'section_match': {
                    'path': 'systems.md',
                    'path_with_anchor': 'systems.md#failure-detection',
                    'line_number': 8,
                },
            }

            destination = root / 'exports' / 'results.md'
            export_results([note], destination, editor='code', base_directory=root)
            payload = destination.read_text(encoding='utf-8')

            self.assertIn('# Exported markdown-notes-search results', payload)
            self.assertIn('## `systems.md`', payload)
            self.assertIn('`systems.md#failure-detection:8`', payload)
            self.assertIn('code --goto', payload)

    def test_export_results_cli_writes_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'systems.md').write_text('# Distributed Systems\nFailure detection and quorum notes.', encoding='utf-8')
            export_path = root / 'results.json'

            subprocess.run(
                [
                    sys.executable,
                    'notes_search.py',
                    str(root),
                    'distributed',
                    '--export-results',
                    str(export_path),
                    '--export-format',
                    'json',
                    '--editor',
                    'code',
                ],
                cwd=Path(__file__).resolve().parent,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(export_path.read_text(encoding='utf-8'))
            self.assertEqual(payload[0]['path'], 'systems.md')
            self.assertEqual(payload[0]['open_command'][0], 'code')

    def test_selection_helpers_prefer_marked_results(self):
        results = [
            {'path': 'a.md', 'score': 3},
            {'path': 'b.md', 'score': 2},
            {'path': 'c.md', 'score': 1},
        ]

        marked = selected_or_current_results(results, {2, 0}, 1)

        self.assertEqual([note['path'] for note in marked], ['a.md', 'c.md'])
        self.assertEqual(selection_label(results, set()), 'current result')
        self.assertEqual(selection_label(results, {1}), '1 selected result')
        self.assertEqual(selection_label(results, {0, 2}), '2 selected results')

    def test_default_index_filename_constant(self):
        self.assertEqual(DEFAULT_INDEX_FILENAME, '.notes_search_index.json')


if __name__ == '__main__':
    unittest.main()
