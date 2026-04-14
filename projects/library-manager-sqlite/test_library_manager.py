import tempfile, unittest
from pathlib import Path
from library_manager import Library

class LibraryTests(unittest.TestCase):
    def test_add_and_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'library.db'
            lib = Library(db)
            lib.add_book('Clean Code', 'Robert C. Martin')
            self.assertTrue(lib.list_books()[0]['available'])
            lib.checkout(1)
            self.assertFalse(lib.list_books()[0]['available'])

if __name__ == '__main__':
    unittest.main()
