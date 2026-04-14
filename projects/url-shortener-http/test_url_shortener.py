import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from url_shortener import Store, build_server, validate_custom_code, validate_url


class UrlShortenerStoreTests(unittest.TestCase):
    def test_store_roundtrip_and_reuse_existing_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            code_a = store.shorten('https://example.com/docs')
            code_b = store.shorten('https://example.com/docs')
            self.assertEqual(code_a, code_b)
            info = store.resolve(code_a)
            self.assertEqual(info['url'], 'https://example.com/docs')
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
            self.assertEqual(store.resolve(second)['url'], 'https://example.com/two')

    def test_store_supports_custom_codes_and_tracks_clicks(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            code = store.shorten('https://example.com/portfolio', custom_code='portfolio')
            self.assertEqual(code, 'portfolio')

            first = store.resolve(code, record_click=True)
            second = store.resolve(code, record_click=True)

            self.assertEqual(first['clicks'], 1)
            self.assertEqual(second['clicks'], 2)
            self.assertIsNotNone(second['last_accessed_at'])
            stats = store.stats()
            self.assertEqual(stats['total_clicks'], 2)
            self.assertEqual(stats['top_links'][0]['code'], 'portfolio')

    def test_store_rejects_conflicting_custom_code_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'shortener.db'
            store = Store(db)
            store.shorten('https://example.com/a', custom_code='alpha')

            with self.assertRaisesRegex(ValueError, 'already in use'):
                store.shorten('https://example.com/b', custom_code='alpha')

            with self.assertRaisesRegex(ValueError, 'already shortened'):
                store.shorten('https://example.com/a', custom_code='beta')


class UrlValidationTests(unittest.TestCase):
    def test_validate_url_accepts_trimmed_http_and_https(self):
        self.assertEqual(validate_url(' https://example.com/path '), 'https://example.com/path')
        self.assertEqual(validate_url('http://localhost:8000/test'), 'http://localhost:8000/test')

    def test_validate_url_rejects_invalid_inputs(self):
        for bad in ['', 'ftp://example.com/file', 'example.com/no-scheme', 'https:///missing-host', None]:
            with self.assertRaises(ValueError):
                validate_url(bad)

    def test_validate_custom_code_rejects_invalid_or_reserved_values(self):
        self.assertEqual(validate_custom_code('portfolio_v1'), 'portfolio_v1')
        for bad in ['', 'ab', 'with space', 'shorten', None]:
            with self.assertRaises(ValueError):
                validate_custom_code(bad)


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
        self.assertEqual(payload['stats']['total_clicks'], 0)

    def test_post_shorten_returns_created_payload_and_redirect_updates_stats(self):
        status, _, body = self._request(
            '/shorten',
            method='POST',
            payload={'url': 'https://example.com/coursework', 'code': 'coursework'},
        )
        self.assertEqual(status, 201)
        payload = json.loads(body.decode('utf-8'))
        self.assertEqual(payload['code'], 'coursework')
        self.assertEqual(payload['clicks'], 0)
        self.assertTrue(payload['short_url'].endswith('/coursework'))

        status, headers, body = self._request('/coursework?from=test')
        self.assertEqual(status, 302)
        self.assertEqual(headers['Location'], 'https://example.com/coursework')
        self.assertEqual(body, b'')

        status, _, body = self._request('/links/coursework')
        self.assertEqual(status, 200)
        info = json.loads(body.decode('utf-8'))
        self.assertEqual(info['clicks'], 1)
        self.assertIsNotNone(info['last_accessed_at'])

        status, _, body = self._request('/stats')
        stats = json.loads(body.decode('utf-8'))
        self.assertEqual(status, 200)
        self.assertEqual(stats['total_clicks'], 1)
        self.assertEqual(stats['top_links'][0]['code'], 'coursework')

    def test_post_shorten_rejects_invalid_json_invalid_urls_and_bad_custom_codes(self):
        status, _, body = self._request('/shorten', method='POST', raw_data=b'{bad json')
        self.assertEqual(status, 400)
        self.assertIn('valid JSON', body.decode('utf-8'))

        status, _, body = self._request('/shorten', method='POST', payload={'url': 'ftp://example.com/file'})
        self.assertEqual(status, 400)
        self.assertIn('http or https', body.decode('utf-8'))

        status, _, body = self._request('/shorten', method='POST', payload={'url': 'https://example.com', 'code': 'x'})
        self.assertEqual(status, 400)
        self.assertIn('3-32 chars', body.decode('utf-8'))

    def test_route_specific_method_not_allowed_and_missing_codes(self):
        status, headers, body = self._request('/shorten')
        self.assertEqual(status, 405)
        self.assertEqual(headers['Allow'], 'POST')
        self.assertIn('method not allowed', body.decode('utf-8'))

        status, _, body = self._request('/missing-code')
        self.assertEqual(status, 404)
        self.assertIn('short code not found', body.decode('utf-8'))

        status, _, body = self._request('/links/missing-code')
        self.assertEqual(status, 404)
        self.assertIn('short code not found', body.decode('utf-8'))


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


if __name__ == '__main__':
    unittest.main()
