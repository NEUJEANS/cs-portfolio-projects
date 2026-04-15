import os

from url_shortener import build_wsgi_app

app = build_wsgi_app(os.environ.get('SHORTENER_DB', 'shortener.db'))
