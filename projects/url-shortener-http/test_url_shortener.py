import tempfile, unittest
from pathlib import Path
from url_shortener import Store

class UrlShortenerTests(unittest.TestCase):
    def test_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            code = store.shorten('https://example.com')
            self.assertEqual(store.resolve(code), 'https://example.com')

if __name__ == '__main__':
    unittest.main()
