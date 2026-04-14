import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from url_shortener import Store, build_server, validate_url


class UrlShortenerStoreTests(unittest.TestCase):
    def test_store_roundtrip_and_reuse_existing_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            code_a = store.shorten('https://example.com/docs')
            code_b = store.shorten('https://example.com/docs')
            self.assertEqual(code_a, code_b)
            self.assertEqual(store.resolve(code_a), 'https://example.com/docs')
            self.assertEqual(store.stats()['link_count'], 1)

    def test_store_handles_code_collision_by_retrying(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            original_candidate = store._candidate_code

            def fake_candidate(url, attempt=0, length=7):
                if attempt == 0:
                    return 'repeat1'
                return original_candidate(url, attempt=attempt, length=length)

            store._candidate_code = fake_candidate
            first = store.shorten('https://example.com/one')
            second = store.shorten('https://example.com/two')

            self.assertEqual(first, 'repeat1')
            self.assertNotEqual(second, first)
            self.assertEqual(store.resolve(second), 'https://example.com/two')


class UrlValidationTests(unittest.TestCase):
    def test_validate_url_accepts_trimmed_http_and_https(self):
        self.assertEqual(validate_url(' https://example.com/path '), 'https://example.com/path')
        self.assertEqual(validate_url('http://localhost:8000/test'), 'http://localhost:8000/test')

    def test_validate_url_rejects_invalid_inputs(self):
        for bad in ['', 'ftp://example.com/file', 'example.com/no-scheme', 'https:///missing-host', None]:
            with self.assertRaises(ValueError):
                validate_url(bad)


class UrlShortenerHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db = Path(self.tmpdir.name) / 'server.db'
        self.server = build_server(db, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmpdir.cleanup()

    def _request(self, path, method='GET', payload=None, raw_data=None):
        data = raw_data
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(f'{self.base_url}{path}', data=data, method=method, headers=headers)
        opener = urllib.request.build_opener(NoRedirectHandler())
        try:
            with opener.open(request) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()
            exc.close()
            return exc.code, exc.headers, body

    def test_root_reports_service_stats(self):
        status, headers, body = self._request('/')
        self.assertEqual(status, 200)
        self.assertIn('application/json', headers.get('Content-Type', ''))
        payload = json.loads(body.decode('utf-8'))
        self.assertEqual(payload['service'], 'url-shortener-http')
        self.assertEqual(payload['stats']['link_count'], 0)

    def test_post_shorten_returns_created_payload_and_redirect_works(self):
        status, _, body = self._request('/shorten', method='POST', payload={'url': 'https://example.com/coursework'})
        self.assertEqual(status, 201)
        payload = json.loads(body.decode('utf-8'))
        self.assertIn('code', payload)
        self.assertEqual(payload['url'], 'https://example.com/coursework')

        status, headers, body = self._request(f"/{payload['code']}")
        self.assertEqual(status, 302)
        self.assertEqual(headers['Location'], 'https://example.com/coursework')
        self.assertEqual(body, b'')

    def test_post_shorten_rejects_invalid_json_and_invalid_urls(self):
        status, _, body = self._request('/shorten', method='POST', raw_data=b'{bad json')
        self.assertEqual(status, 400)
        self.assertIn('valid JSON', body.decode('utf-8'))

        status, _, body = self._request('/shorten', method='POST', payload={'url': 'ftp://example.com/file'})
        self.assertEqual(status, 400)
        self.assertIn('http or https', body.decode('utf-8'))

    def test_route_specific_method_not_allowed_and_missing_codes(self):
        status, headers, body = self._request('/shorten')
        self.assertEqual(status, 405)
        self.assertEqual(headers['Allow'], 'POST')
        self.assertIn('method not allowed', body.decode('utf-8'))

        status, _, body = self._request('/missing-code')
        self.assertEqual(status, 404)
        self.assertIn('short code not found', body.decode('utf-8'))


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


if __name__ == '__main__':
    unittest.main()
