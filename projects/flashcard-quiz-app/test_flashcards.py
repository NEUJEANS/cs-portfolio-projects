import tempfile, unittest
from pathlib import Path
from flashcards import load_cards, quiz

class FlashcardTests(unittest.TestCase):
    def test_load_and_quiz(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cards.csv'
            path.write_text('prompt,answer\n2+2,4\ncapital of France,Paris\n')
            cards = load_cards(path)
            score, results = quiz(cards, ['4', 'paris'])
            self.assertEqual(score, 2)
            self.assertEqual(results, [True, True])

if __name__ == '__main__':
    unittest.main()
