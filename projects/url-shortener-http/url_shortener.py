import argparse
import hashlib
import http.server
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_CODE_LENGTH = 7


class Store:
    def __init__(self, db_path='shortener.db'):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with closing(self._connect()) as conn:
            conn.execute(
                'CREATE TABLE IF NOT EXISTS links ('
                'code TEXT PRIMARY KEY, '
                'url TEXT NOT NULL UNIQUE, '
                'created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP'
                ')'
            )
            conn.commit()

    def _candidate_code(self, url, attempt=0, length=DEFAULT_CODE_LENGTH):
        seed = url if attempt == 0 else f'{url}:{attempt}'
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()[:length]

    def shorten(self, url):
        normalized_url = validate_url(url)
        with closing(self._connect()) as conn:
            existing = conn.execute('SELECT code FROM links WHERE url = ?', (normalized_url,)).fetchone()
            if existing:
                return existing['code']

            attempt = 0
            while True:
                code = self._candidate_code(normalized_url, attempt)
                row = conn.execute('SELECT url FROM links WHERE code = ?', (code,)).fetchone()
                if row is None:
                    conn.execute('INSERT INTO links(code, url) VALUES (?, ?)', (code, normalized_url))
                    conn.commit()
                    return code
                if row['url'] == normalized_url:
                    return code
                attempt += 1

    def resolve(self, code):
        with closing(self._connect()) as conn:
            row = conn.execute('SELECT url FROM links WHERE code = ?', (code,)).fetchone()
            return row['url'] if row else None

    def stats(self):
        with closing(self._connect()) as conn:
            row = conn.execute('SELECT COUNT(*) AS link_count FROM links').fetchone()
            return {'link_count': row['link_count']}


def validate_url(url):
    if not isinstance(url, str):
        raise ValueError('url must be a string')
    candidate = url.strip()
    if not candidate:
        raise ValueError('url must not be empty')

    parsed = urlparse(candidate)
    if parsed.scheme not in {'http', 'https'}:
        raise ValueError('url must use http or https')
    if not parsed.netloc:
        raise ValueError('url must include a host')
    return candidate


class Handler(http.server.BaseHTTPRequestHandler):
    store = None
    server_version = 'UrlShortener/1.0'

    def _send_json(self, status_code, payload, headers=None):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_method_not_allowed(self, allow):
        self._send_json(405, {'error': 'method not allowed'}, {'Allow': allow})

    def _read_json_body(self):
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length)
        if not raw:
            raise ValueError('request body is required')
        try:
            payload = json.loads(raw.decode('utf-8'))
        except json.JSONDecodeError as exc:
            raise ValueError('request body must be valid JSON') from exc
        if not isinstance(payload, dict):
            raise ValueError('JSON body must be an object')
        return payload

    def do_POST(self):
        if self.path != '/shorten':
            self._send_json(404, {'error': 'not found'})
            return
        try:
            payload = self._read_json_body()
            if 'url' not in payload:
                raise ValueError('JSON body must include url')
            normalized_url = validate_url(payload['url'])
            code = self.store.shorten(normalized_url)
        except ValueError as exc:
            self._send_json(400, {'error': str(exc)})
            return

        body = {
            'code': code,
            'short_url': f'http://127.0.0.1:{self.server.server_port}/{code}',
            'url': normalized_url,
        }
        self._send_json(201, body)

    def do_GET(self):
        if self.path == '/':
            self._send_json(200, {'service': 'url-shortener-http', 'stats': self.store.stats()})
            return
        if self.path == '/shorten':
            self._send_method_not_allowed('POST')
            return

        code = self.path.lstrip('/')
        if not code:
            self._send_json(404, {'error': 'not found'})
            return
        url = self.store.resolve(code)
        if not url:
            self._send_json(404, {'error': 'short code not found'})
            return
        self.send_response(302)
        self.send_header('Location', url)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_PUT(self):
        if self.path == '/shorten':
            self._send_method_not_allowed('POST')
        else:
            self._send_json(404, {'error': 'not found'})

    def do_DELETE(self):
        if self.path == '/shorten':
            self._send_method_not_allowed('POST')
        else:
            self._send_json(404, {'error': 'not found'})

    def log_message(self, format, *args):
        return


def build_server(db_path, port=8000, host='127.0.0.1'):
    Handler.store = Store(db_path)
    return http.server.ThreadingHTTPServer((host, port), Handler)


def serve(db_path, port=8000, host='127.0.0.1'):
    server = build_server(db_path, port=port, host=host)
    server.serve_forever()


def main(argv=None):
    parser = argparse.ArgumentParser(description='URL shortener HTTP server')
    parser.add_argument('--db', default='shortener.db')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args(argv)
    serve(args.db, port=args.port, host=args.host)


if __name__ == '__main__':
    main()
