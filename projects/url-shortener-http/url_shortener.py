import argparse
import hashlib
import http.server
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse, urlsplit

DEFAULT_CODE_LENGTH = 7
CUSTOM_CODE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,32}$')
RESERVED_CODES = {'shorten', 'stats', 'links'}


def _request_path(path):
    return urlsplit(path).path


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
                'created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                'clicks INTEGER NOT NULL DEFAULT 0, '
                'last_accessed_at TEXT, '
                'expires_at TEXT, '
                'deleted_at TEXT'
                ')'
            )
            self._ensure_column(conn, 'clicks', 'INTEGER NOT NULL DEFAULT 0')
            self._ensure_column(conn, 'last_accessed_at', 'TEXT')
            self._ensure_column(conn, 'expires_at', 'TEXT')
            self._ensure_column(conn, 'deleted_at', 'TEXT')
            conn.commit()

    def _ensure_column(self, conn, column_name, definition):
        columns = {
            row['name']
            for row in conn.execute('PRAGMA table_info(links)').fetchall()
        }
        if column_name not in columns:
            conn.execute(f'ALTER TABLE links ADD COLUMN {column_name} {definition}')

    def _candidate_code(self, url, attempt=0, length=DEFAULT_CODE_LENGTH):
        seed = url if attempt == 0 else f'{url}:{attempt}'
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()[:length]

    def _current_timestamp(self, conn):
        return conn.execute('SELECT CURRENT_TIMESTAMP').fetchone()[0]

    def _status_from_row(self, row, now):
        if row['deleted_at'] is not None:
            return 'deleted'
        if row['expires_at'] is not None and row['expires_at'] <= now:
            return 'expired'
        return 'active'

    def shorten(self, url, custom_code=None, expires_in_seconds=None):
        normalized_url = validate_url(url)
        if custom_code is not None:
            custom_code = validate_custom_code(custom_code)
        expiry_seconds = validate_expiry_seconds(expires_in_seconds)

        with closing(self._connect()) as conn:
            existing_for_url = conn.execute(
                'SELECT code FROM links WHERE url = ?',
                (normalized_url,),
            ).fetchone()
            if existing_for_url:
                existing_code = existing_for_url['code']
                if custom_code and existing_code != custom_code:
                    raise ValueError(f'url already shortened with code {existing_code}')
                return existing_code

            if custom_code:
                existing_for_code = conn.execute(
                    'SELECT url FROM links WHERE code = ?',
                    (custom_code,),
                ).fetchone()
                if existing_for_code and existing_for_code['url'] != normalized_url:
                    raise ValueError('custom code is already in use')
                self._insert_link(conn, custom_code, normalized_url, expiry_seconds)
                conn.commit()
                return custom_code

            attempt = 0
            while True:
                code = self._candidate_code(normalized_url, attempt)
                row = conn.execute('SELECT url FROM links WHERE code = ?', (code,)).fetchone()
                if row is None:
                    self._insert_link(conn, code, normalized_url, expiry_seconds)
                    conn.commit()
                    return code
                if row['url'] == normalized_url:
                    return code
                attempt += 1

    def _insert_link(self, conn, code, url, expiry_seconds):
        if expiry_seconds is None:
            conn.execute('INSERT INTO links(code, url) VALUES (?, ?)', (code, url))
            return
        conn.execute(
            "INSERT INTO links(code, url, expires_at) VALUES (?, ?, datetime(CURRENT_TIMESTAMP, ?))",
            (code, url, f'+{expiry_seconds} seconds'),
        )

    def resolve(self, code, record_click=False):
        with closing(self._connect()) as conn:
            row = conn.execute(
                'SELECT code, url, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                'FROM links WHERE code = ?',
                (code,),
            ).fetchone()
            if not row:
                return None

            current_time = self._current_timestamp(conn)
            status = self._status_from_row(row, now=current_time)
            if record_click and status == 'active':
                conn.execute(
                    'UPDATE links '
                    'SET clicks = clicks + 1, last_accessed_at = CURRENT_TIMESTAMP '
                    'WHERE code = ?',
                    (code,),
                )
                conn.commit()
                row = conn.execute(
                    'SELECT code, url, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                    'FROM links WHERE code = ?',
                    (code,),
                ).fetchone()
                current_time = self._current_timestamp(conn)
                status = self._status_from_row(row, now=current_time)

            payload = dict(row)
            payload['status'] = status
            return payload

    def delete_link(self, code):
        with closing(self._connect()) as conn:
            row = conn.execute(
                'SELECT code, url, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                'FROM links WHERE code = ?',
                (code,),
            ).fetchone()
            if not row:
                return None
            if row['deleted_at'] is None:
                conn.execute(
                    'UPDATE links SET deleted_at = CURRENT_TIMESTAMP WHERE code = ?',
                    (code,),
                )
                conn.commit()
            return self.get_link_info(code)

    def stats(self):
        with closing(self._connect()) as conn:
            row = conn.execute(
                'SELECT '
                'COUNT(*) AS link_count, '
                'COALESCE(SUM(clicks), 0) AS total_clicks, '
                "SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS deleted_count, "
                "SUM(CASE WHEN deleted_at IS NULL AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS expired_count, "
                "SUM(CASE WHEN deleted_at IS NULL AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP) THEN 1 ELSE 0 END) AS active_count "
                'FROM links'
            ).fetchone()
            current_time = self._current_timestamp(conn)
            top_links = [
                {
                    'code': link['code'],
                    'url': link['url'],
                    'clicks': link['clicks'],
                    'status': self._status_from_row(link, now=current_time),
                    'expires_at': link['expires_at'],
                }
                for link in conn.execute(
                    'SELECT code, url, clicks, expires_at, deleted_at FROM links '
                    'ORDER BY clicks DESC, code ASC LIMIT 5'
                ).fetchall()
            ]
            return {
                'link_count': row['link_count'],
                'active_count': row['active_count'] or 0,
                'expired_count': row['expired_count'] or 0,
                'deleted_count': row['deleted_count'] or 0,
                'total_clicks': row['total_clicks'],
                'top_links': top_links,
            }

    def get_link_info(self, code):
        return self.resolve(code, record_click=False)


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


def validate_custom_code(code):
    if not isinstance(code, str):
        raise ValueError('custom code must be a string')
    candidate = code.strip()
    if not candidate:
        raise ValueError('custom code must not be empty')
    if candidate in RESERVED_CODES:
        raise ValueError('custom code uses a reserved route name')
    if not CUSTOM_CODE_PATTERN.fullmatch(candidate):
        raise ValueError('custom code must be 3-32 chars using letters, numbers, hyphen, or underscore')
    return candidate


def validate_expiry_seconds(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('expires_in_seconds must be an integer')
    if value <= 0:
        raise ValueError('expires_in_seconds must be greater than zero')
    return value


class Handler(http.server.BaseHTTPRequestHandler):
    store = None
    server_version = 'UrlShortener/1.2'

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
        request_path = _request_path(self.path)
        if request_path != '/shorten':
            self._send_json(404, {'error': 'not found'})
            return
        try:
            payload = self._read_json_body()
            if 'url' not in payload:
                raise ValueError('JSON body must include url')
            normalized_url = validate_url(payload['url'])
            custom_code = payload.get('code')
            expires_in_seconds = payload.get('expires_in_seconds')
            code = self.store.shorten(
                normalized_url,
                custom_code=custom_code,
                expires_in_seconds=expires_in_seconds,
            )
            info = self.store.get_link_info(code)
        except ValueError as exc:
            self._send_json(400, {'error': str(exc)})
            return

        host = self.headers.get('Host') or f'{self.server.server_name}:{self.server.server_port}'
        body = {
            'code': code,
            'short_url': f'http://{host}/{code}',
            'url': normalized_url,
            'clicks': info['clicks'],
            'status': info['status'],
            'expires_at': info['expires_at'],
        }
        self._send_json(201, body)

    def do_GET(self):
        request_path = _request_path(self.path)
        if request_path == '/':
            self._send_json(200, {'service': 'url-shortener-http', 'stats': self.store.stats()})
            return
        if request_path == '/shorten':
            self._send_method_not_allowed('POST')
            return
        if request_path == '/stats':
            self._send_json(200, self.store.stats())
            return
        if request_path.startswith('/links/'):
            code = request_path.removeprefix('/links/').strip('/')
            if not code:
                self._send_json(404, {'error': 'not found'})
                return
            info = self.store.get_link_info(code)
            if not info:
                self._send_json(404, {'error': 'short code not found'})
                return
            self._send_json(200, info)
            return

        code = request_path.lstrip('/')
        if not code:
            self._send_json(404, {'error': 'not found'})
            return
        info = self.store.resolve(code, record_click=True)
        if not info:
            self._send_json(404, {'error': 'short code not found'})
            return
        if info['status'] == 'expired':
            self._send_json(410, {'error': 'short code has expired', 'code': code, 'status': 'expired'})
            return
        if info['status'] == 'deleted':
            self._send_json(410, {'error': 'short code has been deleted', 'code': code, 'status': 'deleted'})
            return
        self.send_response(302)
        self.send_header('Location', info['url'])
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_PUT(self):
        if _request_path(self.path) == '/shorten':
            self._send_method_not_allowed('POST')
        else:
            self._send_json(404, {'error': 'not found'})

    def do_DELETE(self):
        request_path = _request_path(self.path)
        if request_path == '/shorten':
            self._send_method_not_allowed('POST')
            return
        if request_path.startswith('/links/'):
            code = request_path.removeprefix('/links/').strip('/')
            if not code:
                self._send_json(404, {'error': 'not found'})
                return
            info = self.store.delete_link(code)
            if not info:
                self._send_json(404, {'error': 'short code not found'})
                return
            self._send_json(200, {'deleted': True, 'link': info})
            return
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
