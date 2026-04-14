import argparse
import json
import re
from pathlib import Path

TAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_-]+)')
FRONT_MATTER_TAGS_RE = re.compile(r'^tags\s*:\s*(.+)$', re.IGNORECASE)
QUERY_TOKEN_RE = re.compile(r'"[^"]+"|\(|\)|\bAND\b|\bOR\b|\bNOT\b|[^\s()]+', re.IGNORECASE)
BOOLEAN_OPERATORS = {'AND', 'OR', 'NOT'}
PRECEDENCE = {'OR': 1, 'AND': 2, 'NOT': 3}


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
    haystacks = [note['name'].lower(), note['path'].lower(), note['text'].lower(), *[tag.lower() for tag in note['tags']]]
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
                snippet = extract_snippet(note['text'], term)
                if snippet:
                    break
        else:
            score = score_note(note, query)
            if score <= 0:
                continue
            snippet = extract_snippet(note['text'], query)

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
