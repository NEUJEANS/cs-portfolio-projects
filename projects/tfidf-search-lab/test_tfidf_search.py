import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tfidf_search import CorpusError, TfIdfSearchEngine, format_results


class TfIdfSearchEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / 'alpha.txt').write_text(
            'Distributed systems use vector clocks and logical clocks.',
            encoding='utf-8',
        )
        (self.root / 'beta.md').write_text(
            'Search systems rely on inverted indexes and tf idf ranking.',
            encoding='utf-8',
        )
        (self.root / 'gamma.txt').write_text(
            'Graph algorithms include pagerank and shortest paths.',
            encoding='utf-8',
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_tokenize_and_stopword_filter(self) -> None:
        engine = TfIdfSearchEngine()
        self.assertEqual(
            engine.normalize_tokens("The Search engine's ranking in practice"),
            ['search', "engine's", 'ranking', 'practice'],
        )

    def test_build_index_and_stats(self) -> None:
        engine = TfIdfSearchEngine()
        engine.build_from_directory(self.root)
        stats = engine.stats()
        self.assertEqual(stats['documents'], 3)
        self.assertGreaterEqual(stats['terms'], 10)
        self.assertIn('beta.md', engine.postings['search'])

    def test_search_ranks_relevant_document_first(self) -> None:
        engine = TfIdfSearchEngine()
        engine.build_from_directory(self.root)
        results = engine.search('tf idf inverted index search', limit=3)
        self.assertEqual(results[0].path, 'beta.md')
        self.assertIn('search', results[0].matched_terms)

    def test_rebuild_resets_previous_index_state(self) -> None:
        engine = TfIdfSearchEngine()
        engine.build_from_directory(self.root)
        isolated_root = self.root / 'isolated'
        isolated_root.mkdir()
        (isolated_root / 'only.txt').write_text('binary trees rotations balancing', encoding='utf-8')
        engine.build_from_directory(isolated_root)
        self.assertEqual(engine.stats()['documents'], 1)
        self.assertNotIn('beta.md', engine.documents)
        self.assertEqual(engine.search('balancing')[0].path, 'only.txt')

    def test_format_results_returns_human_readable_lines(self) -> None:
        engine = TfIdfSearchEngine()
        engine.build_from_directory(self.root)
        rendered = format_results(engine.search('pagerank graph'))
        self.assertIn('gamma.txt', rendered)
        self.assertIn('score=', rendered)
        self.assertIn('terms=[', rendered)

    def test_empty_query_after_stopwords_raises(self) -> None:
        engine = TfIdfSearchEngine()
        engine.build_from_directory(self.root)
        with self.assertRaises(CorpusError):
            engine.search('the and of')


class TfIdfCliTests(unittest.TestCase):
    def test_cli_json_output(self) -> None:
        project_dir = Path(__file__).resolve().parent
        output = subprocess.check_output(
            [
                'python3',
                'tfidf_search.py',
                'sample_corpus',
                'search ranking',
                '--json',
                '--stats',
            ],
            cwd=project_dir,
            text=True,
        )
        payload = json.loads(output)
        self.assertEqual(payload['stats']['documents'], 3)
        self.assertEqual(payload['results'][0]['path'], 'search.txt')
        self.assertIn('search', payload['results'][0]['matched_terms'])


if __name__ == '__main__':
    unittest.main()
