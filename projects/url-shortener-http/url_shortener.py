import argparse, http.server, json, sqlite3, string
from pathlib import Path

ALPHABET = string.ascii_letters + string.digits

class Store:
    def __init__(self, db_path='shortener.db'):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS links (code TEXT PRIMARY KEY, url TEXT NOT NULL)')

    def shorten(self, url):
        code = hex(abs(hash(url)))[2:8]
        with self._connect() as conn:
            conn.execute('INSERT OR REPLACE INTO links(code, url) VALUES (?, ?)', (code, url))
        return code

    def resolve(self, code):
        with self._connect() as conn:
            row = conn.execute('SELECT url FROM links WHERE code = ?', (code,)).fetchone()
            return row['url'] if row else None

class Handler(http.server.BaseHTTPRequestHandler):
    store = None

    def do_POST(self):
        if self.path != '/shorten':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length).decode())
        code = self.store.shorten(payload['url'])
        body = json.dumps({'code': code}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        code = self.path.lstrip('/')
        url = self.store.resolve(code)
        if not url:
            self.send_error(404)
            return
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()


def serve(db_path, port=8000):
    Handler.store = Store(db_path)
    server = http.server.HTTPServer(('127.0.0.1', port), Handler)
    server.serve_forever()


def main(argv=None):
    p = argparse.ArgumentParser(description='URL shortener HTTP server')
    p.add_argument('--db', default='shortener.db')
    p.add_argument('--port', type=int, default=8000)
    args = p.parse_args(argv)
    serve(args.db, args.port)

if __name__ == '__main__':
    main()
