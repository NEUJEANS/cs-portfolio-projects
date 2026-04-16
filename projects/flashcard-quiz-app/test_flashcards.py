import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from flashcards import (
    ANKI_PACKAGE_MARKER,
    Card,
    build_history_key,
    build_recommendations,
    build_session,
    export_cards_to_anki_package,
    export_cards_to_anki_text,
    export_cards_to_json,
    filter_cards,
    load_cards,
    load_history,
    main,
    print_recommendations,
    quiz,
    run_quiz,
    summarize_history,
    update_history,
)


class FlashcardTests(unittest.TestCase):
    def test_load_csv_and_quiz(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer,tags\n2+2,4,math\ncapital of France,Paris,geo\n', encoding='utf-8')
            cards = load_cards(path)
            score, results = quiz(cards, ['4', 'paris'])
            self.assertEqual(score, 2)
            self.assertEqual(results, [True, True])
            self.assertEqual(cards[0].tags, ('math',))

    def test_load_json_cards_accepts_list_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.json'
            path.write_text(
                json.dumps(
                    [
                        {'prompt': '2+2', 'answer': '4', 'tags': ['math', 'drill']},
                        {'prompt': 'capital of France', 'answer': 'Paris', 'tags': 'geo, capitals'},
                    ]
                ),
                encoding='utf-8',
            )
            cards = load_cards(path)
            self.assertEqual(cards[0], Card('2+2', '4', ('math', 'drill')))
            self.assertEqual(cards[1].tags, ('geo', 'capitals'))

    def test_load_anki_text_accepts_tab_separated_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.tsv'
            path.write_text('2+2\t4\tmath, drill\ncapital of France\tParis\tgeo\n', encoding='utf-8')
            cards = load_cards(path)
            self.assertEqual(cards[0], Card('2+2', '4', ('math', 'drill')))
            self.assertEqual(cards[1], Card('capital of France', 'Paris', ('geo',)))

    def test_export_cards_to_json_writes_normalized_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / 'deck.json'
            cards = [Card('2+2', '4', ('math',)), Card('BFS', 'queue', ('graphs', 'algorithms'))]
            export_cards_to_json(cards, export_path, source_path='cards.csv')
            payload = json.loads(export_path.read_text(encoding='utf-8'))
            self.assertEqual(payload['version'], 1)
            self.assertEqual(payload['card_count'], 2)
            self.assertEqual(payload['source_path'], 'cards.csv')
            self.assertEqual(payload['cards'][1]['tags'], ['graphs', 'algorithms'])

    def test_export_cards_to_anki_text_writes_importable_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / 'anki-notes.tsv'
            cards = [Card('2+2', '4', ('math',)), Card('BFS', 'queue', ('graphs', 'algorithms'))]
            export_cards_to_anki_text(cards, export_path)
            lines = export_path.read_text(encoding='utf-8').splitlines()
            self.assertEqual(lines[0], '2+2\t4\tmath')
            self.assertEqual(lines[1], 'BFS\tqueue\tgraphs, algorithms')

    def test_export_cards_to_anki_package_writes_bridge_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / 'deck.anki.zip'
            cards = [Card('2+2', '4', ('math',)), Card('BFS', 'queue', ('graphs', 'algorithms'))]
            export_cards_to_anki_package(cards, export_path, source_path='cards.csv')
            with zipfile.ZipFile(export_path) as archive:
                manifest = json.loads(archive.read('manifest.json').decode('utf-8'))
                notes = archive.read('anki-notes.tsv').decode('utf-8').splitlines()
                self.assertEqual(manifest['format'], ANKI_PACKAGE_MARKER)
                self.assertEqual(manifest['source_path'], 'cards.csv')
                self.assertIn('Bridge bundle', manifest['notes'])
                self.assertEqual(notes[0], '2+2\t4\tmath')

    def test_load_cards_from_anki_package_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / 'deck.anki.zip'
            cards = [Card('2+2', '4', ('math',)), Card('capital of France', 'Paris', ('geo', 'capitals'))]
            export_cards_to_anki_package(cards, export_path)
            loaded = load_cards(export_path)
            self.assertEqual(loaded, cards)

    def test_load_anki_package_rejects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'broken.anki.zip'
            with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('anki-notes.tsv', '2+2\t4\tmath\n')
            with self.assertRaisesRegex(ValueError, 'Anki package missing required entry: manifest.json'):
                load_cards(path)

    def test_load_cards_rejects_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,response\n2+2,4\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'missing required columns: answer'):
                load_cards(path)

    def test_load_json_rejects_non_object_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.json'
            path.write_text(json.dumps(['bad-card']), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'JSON deck card 1 must be an object'):
                load_cards(path)

    def test_load_anki_text_rejects_short_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.tsv'
            path.write_text('2+2\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Anki text deck row 1 must contain at least prompt and answer columns'):
                load_cards(path)

    def test_load_cards_rejects_blank_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer\n2+2,\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'CSV row 2 must include non-empty prompt and answer values'):
                load_cards(path)

    def test_build_session_is_reproducible_and_limited(self):
        cards = [
            Card('one', '1'),
            Card('two', '2'),
            Card('three', '3'),
            Card('four', '4'),
        ]
        session = build_session(cards, limit=2, seed=7)
        self.assertEqual([(card.prompt, card.answer) for card in session], [('four', '4'), ('two', '2')])

    def test_filter_cards_supports_multi_tag_matching(self):
        cards = [
            Card('binary tree', 'node', ('data-structures', 'trees')),
            Card('quick sort', 'n log n', ('algorithms', 'sorting')),
            Card('heap', 'priority queue', ('data-structures', 'trees', 'heaps')),
        ]
        filtered = filter_cards(cards, ['trees', 'data-structures'])
        self.assertEqual([card.prompt for card in filtered], ['binary tree', 'heap'])

    def test_filter_cards_rejects_empty_result(self):
        cards = [Card('2+2', '4', ('math',))]
        with self.assertRaisesRegex(ValueError, 'No cards matched tags: geography'):
            filter_cards(cards, ['geography'])

    def test_run_quiz_retry_incorrect_recovers_score_and_tracks_weak_tags(self):
        cards = [Card('2+2', '4', ('math',)), Card('capital of France', 'Paris', ('geography',))]
        stdout = io.StringIO()
        with patch('builtins.input', side_effect=['5', 'Paris', '4']), patch('sys.stdout', stdout):
            summary = run_quiz(cards, retry_incorrect=True)
        self.assertEqual(summary['unique_cards'], 2)
        self.assertEqual(summary['attempts'], 3)
        self.assertEqual(summary['correct'], 2)
        self.assertEqual(summary['incorrect'], 1)
        self.assertEqual(summary['weakest_tags'], ['math'])
        self.assertEqual(
            [result['correct'] for result in summary['card_results']],
            [False, True, True],
        )
        output = stdout.getvalue()
        self.assertIn('Retry round for missed cards', output)
        self.assertIn('Incorrect. Expected: 4', output)
        self.assertGreaterEqual(output.count('Correct!'), 2)

    def test_load_history_returns_default_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = load_history(Path(tmp) / 'history.json')
        self.assertEqual(history['sessions_run'], 0)
        self.assertEqual(history['cards'], {})
        self.assertEqual(history['version'], 2)

    def test_update_history_tracks_repeat_misses_and_summary(self):
        history = load_history(Path(tempfile.gettempdir()) / 'does-not-exist-history.json')
        updated = update_history(
            history,
            [
                {'prompt': '2+2', 'answer': '4', 'tags': ('math',), 'correct': False},
                {'prompt': '2+2', 'answer': '4', 'tags': ('math',), 'correct': True},
                {'prompt': 'capital of France', 'answer': 'Paris', 'tags': ('geography',), 'correct': False},
            ],
            now='2026-04-14T20:06:00Z',
        )
        summary = summarize_history(updated)
        self.assertEqual(updated['sessions_run'], 1)
        self.assertEqual(updated['total_attempts'], 3)
        self.assertEqual(updated['total_correct'], 1)
        card_key = build_history_key('2+2', '4')
        self.assertEqual(updated['cards'][card_key]['times_incorrect'], 1)
        self.assertEqual(updated['cards'][card_key]['times_correct'], 1)
        self.assertEqual(updated['cards'][card_key]['last_seen_at'], '2026-04-14T20:06:00Z')
        self.assertEqual(updated['cards'][card_key]['first_seen_at'], '2026-04-14T20:06:00Z')
        self.assertEqual(summary['weakest_cards'][0]['prompt'], 'capital of France')
        self.assertEqual(summary['weakest_cards'][1]['prompt'], '2+2')

    def test_update_history_uses_prompt_and_answer_for_card_identity(self):
        updated = update_history(
            load_history(Path(tempfile.gettempdir()) / 'does-not-exist-history.json'),
            [
                {'prompt': 'capital', 'answer': 'Paris', 'tags': ('geography',), 'correct': False},
                {'prompt': 'capital', 'answer': 'Seoul', 'tags': ('geography',), 'correct': True},
            ],
            now='2026-04-14T20:06:00Z',
        )
        self.assertIn(build_history_key('capital', 'Paris'), updated['cards'])
        self.assertIn(build_history_key('capital', 'Seoul'), updated['cards'])

    def test_build_recommendations_prioritizes_fragile_cards(self):
        history = {
            'version': 2,
            'sessions_run': 4,
            'total_attempts': 10,
            'total_correct': 7,
            'cards': {
                build_history_key('binary tree', 'node'): {
                    'prompt': 'binary tree',
                    'answer': 'node',
                    'times_seen': 2,
                    'times_correct': 0,
                    'times_incorrect': 2,
                    'last_result': 'incorrect',
                    'streak': 0,
                },
                build_history_key('queue', 'fifo'): {
                    'prompt': 'queue',
                    'answer': 'fifo',
                    'times_seen': 5,
                    'times_correct': 4,
                    'times_incorrect': 1,
                    'last_result': 'correct',
                    'streak': 2,
                },
                build_history_key('hash map', 'dict'): {
                    'prompt': 'hash map',
                    'answer': 'dict',
                    'times_seen': 6,
                    'times_correct': 6,
                    'times_incorrect': 0,
                    'last_result': 'correct',
                    'streak': 4,
                },
            },
        }
        recommendations = build_recommendations(history, limit=3)
        self.assertEqual(recommendations[0]['prompt'], 'binary tree')
        self.assertEqual(recommendations[0]['action'], 'relearn now')
        self.assertEqual(recommendations[1]['prompt'], 'queue')
        self.assertEqual(recommendations[1]['action'], 'review later')
        self.assertEqual(recommendations[-1]['prompt'], 'hash map')
        self.assertEqual(recommendations[-1]['action'], 'space out')

    def test_print_recommendations_handles_empty_history(self):
        stdout = io.StringIO()
        with patch('sys.stdout', stdout):
            print_recommendations(load_history(Path(tempfile.gettempdir()) / 'does-not-exist-history.json'))
        self.assertIn('Recommendations: no history available yet', stdout.getvalue())

    def test_build_recommendations_marks_single_recent_success_for_review_soon(self):
        history = {
            'version': 2,
            'sessions_run': 1,
            'total_attempts': 1,
            'total_correct': 1,
            'cards': {
                build_history_key('stack', 'lifo'): {
                    'prompt': 'stack',
                    'answer': 'lifo',
                    'times_seen': 1,
                    'times_correct': 1,
                    'times_incorrect': 0,
                    'last_result': 'correct',
                    'streak': 1,
                }
            },
        }
        recommendations = build_recommendations(history, limit=1)
        self.assertEqual(recommendations[0]['action'], 'review soon')

    def test_main_supports_tag_filter_and_reports_weakest_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text(
                'prompt,answer,tags\n2+2,4,math\n2+3,5,math\ncapital of France,Paris,geography\n',
                encoding='utf-8',
            )
            stdout = io.StringIO()
            with patch('builtins.input', side_effect=['0', '4']), patch('sys.stdout', stdout):
                main([str(path), '--tag', 'math', '--seed', '1'])
        output = stdout.getvalue()
        self.assertIn('Tag filter: math', output)
        self.assertIn('Weakest tags: math', output)
        self.assertIn('across 2 unique cards', output)

    def test_main_can_export_only_normalized_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards_path = Path(tmp) / 'cards.csv'
            export_path = Path(tmp) / 'out' / 'cards.json'
            cards_path.write_text('prompt,answer,tags\n2+2,4,math\ncapital of France,Paris,geo\n', encoding='utf-8')
            stdout = io.StringIO()
            with patch('sys.stdout', stdout):
                main([str(cards_path), '--export-json', str(export_path), '--export-only'])
            payload = json.loads(export_path.read_text(encoding='utf-8'))
            self.assertEqual(payload['card_count'], 2)
            self.assertEqual(payload['cards'][0]['prompt'], '2+2')
            self.assertIn('Exported 2 cards', stdout.getvalue())

    def test_main_can_export_anki_bridge_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards_path = Path(tmp) / 'cards.csv'
            notes_path = Path(tmp) / 'out' / 'anki-notes.tsv'
            package_path = Path(tmp) / 'out' / 'deck.anki.zip'
            cards_path.write_text('prompt,answer,tags\n2+2,4,math\ncapital of France,Paris,geo\n', encoding='utf-8')
            stdout = io.StringIO()
            with patch('sys.stdout', stdout):
                main([
                    str(cards_path),
                    '--export-anki-text', str(notes_path),
                    '--export-anki-package', str(package_path),
                    '--export-only',
                ])
            self.assertTrue(notes_path.exists())
            self.assertTrue(package_path.exists())
            output = stdout.getvalue()
            self.assertIn('Anki text file', output)
            self.assertIn('Anki package bridge', output)

    def test_main_loads_json_deck_and_persists_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            cards_path = Path(tmp) / 'cards.json'
            history_path = Path(tmp) / 'history.json'
            cards_path.write_text(
                json.dumps(
                    {
                        'cards': [
                            {'prompt': '2+2', 'answer': '4', 'tags': ['math']},
                            {'prompt': 'capital of France', 'answer': 'Paris', 'tags': ['geography']},
                        ]
                    }
                ),
                encoding='utf-8',
            )
            stdout = io.StringIO()
            with patch('builtins.input', side_effect=['4', 'Rome']), patch('sys.stdout', stdout):
                main([
                    str(cards_path),
                    '--seed', '0',
                    '--history-path', str(history_path),
                    '--show-history-summary',
                    '--show-recommendations',
                    '--recommend-limit', '2',
                ])

            history_data = json.loads(history_path.read_text(encoding='utf-8'))
            self.assertEqual(history_data['sessions_run'], 1)
            self.assertEqual(history_data['total_attempts'], 2)
            self.assertEqual(history_data['total_correct'], 1)
            self.assertEqual(history_data['version'], 2)
            output = stdout.getvalue()
            self.assertIn('History: 1 correct / 2 attempts across 1 sessions (50% accuracy)', output)
            self.assertIn('Historically weakest cards:', output)
            self.assertIn('Recommendations:', output)
            self.assertIn('capital of France: relearn now', output)

    def test_main_exits_cleanly_for_invalid_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,response\n2+2,4\n', encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', stderr), self.assertRaises(SystemExit) as cm:
                main([str(path)])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn('missing required columns: answer', stderr.getvalue())

    def test_main_exits_cleanly_for_invalid_history_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            history_path = Path(tmp) / 'history.json'
            path.write_text('prompt,answer\n2+2,4\n', encoding='utf-8')
            history_path.write_text('{not-json', encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', stderr), self.assertRaises(SystemExit) as cm:
                main([str(path), '--history-path', str(history_path)])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn('History file is not valid JSON', stderr.getvalue())

    def test_main_exits_when_history_output_requested_without_history_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer\n2+2,4\n', encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', stderr), self.assertRaises(SystemExit) as cm:
                main([str(path), '--show-recommendations'])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn('--show-recommendations require --history-path', stderr.getvalue())

    def test_main_exits_for_non_positive_recommend_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer\n2+2,4\n', encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', stderr), self.assertRaises(SystemExit) as cm:
                main([str(path), '--recommend-limit', '0'])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn('--recommend-limit must be a positive integer', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
