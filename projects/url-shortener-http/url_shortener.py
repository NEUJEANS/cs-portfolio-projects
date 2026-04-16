import argparse
import hashlib
import http.server
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse, urlsplit

DEFAULT_CODE_LENGTH = 7
CUSTOM_CODE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,32}$')
OWNER_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$')
RESERVED_CODES = {'shorten', 'stats', 'links', 'owners'}
ADMIN_KEY_HEADER = 'X-Admin-Key'


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
                'owner TEXT NOT NULL DEFAULT \'public\', '
                'created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                'clicks INTEGER NOT NULL DEFAULT 0, '
                'last_accessed_at TEXT, '
                'expires_at TEXT, '
                'deleted_at TEXT'
                ')'
            )
            self._ensure_column(conn, 'owner', "TEXT NOT NULL DEFAULT 'public'")
            self._ensure_column(conn, 'clicks', 'INTEGER NOT NULL DEFAULT 0')
            self._ensure_column(conn, 'last_accessed_at', 'TEXT')
            self._ensure_column(conn, 'expires_at', 'TEXT')
            self._ensure_column(conn, 'deleted_at', 'TEXT')
            conn.commit()

    def _ensure_column(self, conn, column_name, definition):
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(links)').fetchall()}
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

    def shorten(self, url, custom_code=None, expires_in_seconds=None, owner='public'):
        normalized_url = validate_url(url)
        owner = validate_owner(owner)
        if custom_code is not None:
            custom_code = validate_custom_code(custom_code)
        expiry_seconds = validate_expiry_seconds(expires_in_seconds)

        with closing(self._connect()) as conn:
            existing_for_url = conn.execute(
                'SELECT code, owner FROM links WHERE url = ?',
                (normalized_url,),
            ).fetchone()
            if existing_for_url:
                existing_code = existing_for_url['code']
                if custom_code and existing_code != custom_code:
                    raise ValueError(f'url already shortened with code {existing_code}')
                if existing_for_url['owner'] != owner:
                    raise ValueError(f'url already shortened for owner {existing_for_url["owner"]}')
                return existing_code

            if custom_code:
                existing_for_code = conn.execute(
                    'SELECT url FROM links WHERE code = ?',
                    (custom_code,),
                ).fetchone()
                if existing_for_code and existing_for_code['url'] != normalized_url:
                    raise ValueError('custom code is already in use')
                self._insert_link(conn, custom_code, normalized_url, expiry_seconds, owner)
                conn.commit()
                return custom_code

            attempt = 0
            while True:
                code = self._candidate_code(normalized_url, attempt)
                row = conn.execute('SELECT url FROM links WHERE code = ?', (code,)).fetchone()
                if row is None:
                    self._insert_link(conn, code, normalized_url, expiry_seconds, owner)
                    conn.commit()
                    return code
                if row['url'] == normalized_url:
                    return code
                attempt += 1

    def _insert_link(self, conn, code, url, expiry_seconds, owner):
        if expiry_seconds is None:
            conn.execute('INSERT INTO links(code, url, owner) VALUES (?, ?, ?)', (code, url, owner))
            return
        conn.execute(
            "INSERT INTO links(code, url, owner, expires_at) VALUES (?, ?, ?, datetime(CURRENT_TIMESTAMP, ?))",
            (code, url, owner, f'+{expiry_seconds} seconds'),
        )

    def resolve(self, code, record_click=False):
        with closing(self._connect()) as conn:
            row = conn.execute(
                'SELECT code, url, owner, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                'FROM links WHERE code = ?',
                (code,),
            ).fetchone()
            if not row:
                return None

            current_time = self._current_timestamp(conn)
            status = self._status_from_row(row, now=current_time)
            if record_click and status == 'active':
                conn.execute(
                    'UPDATE links SET clicks = clicks + 1, last_accessed_at = CURRENT_TIMESTAMP WHERE code = ?',
                    (code,),
                )
                conn.commit()
                row = conn.execute(
                    'SELECT code, url, owner, clicks, created_at, last_accessed_at, expires_at, deleted_at '
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
                'SELECT code, url, owner, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                'FROM links WHERE code = ?',
                (code,),
            ).fetchone()
            if not row:
                return None
            if row['deleted_at'] is None:
                conn.execute('UPDATE links SET deleted_at = CURRENT_TIMESTAMP WHERE code = ?', (code,))
                conn.commit()
            return self.get_link_info(code)

    def stats(self, owner=None):
        owner = validate_owner(owner) if owner is not None else None
        with closing(self._connect()) as conn:
            where = ''
            params = ()
            if owner is not None:
                where = ' WHERE owner = ?'
                params = (owner,)
            row = conn.execute(
                'SELECT '
                'COUNT(*) AS link_count, '
                'COALESCE(SUM(clicks), 0) AS total_clicks, '
                "SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS deleted_count, "
                "SUM(CASE WHEN deleted_at IS NULL AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS expired_count, "
                "SUM(CASE WHEN deleted_at IS NULL AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP) THEN 1 ELSE 0 END) AS active_count "
                'FROM links' + where,
                params,
            ).fetchone()
            current_time = self._current_timestamp(conn)
            top_links = [
                {
                    'code': link['code'],
                    'url': link['url'],
                    'owner': link['owner'],
                    'clicks': link['clicks'],
                    'status': self._status_from_row(link, now=current_time),
                    'expires_at': link['expires_at'],
                }
                for link in conn.execute(
                    'SELECT code, url, owner, clicks, expires_at, deleted_at FROM links'
                    + where
                    + ' ORDER BY clicks DESC, code ASC LIMIT 5',
                    params,
                ).fetchall()
            ]
            owners = [
                {'owner': item['owner'], 'link_count': item['link_count'], 'total_clicks': item['total_clicks']}
                for item in conn.execute(
                    'SELECT owner, COUNT(*) AS link_count, COALESCE(SUM(clicks), 0) AS total_clicks '
                    'FROM links' + where + ' GROUP BY owner ORDER BY owner ASC',
                    params,
                ).fetchall()
            ]
            payload = {
                'link_count': row['link_count'],
                'active_count': row['active_count'] or 0,
                'expired_count': row['expired_count'] or 0,
                'deleted_count': row['deleted_count'] or 0,
                'total_clicks': row['total_clicks'],
                'top_links': top_links,
            }
            if owner is None:
                payload['owners'] = owners
            else:
                payload['owner'] = owner
            return payload

    def list_links(self, owner=None, limit=50):
        owner = validate_owner(owner) if owner is not None else None
        limit = validate_limit(limit)
        with closing(self._connect()) as conn:
            current_time = self._current_timestamp(conn)
            if owner is None:
                rows = conn.execute(
                    'SELECT code, url, owner, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                    'FROM links ORDER BY created_at DESC, code ASC LIMIT ?',
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT code, url, owner, clicks, created_at, last_accessed_at, expires_at, deleted_at '
                    'FROM links WHERE owner = ? ORDER BY created_at DESC, code ASC LIMIT ?',
                    (owner, limit),
                ).fetchall()
            links = []
            for row in rows:
                payload = dict(row)
                payload['status'] = self._status_from_row(row, now=current_time)
                links.append(payload)
            return links

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


def validate_owner(owner):
    if not isinstance(owner, str):
        raise ValueError('owner must be a string')
    candidate = owner.strip()
    if not candidate:
        raise ValueError('owner must not be empty')
    if not OWNER_PATTERN.fullmatch(candidate):
        raise ValueError('owner must be 2-32 chars using letters, numbers, hyphen, or underscore')
    return candidate


def validate_expiry_seconds(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('expires_in_seconds must be an integer')
    if value <= 0:
        raise ValueError('expires_in_seconds must be greater than zero')
    return value


def validate_limit(value):
    if isinstance(value, bool):
        raise ValueError('limit must be an integer')
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError as exc:
            raise ValueError('limit must be an integer') from exc
    if not isinstance(value, int):
        raise ValueError('limit must be an integer')
    if value <= 0 or value > 200:
        raise ValueError('limit must be between 1 and 200')
    return value


class UrlShortenerApp:
    def __init__(self, store, admin_key=None):
        self.store = store
        self.admin_key = admin_key

    def _json_bytes(self, payload):
        return json.dumps(payload).encode('utf-8')

    def _response(self, status_code, payload=None, headers=None, body=b''):
        final_headers = {'Content-Length': str(len(body))}
        if payload is not None:
            body = self._json_bytes(payload)
            final_headers['Content-Type'] = 'application/json; charset=utf-8'
            final_headers['Content-Length'] = str(len(body))
        if headers:
            final_headers.update(headers)
        return {'status': status_code, 'headers': final_headers, 'body': body}

    def _read_json_body(self, body_bytes):
        if not body_bytes:
            raise ValueError('request body is required')
        try:
            payload = json.loads(body_bytes.decode('utf-8'))
        except json.JSONDecodeError as exc:
            raise ValueError('request body must be valid JSON') from exc
        if not isinstance(payload, dict):
            raise ValueError('JSON body must be an object')
        return payload

    def _short_url(self, base_url, code):
        return f'{base_url.rstrip("/")}/{code}'

    def _is_admin(self, headers):
        if not self.admin_key:
            return True
        supplied = headers.get(ADMIN_KEY_HEADER) or headers.get(ADMIN_KEY_HEADER.lower())
        return supplied == self.admin_key

    def _require_admin(self, headers):
        if self._is_admin(headers):
            return None
        return self._response(
            401,
            {'error': 'admin api key required'},
            {'WWW-Authenticate': 'ApiKey realm="url-shortener-admin"'},
        )

    def handle_request(self, method, path, headers=None, body=b'', base_url='http://127.0.0.1:8000'):
        headers = headers or {}
        request_path = _request_path(path)
        query = urlsplit(path).query
        query_params = dict(item.split('=', 1) if '=' in item else (item, '') for item in query.split('&') if item)

        if method == 'POST' and request_path == '/shorten':
            try:
                payload = self._read_json_body(body)
                if 'url' not in payload:
                    raise ValueError('JSON body must include url')
                normalized_url = validate_url(payload['url'])
                owner = payload.get('owner', 'public')
                if owner != 'public' and not self._is_admin(headers):
                    return self._response(
                        401,
                        {'error': 'admin api key required to assign a custom owner'},
                        {'WWW-Authenticate': 'ApiKey realm="url-shortener-admin"'},
                    )
                code = self.store.shorten(
                    normalized_url,
                    custom_code=payload.get('code'),
                    expires_in_seconds=payload.get('expires_in_seconds'),
                    owner=owner,
                )
                info = self.store.get_link_info(code)
            except ValueError as exc:
                return self._response(400, {'error': str(exc)})
            return self._response(
                201,
                {
                    'code': code,
                    'short_url': self._short_url(base_url, code),
                    'url': normalized_url,
                    'owner': info['owner'],
                    'clicks': info['clicks'],
                    'status': info['status'],
                    'expires_at': info['expires_at'],
                },
            )

        if method == 'GET' and request_path == '/':
            return self._response(200, {'service': 'url-shortener-http', 'stats': self.store.stats()})
        if request_path == '/shorten' and method in {'GET', 'PUT', 'DELETE'}:
            return self._response(405, {'error': 'method not allowed'}, {'Allow': 'POST'})
        if method == 'GET' and request_path == '/stats':
            auth = self._require_admin(headers)
            if auth:
                return auth
            owner = query_params.get('owner')
            try:
                return self._response(200, self.store.stats(owner=owner))
            except ValueError as exc:
                return self._response(400, {'error': str(exc)})
        if request_path.startswith('/owners/'):
            auth = self._require_admin(headers)
            if auth:
                return auth
            suffix = request_path.removeprefix('/owners/')
            if not suffix.endswith('/links'):
                return self._response(404, {'error': 'not found'})
            owner = suffix[:-len('/links')].strip('/')
            if not owner or '/' in owner:
                return self._response(404, {'error': 'not found'})
            try:
                limit = query_params.get('limit', 50)
                validated_owner = validate_owner(owner)
                links = self.store.list_links(owner=validated_owner, limit=limit)
                return self._response(200, {'owner': validated_owner, 'links': links, 'count': len(links)})
            except ValueError as exc:
                return self._response(400, {'error': str(exc)})
        if request_path.startswith('/links/'):
            auth = self._require_admin(headers)
            if auth:
                return auth
            code = request_path.removeprefix('/links/').strip('/')
            if not code:
                return self._response(404, {'error': 'not found'})
            if method == 'GET':
                info = self.store.get_link_info(code)
                if not info:
                    return self._response(404, {'error': 'short code not found'})
                return self._response(200, info)
            if method == 'DELETE':
                info = self.store.delete_link(code)
                if not info:
                    return self._response(404, {'error': 'short code not found'})
                return self._response(200, {'deleted': True, 'link': info})
            return self._response(405, {'error': 'method not allowed'}, {'Allow': 'GET, DELETE'})

        if method != 'GET':
            return self._response(404, {'error': 'not found'})

        code = request_path.lstrip('/')
        if not code:
            return self._response(404, {'error': 'not found'})
        info = self.store.resolve(code, record_click=True)
        if not info:
            return self._response(404, {'error': 'short code not found'})
        if info['status'] == 'expired':
            return self._response(410, {'error': 'short code has expired', 'code': code, 'status': 'expired'})
        if info['status'] == 'deleted':
            return self._response(410, {'error': 'short code has been deleted', 'code': code, 'status': 'deleted'})
        return self._response(302, headers={'Location': info['url']})


class Handler(http.server.BaseHTTPRequestHandler):
    store = None
    admin_key = None
    server_version = 'UrlShortener/1.4'

    def _base_url(self):
        host = self.headers.get('Host') or f'{self.server.server_name}:{self.server.server_port}'
        return f'http://{host}'

    def _write_response(self, response):
        self.send_response(response['status'])
        for key, value in response['headers'].items():
            self.send_header(key, value)
        self.end_headers()
        if response['body']:
            self.wfile.write(response['body'])

    def _dispatch(self, method):
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length else b''
        app = UrlShortenerApp(self.store, admin_key=self.admin_key)
        response = app.handle_request(
            method,
            self.path,
            headers=dict(self.headers.items()),
            body=body,
            base_url=self._base_url(),
        )
        self._write_response(response)

    def do_POST(self):
        self._dispatch('POST')

    def do_GET(self):
        self._dispatch('GET')

    def do_PUT(self):
        self._dispatch('PUT')

    def do_DELETE(self):
        self._dispatch('DELETE')

    def log_message(self, format, *args):
        return


class WsgiUrlShortenerApp:
    def __init__(self, store, admin_key=None):
        self.app = UrlShortenerApp(store, admin_key=admin_key)

    def __call__(self, environ, start_response):
        body_length = environ.get('CONTENT_LENGTH') or '0'
        try:
            length = int(body_length)
        except ValueError:
            length = 0
        body = environ['wsgi.input'].read(length) if length else b''
        scheme = environ.get('wsgi.url_scheme', 'http')
        host = environ.get('HTTP_HOST') or environ.get('SERVER_NAME', '127.0.0.1')
        port = environ.get('SERVER_PORT')
        if port and ':' not in host and port not in {'80', '443'}:
            host = f'{host}:{port}'
        path = (environ.get('PATH_INFO') or '/') + (f"?{environ.get('QUERY_STRING')}" if environ.get('QUERY_STRING') else '')
        headers = {}
        if 'HTTP_X_ADMIN_KEY' in environ:
            headers[ADMIN_KEY_HEADER] = environ['HTTP_X_ADMIN_KEY']
        response = self.app.handle_request(
            environ.get('REQUEST_METHOD', 'GET'),
            path,
            headers=headers,
            body=body,
            base_url=f'{scheme}://{host}',
        )
        status_line = f"{response['status']} {_http_status_phrase(response['status'])}"
        start_response(status_line, list(response['headers'].items()))
        return [response['body']]


def _http_status_phrase(status_code):
    return {
        200: 'OK',
        201: 'Created',
        302: 'Found',
        400: 'Bad Request',
        401: 'Unauthorized',
        404: 'Not Found',
        405: 'Method Not Allowed',
        410: 'Gone',
    }.get(status_code, 'OK')


def build_wsgi_app(db_path='shortener.db', admin_key=None):
    if admin_key is None:
        admin_key = os.environ.get('SHORTENER_ADMIN_KEY')
    return WsgiUrlShortenerApp(Store(db_path), admin_key=admin_key)


def build_server(db_path, port=8000, host='127.0.0.1', admin_key=None):
    Handler.store = Store(db_path)
    Handler.admin_key = admin_key if admin_key is not None else os.environ.get('SHORTENER_ADMIN_KEY')
    return http.server.ThreadingHTTPServer((host, port), Handler)


def serve(db_path, port=8000, host='127.0.0.1', admin_key=None):
    server = build_server(db_path, port=port, host=host, admin_key=admin_key)
    server.serve_forever()


def main(argv=None):
    parser = argparse.ArgumentParser(description='URL shortener HTTP server')
    parser.add_argument('--db', default='shortener.db')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--admin-key', default=os.environ.get('SHORTENER_ADMIN_KEY'))
    args = parser.parse_args(argv)
    serve(args.db, port=args.port, host=args.host, admin_key=args.admin_key)


if __name__ == '__main__':
    main()
