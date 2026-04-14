import tempfile, unittest
from pathlib import Path
from notes_search import index_notes, search_notes

class NotesSearchTests(unittest.TestCase):
    def test_find_by_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'algorithms.md').write_text('#graphs shortest path notes')
            (p / 'db.md').write_text('#sql indexing notes')
            results = search_notes(index_notes(p), 'graphs')
            self.assertEqual([r['name'] for r in results], ['algorithms.md'])

if __name__ == '__main__':
    unittest.main()
