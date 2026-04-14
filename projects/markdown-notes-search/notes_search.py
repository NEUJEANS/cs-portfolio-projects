import argparse
import json
import re
from pathlib import Path

TAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_-]+)')
FRONT_MATTER_TAGS_RE = re.compile(r'^tags\s*:\s*(.+)$', re.IGNORECASE)
QUERY_TOKEN_RE = re.compile(r'"[^"]+"|\(|\)|\bAND\b|\bOR\b|\bNOT\b|[^\s()]+', re.IGNORECASE)
BOOLEAN_OPERATORS = {'AND', 'OR', 'NOT'}
PRECEDENCE = {'OR': 1, 'AND': 2, 'NOT': 3}
DEFAULT_INDEX_FILENAME = '.notes_search_index.json'
INDEX_VERSION = 2
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')
MARKDOWN_LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')


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


def extract_headings(text):
    headings = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            heading = stripped.lstrip('#').strip()
            if heading:
                headings.append(heading)
    return headings


def normalize_link_target(raw_target):
    target = raw_target.strip()
    if not target or '://' in target or target.startswith('#'):
        return None
    target = target.split('#', 1)[0].strip()
    if not target:
        return None
    if target.endswith('.md'):
        target = target[:-3]
    return target.replace('\\', '/').strip().lower()


def extract_outgoing_links(text):
    outgoing = set()
    for match in WIKILINK_RE.findall(text):
        normalized = normalize_link_target(match)
        if normalized:
            outgoing.add(normalized)
    for raw_target in MARKDOWN_LINK_RE.findall(text):
        normalized = normalize_link_target(raw_target)
        if normalized:
            outgoing.add(normalized)
    return sorted(outgoing)


def build_note_record(base, path):
    text = path.read_text(encoding='utf-8')
    metadata = parse_front_matter(text)
    body = strip_front_matter(text)
    tags = sorted({*TAG_RE.findall(body), *metadata.get('tags', [])}, key=str.lower)
    relative_path = path.relative_to(base)
    stat = path.stat()
    return {
        'name': path.name,
        'path': str(relative_path),
        'tags': tags,
        'text': body,
        'headings': extract_headings(body),
        'outgoing_links': extract_outgoing_links(body),
        'backlinks': [],
        'metadata': metadata,
        'source': {
            'mtime_ns': stat.st_mtime_ns,
            'size': stat.st_size,
        },
    }


def load_index_cache(index_path):
    if not index_path.exists():
        return {}
    try:
        payload = json.loads(index_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get('version') != INDEX_VERSION:
        return {}
    entries = payload.get('entries', {})
    return entries if isinstance(entries, dict) else {}


def save_index_cache(index_path, entries):
    serializable_entries = {path: value for path, value in sorted(entries.items())}
    payload = {
        'version': INDEX_VERSION,
        'entries': serializable_entries,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def cache_matches_signature(cached_note, stat_result):
    source = cached_note.get('source', {})
    return source.get('mtime_ns') == stat_result.st_mtime_ns and source.get('size') == stat_result.st_size


def resolve_index_path(base, index_file):
    if not index_file:
        return base / DEFAULT_INDEX_FILENAME
    candidate = Path(index_file)
    return candidate if candidate.is_absolute() else base / candidate


def note_link_aliases(note):
    path_without_suffix = str(Path(note['path']).with_suffix('')).lower()
    name_without_suffix = Path(note['name']).stem.lower()
    return {path_without_suffix, name_without_suffix}


def apply_backlinks(notes):
    alias_to_path = {}
    for note in notes:
        for alias in note_link_aliases(note):
            alias_to_path[alias] = note['path']

    backlinks_map = {note['path']: set() for note in notes}
    for note in notes:
        for outgoing in note.get('outgoing_links', []):
            target_path = alias_to_path.get(outgoing)
            if target_path and target_path != note['path']:
                backlinks_map[target_path].add(note['path'])

    for note in notes:
        note['backlinks'] = sorted(backlinks_map[note['path']])
    return notes


def index_notes(directory, recursive=False, index_file=None, rebuild_index=False):
    notes = []
    base = Path(directory)
    pattern = '**/*.md' if recursive else '*.md'
    paths = [path for path in sorted(base.glob(pattern)) if path.is_file()]

    if index_file is None and not rebuild_index:
        for path in paths:
            notes.append(build_note_record(base, path))
        return apply_backlinks(notes)

    index_path = resolve_index_path(base, index_file)
    cached_entries = {} if rebuild_index else load_index_cache(index_path)
    refreshed_entries = {}

    for path in paths:
        relative_path = str(path.relative_to(base))
        stat_result = path.stat()
        cached_note = cached_entries.get(relative_path)
        if cached_note and cache_matches_signature(cached_note, stat_result):
            refreshed_entries[relative_path] = cached_note
        else:
            refreshed_entries[relative_path] = build_note_record(base, path)

    notes = [refreshed_entries[relative_path] for relative_path in sorted(refreshed_entries)]
    apply_backlinks(notes)
    refreshed_entries = {note['path']: note for note in notes}
    save_index_cache(index_path, refreshed_entries)
    return notes


def score_note(note, query):
    q = query.lower()
    name_lower = note['name'].lower()
    path_lower = note['path'].lower()
    text_lower = note['text'].lower()
    tag_lowers = [tag.lower() for tag in note['tags']]
    heading_lowers = [heading.lower() for heading in note.get('headings', [])]

    score = 0
    if q == name_lower:
        score += 120
    if q in name_lower:
        score += 60
    if q in path_lower and path_lower != name_lower:
        score += 25
    if q in tag_lowers:
        score += 80
    if q in heading_lowers:
        score += 95
    heading_substring_hits = sum(1 for heading in heading_lowers if q in heading and q != heading)
    score += heading_substring_hits * 35

    word_hits = len(re.findall(rf'(?<!\w){re.escape(q)}(?!\w)', text_lower))
    substring_hits = text_lower.count(q)
    score += word_hits * 15
    score += max(0, substring_hits - word_hits) * 4
    score += len(note['tags'])
    score += min(len(note.get('backlinks', [])), 5) * 3
    return score


def tokenize_query(query):
    raw_tokens = QUERY_TOKEN_RE.findall(query)
    tokens = []
    previous_was_operand = False
    for raw in raw_tokens:
        upper = raw.upper()
        if raw in ('(', ')') or upper in BOOLEAN_OPERATORS:
            token = {'type': upper if upper in BOOLEAN_OPERATORS else raw}
        else:
            value = raw[1:-1] if raw.startswith('"') and raw.endswith('"') else raw
            token = {'type': 'TERM', 'value': value}

        is_operand_start = token['type'] in {'TERM', '(', 'NOT'}
        if previous_was_operand and is_operand_start:
            tokens.append({'type': 'AND'})

        tokens.append(token)
        previous_was_operand = token['type'] in {'TERM', ')'}
    return tokens


def to_postfix(tokens):
    output = []
    operators = []
    for token in tokens:
        token_type = token['type']
        if token_type == 'TERM':
            output.append(token)
        elif token_type == '(':
            operators.append(token)
        elif token_type == ')':
            while operators and operators[-1]['type'] != '(':
                output.append(operators.pop())
            if not operators:
                raise ValueError('unmatched closing parenthesis in query')
            operators.pop()
        else:
            while operators and operators[-1]['type'] != '(':
                top_type = operators[-1]['type']
                if PRECEDENCE[top_type] > PRECEDENCE[token_type] or (
                    PRECEDENCE[top_type] == PRECEDENCE[token_type] and token_type != 'NOT'
                ):
                    output.append(operators.pop())
                else:
                    break
            operators.append(token)

    while operators:
        operator = operators.pop()
        if operator['type'] == '(':
            raise ValueError('unmatched opening parenthesis in query')
        output.append(operator)
    return output


def query_term_matches(note, term):
    q = term.lower()
    haystacks = [
        note['name'].lower(),
        note['path'].lower(),
        note['text'].lower(),
        *[tag.lower() for tag in note['tags']],
        *[heading.lower() for heading in note.get('headings', [])],
        *[path.lower() for path in note.get('backlinks', [])],
    ]
    return any(q in haystack for haystack in haystacks)


def evaluate_postfix(postfix_tokens, note):
    stack = []
    positive_terms = []
    for token in postfix_tokens:
        token_type = token['type']
        if token_type == 'TERM':
            matches = query_term_matches(note, token['value'])
            stack.append(matches)
            positive_terms.append(token['value'])
        elif token_type == 'NOT':
            if not stack:
                raise ValueError('NOT must follow a query term or expression')
            stack.append(not stack.pop())
        else:
            if len(stack) < 2:
                raise ValueError(f'{token_type} requires two operands')
            right = stack.pop()
            left = stack.pop()
            stack.append(left and right if token_type == 'AND' else left or right)
    if len(stack) != 1:
        raise ValueError('invalid query expression')
    return stack[0], positive_terms


def is_boolean_query(query):
    return bool(re.search(r'\b(?:AND|OR|NOT)\b|["()]', query, re.IGNORECASE))


def best_snippet_for_query(note, query):
    for heading in note.get('headings', []):
        if query.lower() in heading.lower():
            return f'Heading: {heading}'
    snippet = extract_snippet(note['text'], query)
    if snippet:
        return snippet
    for backlink in note.get('backlinks', []):
        if query.lower() in backlink.lower():
            return f'Backlinked from: {backlink}'
    return ''


def search_notes(notes, query, limit=None):
    query = query.strip()
    if not query:
        return []
    if limit is not None and limit <= 0:
        raise ValueError('limit must be positive when provided')

    results = []
    postfix = None
    boolean_mode = is_boolean_query(query)
    if boolean_mode:
        postfix = to_postfix(tokenize_query(query))

    for note in notes:
        if boolean_mode:
            matched, positive_terms = evaluate_postfix(postfix, note)
            if not matched:
                continue
            matched_terms = []
            seen = set()
            for term in positive_terms:
                normalized = term.lower()
                if normalized in seen or not query_term_matches(note, term):
                    continue
                seen.add(normalized)
                matched_terms.append(term)
            score = sum(score_note(note, term) for term in matched_terms) + len(matched_terms) * 10
            if not matched_terms:
                score = max(score, 1 + len(note['tags']))
            snippet = ''
            for term in matched_terms:
                snippet = best_snippet_for_query(note, term)
                if snippet:
                    break
        else:
            score = score_note(note, query)
            if score <= 0:
                continue
            snippet = best_snippet_for_query(note, query)

        if not boolean_mode and score <= 0:
            continue

        result = dict(note)
        result['score'] = score
        result['snippet'] = snippet
        results.append(result)

    results.sort(key=lambda note: (-note['score'], note['path'].lower()))
    if limit is not None:
        return results[:limit]
    return results


def format_result(note, show_backlinks=False):
    tags = f" [{' '.join('#' + tag for tag in note['tags'])}]" if note['tags'] else ''
    snippet = f"\n  {note['snippet']}" if note.get('snippet') else ''
    backlinks = ''
    if show_backlinks and note.get('backlinks'):
        backlinks = f"\n  backlinks: {', '.join(note['backlinks'])}"
    return f"{note['path']} (score={note['score']}){tags}{snippet}{backlinks}"


def main(argv=None):
    parser = argparse.ArgumentParser(description='Markdown notes search')
    parser.add_argument('directory')
    parser.add_argument('query')
    parser.add_argument('--recursive', action='store_true', help='search nested directories for Markdown files')
    parser.add_argument('--limit', type=int, default=None, help='maximum number of results to return')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    parser.add_argument('--show-backlinks', action='store_true', help='include backlink references in plain-text output')
    parser.add_argument(
        '--index-file',
        default=None,
        help='persist and reuse note metadata in a JSON index file (defaults to .notes_search_index.json inside the notes directory when enabled)',
    )
    parser.add_argument('--rebuild-index', action='store_true', help='ignore any existing cached index contents and rebuild it')
    args = parser.parse_args(argv)

    use_index = args.index_file is not None or args.rebuild_index
    notes = index_notes(
        args.directory,
        recursive=args.recursive,
        index_file=args.index_file if use_index else None,
        rebuild_index=args.rebuild_index,
    )
    results = search_notes(notes, args.query, limit=args.limit)
    if args.json:
        payload = [
            {
                'name': note['name'],
                'path': note['path'],
                'tags': note['tags'],
                'headings': note['headings'],
                'backlinks': note['backlinks'],
                'score': note['score'],
                'snippet': note['snippet'],
            }
            for note in results
        ]
        print(json.dumps(payload, indent=2))
        return

    for note in results:
        print(format_result(note, show_backlinks=args.show_backlinks))


if __name__ == '__main__':
    main()
