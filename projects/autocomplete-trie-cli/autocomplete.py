import argparse
import csv
import heapq
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class Suggestion:
    word: str
    weight: int
    distance: int = 0


@dataclass
class TrieNode:
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    is_terminal: bool = False
    weight: int = 0
    max_subtree_weight: int = 0


@dataclass
class SearchStats:
    nodes_visited: int = 0
    candidate_updates: int = 0
    branches_pruned: int = 0
    dynamic_programming_rows: int = 0
    terminals_considered: int = 0
    accepted_matches: int = 0


@dataclass
class QueryResult:
    query: str
    prefix_matches: List[Suggestion]
    fuzzy_matches: List[Suggestion]
    prefix_time_ms: float
    fuzzy_time_ms: float
    prefix_stats: Optional[SearchStats] = None
    fuzzy_stats: Optional[SearchStats] = None


class DatasetError(ValueError):
    pass


class TrieAutocomplete:
    def __init__(self) -> None:
        self.root = TrieNode()
        self.word_count = 0

    def insert(self, word: str, weight: int) -> None:
        if not word:
            raise DatasetError('word must not be empty')
        if weight < 0:
            raise DatasetError('weight must not be negative')

        node = self.root
        node.max_subtree_weight = max(node.max_subtree_weight, weight)
        is_new_word = False
        for ch in word.lower():
            node = node.children.setdefault(ch, TrieNode())
            node.max_subtree_weight = max(node.max_subtree_weight, weight)
        if not node.is_terminal:
            is_new_word = True
        node.is_terminal = True
        node.weight = max(node.weight, weight)
        if is_new_word:
            self.word_count += 1

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        node = self.root
        for ch in prefix.lower():
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def top_k_prefix(
        self,
        prefix: str,
        limit: int,
        collect_stats: bool = False,
    ) -> List[Suggestion] | Tuple[List[Suggestion], SearchStats]:
        stats = SearchStats()
        if limit <= 0:
            return ([], stats) if collect_stats else []
        node = self._find_node(prefix)
        if node is None:
            return ([], stats) if collect_stats else []

        heap: List[Tuple[int, str]] = []
        stack: List[Tuple[TrieNode, str]] = [(node, prefix.lower())]
        while stack:
            current, built = stack.pop()
            stats.nodes_visited += 1
            if current.is_terminal:
                stats.terminals_considered += 1
                candidate = (current.weight, built)
                if len(heap) < limit:
                    heapq.heappush(heap, candidate)
                    stats.candidate_updates += 1
                elif candidate > heap[0]:
                    heapq.heapreplace(heap, candidate)
                    stats.candidate_updates += 1

            children = sorted(
                current.children.items(),
                key=lambda item: (item[1].max_subtree_weight, item[0]),
            )
            for ch, child in children:
                if len(heap) == limit and child.max_subtree_weight < heap[0][0]:
                    stats.branches_pruned += 1
                    continue
                stack.append((child, built + ch))

        results = [Suggestion(word=word, weight=weight) for weight, word in heap]
        ranked = sorted(results, key=lambda item: (-item.weight, item.word))
        return (ranked, stats) if collect_stats else ranked

    def fuzzy_search(
        self,
        query: str,
        limit: int,
        max_distance: int,
        collect_stats: bool = False,
    ) -> List[Suggestion] | Tuple[List[Suggestion], SearchStats]:
        stats = SearchStats()
        if limit <= 0 or max_distance < 0:
            return ([], stats) if collect_stats else []
        query = query.lower()
        initial_row = list(range(len(query) + 1))
        results: List[Suggestion] = []

        def walk(node: TrieNode, prefix: str, previous_row: Sequence[int]) -> None:
            for ch, child in node.children.items():
                stats.nodes_visited += 1
                stats.dynamic_programming_rows += 1
                current_row = [previous_row[0] + 1]
                for col in range(1, len(query) + 1):
                    insert_cost = current_row[col - 1] + 1
                    delete_cost = previous_row[col] + 1
                    replace_cost = previous_row[col - 1] + (query[col - 1] != ch)
                    current_row.append(min(insert_cost, delete_cost, replace_cost))

                next_prefix = prefix + ch
                distance = current_row[-1]
                if child.is_terminal:
                    stats.terminals_considered += 1
                    if distance <= max_distance:
                        results.append(Suggestion(word=next_prefix, weight=child.weight, distance=distance))
                        stats.accepted_matches += 1

                if min(current_row) <= max_distance:
                    walk(child, next_prefix, current_row)
                else:
                    stats.branches_pruned += 1

        walk(self.root, '', initial_row)
        ranked = sorted(results, key=lambda item: (item.distance, -item.weight, item.word))
        deduped: List[Suggestion] = []
        seen = set()
        for item in ranked:
            if item.word in seen:
                continue
            deduped.append(item)
            seen.add(item.word)
            if len(deduped) == limit:
                break
        return (deduped, stats) if collect_stats else deduped


def load_entries(lines: Iterable[str]) -> List[Tuple[str, int]]:
    entries: List[Tuple[str, int]] = []
    reader = csv.reader(line for line in lines if line.strip() and not line.lstrip().startswith('#'))
    for row_number, row in enumerate(reader, start=1):
        if not row:
            continue
        if len(row) != 2:
            raise DatasetError(f'row {row_number} must contain exactly two columns: word,weight')
        word = row[0].strip().lower()
        if not word.isalpha():
            raise DatasetError(f'row {row_number} has invalid word: {row[0]!r}')
        try:
            weight = int(row[1].strip())
        except ValueError as exc:
            raise DatasetError(f'row {row_number} has invalid integer weight: {row[1]!r}') from exc
        if weight < 0:
            raise DatasetError(f'row {row_number} weight must not be negative')
        entries.append((word, weight))
    if not entries:
        raise DatasetError('dataset must contain at least one word,weight row')
    return entries


def build_trie(entries: Iterable[Tuple[str, int]]) -> TrieAutocomplete:
    trie = TrieAutocomplete()
    for word, weight in entries:
        trie.insert(word, weight)
    return trie


def format_suggestions(prefix_results: Sequence[Suggestion], fuzzy_results: Sequence[Suggestion]) -> str:
    lines: List[str] = ['exact_prefix_matches:']
    if prefix_results:
        for item in prefix_results:
            lines.append(f'- {item.word} (weight={item.weight})')
    else:
        lines.append('- none')

    lines.append('')
    lines.append('fuzzy_matches:')
    if fuzzy_results:
        for item in fuzzy_results:
            lines.append(f'- {item.word} (distance={item.distance}, weight={item.weight})')
    else:
        lines.append('- none')
    return '\n'.join(lines)


def format_explain_block(prefix_stats: Optional[SearchStats], fuzzy_stats: Optional[SearchStats]) -> str:
    lines = ['search_explanation:']
    if prefix_stats is None or fuzzy_stats is None:
        lines.append('- unavailable')
        return '\n'.join(lines)
    lines.extend([
        '- prefix_search:',
        f'  - nodes_visited: {prefix_stats.nodes_visited}',
        f'  - terminal_words_considered: {prefix_stats.terminals_considered}',
        f'  - heap_updates: {prefix_stats.candidate_updates}',
        f'  - branches_pruned_by_weight: {prefix_stats.branches_pruned}',
        '- fuzzy_search:',
        f'  - trie_edges_evaluated: {fuzzy_stats.nodes_visited}',
        f'  - dynamic_programming_rows: {fuzzy_stats.dynamic_programming_rows}',
        f'  - terminal_words_considered: {fuzzy_stats.terminals_considered}',
        f'  - accepted_matches_within_distance: {fuzzy_stats.accepted_matches}',
        f'  - branches_pruned_by_distance: {fuzzy_stats.branches_pruned}',
    ])
    return '\n'.join(lines)


def format_query_result(result: QueryResult, explain: bool = False) -> str:
    lines = [f'query: {result.query}']
    lines.append(format_suggestions(result.prefix_matches, result.fuzzy_matches))
    if explain:
        lines.append('')
        lines.append(format_explain_block(result.prefix_stats, result.fuzzy_stats))
    lines.append('')
    lines.append(f'prefix_time_ms: {result.prefix_time_ms:.3f}')
    lines.append(f'fuzzy_time_ms: {result.fuzzy_time_ms:.3f}')
    return '\n'.join(lines)


def format_benchmark_report(results: Sequence[QueryResult], trie: TrieAutocomplete, explain: bool = False) -> str:
    if not results:
        return 'No benchmark queries provided.'
    average_prefix = sum(item.prefix_time_ms for item in results) / len(results)
    average_fuzzy = sum(item.fuzzy_time_ms for item in results) / len(results)
    slowest_prefix = max(results, key=lambda item: item.prefix_time_ms)
    slowest_fuzzy = max(results, key=lambda item: item.fuzzy_time_ms)

    lines = [
        'benchmark_summary:',
        f'- queries: {len(results)}',
        f'- indexed_words: {trie.word_count}',
        f'- avg_prefix_time_ms: {average_prefix:.3f}',
        f'- avg_fuzzy_time_ms: {average_fuzzy:.3f}',
        f'- slowest_prefix_query: {slowest_prefix.query} ({slowest_prefix.prefix_time_ms:.3f} ms)',
        f'- slowest_fuzzy_query: {slowest_fuzzy.query} ({slowest_fuzzy.fuzzy_time_ms:.3f} ms)',
    ]
    if explain:
        total_prefix_nodes = sum((item.prefix_stats.nodes_visited if item.prefix_stats else 0) for item in results)
        total_prefix_pruned = sum((item.prefix_stats.branches_pruned if item.prefix_stats else 0) for item in results)
        total_fuzzy_rows = sum((item.fuzzy_stats.dynamic_programming_rows if item.fuzzy_stats else 0) for item in results)
        total_fuzzy_pruned = sum((item.fuzzy_stats.branches_pruned if item.fuzzy_stats else 0) for item in results)
        lines.extend([
            f'- total_prefix_nodes_visited: {total_prefix_nodes}',
            f'- total_prefix_branches_pruned: {total_prefix_pruned}',
            f'- total_fuzzy_dp_rows: {total_fuzzy_rows}',
            f'- total_fuzzy_branches_pruned: {total_fuzzy_pruned}',
        ])
    lines.extend([
        '',
        'per_query_top_hits:',
    ])
    for item in results:
        prefix_words = ', '.join(match.word for match in item.prefix_matches) or 'none'
        fuzzy_words = ', '.join(match.word for match in item.fuzzy_matches) or 'none'
        line = (
            f'- {item.query}: prefix=[{prefix_words}] fuzzy=[{fuzzy_words}] '
            f'prefix_ms={item.prefix_time_ms:.3f} fuzzy_ms={item.fuzzy_time_ms:.3f}'
        )
        if explain and item.prefix_stats and item.fuzzy_stats:
            line += (
                f' prefix_nodes={item.prefix_stats.nodes_visited}'
                f' prefix_pruned={item.prefix_stats.branches_pruned}'
                f' fuzzy_rows={item.fuzzy_stats.dynamic_programming_rows}'
                f' fuzzy_pruned={item.fuzzy_stats.branches_pruned}'
            )
        lines.append(line)
    return '\n'.join(lines)


def query_to_dict(result: QueryResult) -> Dict[str, object]:
    payload = {
        'query': result.query,
        'prefix_matches': [asdict(item) for item in result.prefix_matches],
        'fuzzy_matches': [asdict(item) for item in result.fuzzy_matches],
        'prefix_time_ms': round(result.prefix_time_ms, 6),
        'fuzzy_time_ms': round(result.fuzzy_time_ms, 6),
    }
    if result.prefix_stats is not None:
        payload['prefix_stats'] = asdict(result.prefix_stats)
    if result.fuzzy_stats is not None:
        payload['fuzzy_stats'] = asdict(result.fuzzy_stats)
    return payload


def benchmark_to_dict(results: Sequence[QueryResult], trie: TrieAutocomplete) -> Dict[str, object]:
    average_prefix = (sum(item.prefix_time_ms for item in results) / len(results)) if results else 0.0
    average_fuzzy = (sum(item.fuzzy_time_ms for item in results) / len(results)) if results else 0.0
    slowest_prefix = max(results, key=lambda item: item.prefix_time_ms) if results else None
    slowest_fuzzy = max(results, key=lambda item: item.fuzzy_time_ms) if results else None
    payload = {
        'query_count': len(results),
        'indexed_words': trie.word_count,
        'avg_prefix_time_ms': round(average_prefix, 6),
        'avg_fuzzy_time_ms': round(average_fuzzy, 6),
        'slowest_prefix_query': query_to_dict(slowest_prefix) if slowest_prefix else None,
        'slowest_fuzzy_query': query_to_dict(slowest_fuzzy) if slowest_fuzzy else None,
        'results': [query_to_dict(item) for item in results],
    }
    if results and any(item.prefix_stats is not None for item in results):
        payload['aggregate_stats'] = {
            'prefix_nodes_visited': sum((item.prefix_stats.nodes_visited if item.prefix_stats else 0) for item in results),
            'prefix_branches_pruned': sum((item.prefix_stats.branches_pruned if item.prefix_stats else 0) for item in results),
            'fuzzy_dynamic_programming_rows': sum((item.fuzzy_stats.dynamic_programming_rows if item.fuzzy_stats else 0) for item in results),
            'fuzzy_branches_pruned': sum((item.fuzzy_stats.branches_pruned if item.fuzzy_stats else 0) for item in results),
        }
    return payload


def normalize_query(raw: str) -> str:
    query = raw.strip().lower()
    if not query:
        raise DatasetError('query must not be empty')
    if not query.isalpha():
        raise DatasetError('query must contain letters only')
    return query


def load_queries(lines: Iterable[str]) -> List[str]:
    queries = [normalize_query(line) for line in lines if line.strip() and not line.lstrip().startswith('#')]
    if not queries:
        raise DatasetError('query file must contain at least one non-empty query line')
    return queries


def run_query(trie: TrieAutocomplete, query: str, limit: int, max_distance: int, explain: bool = False) -> QueryResult:
    prefix_start = time.perf_counter()
    if explain:
        prefix_matches, prefix_stats = trie.top_k_prefix(query, limit, collect_stats=True)
    else:
        prefix_matches = trie.top_k_prefix(query, limit)
        prefix_stats = None
    prefix_time_ms = (time.perf_counter() - prefix_start) * 1000

    prefix_words = {match.word for match in prefix_matches}
    fuzzy_start = time.perf_counter()
    if explain:
        fuzzy_candidates, fuzzy_stats = trie.fuzzy_search(query, limit, max_distance, collect_stats=True)
    else:
        fuzzy_candidates = trie.fuzzy_search(query, limit, max_distance)
        fuzzy_stats = None
    fuzzy_matches = [
        item for item in fuzzy_candidates
        if item.word not in prefix_words
    ]
    fuzzy_time_ms = (time.perf_counter() - fuzzy_start) * 1000

    return QueryResult(
        query=query,
        prefix_matches=prefix_matches,
        fuzzy_matches=fuzzy_matches,
        prefix_time_ms=prefix_time_ms,
        fuzzy_time_ms=fuzzy_time_ms,
        prefix_stats=prefix_stats,
        fuzzy_stats=fuzzy_stats,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Weighted trie autocomplete with typo-tolerant fuzzy search')
    parser.add_argument('dataset', help='CSV-like text file containing word,weight rows')
    parser.add_argument('query', nargs='?', help='prefix or typo-prone query string')
    parser.add_argument('--batch-file', help='optional file of one query per line for benchmark mode')
    parser.add_argument('--limit', type=int, default=5, help='maximum number of suggestions per section')
    parser.add_argument('--max-distance', type=int, default=1, help='maximum edit distance for fuzzy matches')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON output')
    parser.add_argument('--explain', action='store_true', help='include traversal/pruning diagnostics for portfolio walkthroughs')
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.limit <= 0:
        parser.exit(2, 'argument error: --limit must be positive\n')
    if args.max_distance < 0:
        parser.exit(2, 'argument error: --max-distance must be non-negative\n')
    if bool(args.query) == bool(args.batch_file):
        parser.exit(2, 'argument error: provide exactly one of QUERY or --batch-file\n')

    try:
        entries = load_entries(Path(args.dataset).read_text(encoding='utf-8').splitlines())
        trie = build_trie(entries)
        if args.batch_file:
            queries = load_queries(Path(args.batch_file).read_text(encoding='utf-8').splitlines())
            results = [run_query(trie, query, args.limit, args.max_distance, explain=args.explain) for query in queries]
            if args.json:
                print(json.dumps(benchmark_to_dict(results, trie), indent=2))
            else:
                print(format_benchmark_report(results, trie, explain=args.explain))
        else:
            result = run_query(trie, normalize_query(args.query), args.limit, args.max_distance, explain=args.explain)
            if args.json:
                print(json.dumps(query_to_dict(result), indent=2))
            else:
                print(format_query_result(result, explain=args.explain))
    except OSError as exc:
        parser.exit(2, f'file error: {exc}\n')
    except DatasetError as exc:
        parser.exit(2, f'dataset error: {exc}\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
