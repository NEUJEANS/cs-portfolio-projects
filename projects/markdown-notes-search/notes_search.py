import argparse
import json
import re
from pathlib import Path

TAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_-]+)')
FRONT_MATTER_TAGS_RE = re.compile(r'^tags\s*:\s*(.+)$', re.IGNORECASE)


def parse_front_matter(text):
    if not text.startswith('---\n'):
        return {}

    lines = text.splitlines()
    metadata = {}
    for line in lines[1:]:
        if line.strip() == '---':
            return metadata
        match = FRONT_MATTER_TAGS_RE.match(line.strip())
        if match:
            raw = match.group(1).strip()
            if raw.startswith('[') and raw.endswith(']'):
                values = [item.strip().strip('"\'') for item in raw[1:-1].split(',') if item.strip()]
            else:
                values = [item.strip().strip('"\'') for item in raw.split(',') if item.strip()]
            metadata['tags'] = values
    return metadata


def strip_front_matter(text):
    if not text.startswith('---\n'):
        return text

    lines = text.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            return '\n'.join(lines[index + 1 :])
    return text


def extract_snippet(text, query, radius=55):
    query_lower = query.lower()
    index = text.lower().find(query_lower)
    if index == -1:
        return ''

    start = max(0, index - radius)
    end = min(len(text), index + len(query) + radius)
    snippet = text[start:end].replace('\n', ' ')
    snippet = re.sub(r'\s+', ' ', snippet).strip()
    if start > 0:
        snippet = '…' + snippet
    if end < len(text):
        snippet = snippet + '…'
    return snippet


def index_notes(directory, recursive=False):
    notes = []
    base = Path(directory)
    pattern = '**/*.md' if recursive else '*.md'
    for path in sorted(base.glob(pattern)):
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8')
        metadata = parse_front_matter(text)
        body = strip_front_matter(text)
        tags = sorted({*TAG_RE.findall(body), *metadata.get('tags', [])}, key=str.lower)
        relative_path = path.relative_to(base)
        notes.append(
            {
                'name': path.name,
                'path': str(relative_path),
                'tags': tags,
                'text': body,
                'metadata': metadata,
            }
        )
    return notes


def score_note(note, query):
    q = query.lower()
    name_lower = note['name'].lower()
    path_lower = note['path'].lower()
    text_lower = note['text'].lower()
    tag_lowers = [tag.lower() for tag in note['tags']]

    score = 0
    if q == name_lower:
        score += 120
    if q in name_lower:
        score += 60
    if q in path_lower and path_lower != name_lower:
        score += 25
    if q in tag_lowers:
        score += 80

    word_hits = len(re.findall(rf'(?<!\w){re.escape(q)}(?!\w)', text_lower))
    substring_hits = text_lower.count(q)
    score += word_hits * 15
    score += max(0, substring_hits - word_hits) * 4
    score += len(note['tags'])
    return score


def search_notes(notes, query, limit=None):
    query = query.strip()
    if not query:
        return []
    if limit is not None and limit <= 0:
        raise ValueError('limit must be positive when provided')

    results = []
    for note in notes:
        score = score_note(note, query)
        if score <= 0:
            continue
        result = dict(note)
        result['score'] = score
        result['snippet'] = extract_snippet(note['text'], query)
        results.append(result)

    results.sort(key=lambda note: (-note['score'], note['path'].lower()))
    if limit is not None:
        return results[:limit]
    return results


def format_result(note):
    tags = f" [{' '.join('#' + tag for tag in note['tags'])}]" if note['tags'] else ''
    snippet = f"\n  {note['snippet']}" if note.get('snippet') else ''
    return f"{note['path']} (score={note['score']}){tags}{snippet}"


def main(argv=None):
    parser = argparse.ArgumentParser(description='Markdown notes search')
    parser.add_argument('directory')
    parser.add_argument('query')
    parser.add_argument('--recursive', action='store_true', help='search nested directories for Markdown files')
    parser.add_argument('--limit', type=int, default=None, help='maximum number of results to return')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    args = parser.parse_args(argv)

    results = search_notes(index_notes(args.directory, recursive=args.recursive), args.query, limit=args.limit)
    if args.json:
        payload = [
            {
                'name': note['name'],
                'path': note['path'],
                'tags': note['tags'],
                'score': note['score'],
                'snippet': note['snippet'],
            }
            for note in results
        ]
        print(json.dumps(payload, indent=2))
        return

    for note in results:
        print(format_result(note))


if __name__ == '__main__':
    main()
