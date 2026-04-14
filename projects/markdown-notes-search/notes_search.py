import argparse, re
from pathlib import Path

TAG_RE = re.compile(r'#([A-Za-z0-9_-]+)')

def index_notes(directory):
    notes = []
    for path in sorted(Path(directory).glob('*.md')):
        text = path.read_text(encoding='utf-8')
        notes.append({'name': path.name, 'tags': TAG_RE.findall(text), 'text': text})
    return notes


def search_notes(notes, query):
    q = query.lower()
    return [n for n in notes if q in n['name'].lower() or q in n['text'].lower() or q in [t.lower() for t in n['tags']]]


def main(argv=None):
    p = argparse.ArgumentParser(description='Markdown notes search')
    p.add_argument('directory')
    p.add_argument('query')
    args = p.parse_args(argv)
    for note in search_notes(index_notes(args.directory), args.query):
        print(note['name'])

if __name__ == '__main__':
    main()
