import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flashcards import Card, build_session, filter_cards, load_cards, main, quiz, run_quiz


class FlashcardTests(unittest.TestCase):
    def test_load_and_quiz(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer,tags\n2+2,4,math\ncapital of France,Paris,geo\n', encoding='utf-8')
            cards = load_cards(path)
            score, results = quiz(cards, ['4', 'paris'])
            self.assertEqual(score, 2)
            self.assertEqual(results, [True, True])
            self.assertEqual(cards[0].tags, ('math',))

    def test_load_cards_rejects_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,response\n2+2,4\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'missing required columns: answer'):
                load_cards(path)

    def test_load_cards_rejects_blank_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer\n2+2,\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Row 2 must include non-empty prompt and answer values'):
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
        self.assertEqual(summary, {
            'unique_cards': 2,
            'attempts': 3,
            'correct': 2,
            'incorrect': 1,
            'weakest_tags': ['math'],
        })
        output = stdout.getvalue()
        self.assertIn('Retry round for missed cards', output)
        self.assertIn('Incorrect. Expected: 4', output)
        self.assertGreaterEqual(output.count('Correct!'), 2)

    def test_main_exits_cleanly_for_invalid_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,response\n2+2,4\n', encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', stderr), self.assertRaises(SystemExit) as cm:
                main([str(path)])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn('missing required columns: answer', stderr.getvalue())

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


if __name__ == '__main__':
    unittest.main()
