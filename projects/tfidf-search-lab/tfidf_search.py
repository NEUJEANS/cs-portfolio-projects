import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
DEFAULT_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'in', 'is',
    'it', 'of', 'on', 'or', 'that', 'the', 'to', 'with'
}


class CorpusError(ValueError):
    pass


@dataclass(frozen=True)
class SearchResult:
    path: str
    score: float
    matched_terms: List[str]
    contributions: List[Tuple[str, float]]


@dataclass
class IndexedDocument:
    path: str
    tf: Counter
    weights: Dict[str, float]
    norm: float
    total_terms: int


class TfIdfSearchEngine:
    def __init__(self, stopwords: Optional[Iterable[str]] = None) -> None:
        self.stopwords = set(stopwords or DEFAULT_STOPWORDS)
        self.documents: Dict[str, IndexedDocument] = {}
        self.doc_freq: Counter = Counter()
        self.postings: DefaultDict[str, List[str]] = defaultdict(list)

    def reset(self) -> None:
        self.documents = {}
        self.doc_freq = Counter()
        self.postings = defaultdict(list)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return TOKEN_RE.findall(text.lower())

    def normalize_tokens(self, text: str) -> List[str]:
        return [token for token in self.tokenize(text) if token not in self.stopwords]

    def build_from_directory(self, root: Path) -> None:
        self.reset()
        if not root.exists() or not root.is_dir():
            raise CorpusError(f'corpus directory does not exist: {root}')

        paths = sorted(
            path for path in root.rglob('*')
            if path.is_file() and path.suffix.lower() in {'.txt', '.md'}
        )
        if not paths:
            raise CorpusError('corpus must contain at least one .txt or .md file')

        raw_docs: Dict[str, Counter] = {}
        for path in paths:
            tokens = self.normalize_tokens(path.read_text(encoding='utf-8'))
            if not tokens:
                continue
            rel_path = str(path.relative_to(root))
            counts = Counter(tokens)
            raw_docs[rel_path] = counts
            for term in counts:
                self.doc_freq[term] += 1
                self.postings[term].append(rel_path)

        if not raw_docs:
            raise CorpusError('corpus files did not contain any indexable tokens after filtering')

        total_docs = len(raw_docs)
        for rel_path, counts in raw_docs.items():
            weights: Dict[str, float] = {}
            total_terms = sum(counts.values())
            for term, count in counts.items():
                tf = count / total_terms
                idf = math.log((1 + total_docs) / (1 + self.doc_freq[term])) + 1
                weights[term] = tf * idf
            norm = math.sqrt(sum(value * value for value in weights.values())) or 1.0
            self.documents[rel_path] = IndexedDocument(
                path=rel_path,
                tf=counts,
                weights=weights,
                norm=norm,
                total_terms=total_terms,
            )

        for term, docs in self.postings.items():
            self.postings[term] = sorted(docs)

    def _query_weights(self, query: str) -> Dict[str, float]:
        tokens = self.normalize_tokens(query)
        if not tokens:
            raise CorpusError('query must contain at least one non-stopword token')

        counts = Counter(tokens)
        total_terms = sum(counts.values())
        total_docs = len(self.documents)
        weights: Dict[str, float] = {}
        for term, count in counts.items():
            tf = count / total_terms
            df = self.doc_freq.get(term, 0)
            idf = math.log((1 + total_docs) / (1 + df)) + 1
            weights[term] = tf * idf
        return weights

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        if limit <= 0:
            return []
        if not self.documents:
            raise CorpusError('index has not been built')

        query_weights = self._query_weights(query)
        query_norm = math.sqrt(sum(value * value for value in query_weights.values())) or 1.0
        candidate_docs = set()
        for term in query_weights:
            candidate_docs.update(self.postings.get(term, []))

        results: List[SearchResult] = []
        for path in sorted(candidate_docs):
            document = self.documents[path]
            contributions = []
            dot_product = 0.0
            for term, query_weight in query_weights.items():
                contribution = query_weight * document.weights.get(term, 0.0)
                if contribution > 0:
                    contributions.append((term, contribution))
                    dot_product += contribution
            if dot_product == 0:
                continue
            score = dot_product / (query_norm * document.norm)
            contributions.sort(key=lambda item: (-item[1], item[0]))
            results.append(
                SearchResult(
                    path=path,
                    score=score,
                    matched_terms=[term for term, _ in contributions],
                    contributions=contributions,
                )
            )

        return sorted(results, key=lambda item: (-item.score, item.path))[:limit]

    def stats(self) -> Dict[str, int]:
        return {
            'documents': len(self.documents),
            'terms': len(self.doc_freq),
            'postings': sum(len(paths) for paths in self.postings.values()),
        }


def format_results(results: Sequence[SearchResult]) -> str:
    if not results:
        return 'no matches'
    lines = []
    for item in results:
        explain = ', '.join(f'{term}={value:.4f}' for term, value in item.contributions)
        matched = ', '.join(item.matched_terms)
        lines.append(f'{item.path} | score={item.score:.4f} | terms=[{matched}] | contributions=[{explain}]')
    return '\n'.join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Search a local text corpus with an inverted index and TF-IDF ranking')
    parser.add_argument('corpus', help='directory containing .txt and .md documents')
    parser.add_argument('query', help='search query string')
    parser.add_argument('--limit', type=int, default=5, help='maximum number of results to print')
    parser.add_argument('--stats', action='store_true', help='print corpus stats before results')
    parser.add_argument('--json', action='store_true', help='print results as JSON')
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit <= 0:
        parser.exit(2, 'argument error: --limit must be positive\n')

    engine = TfIdfSearchEngine()
    try:
        engine.build_from_directory(Path(args.corpus))
        results = engine.search(args.query, args.limit)
    except (OSError, UnicodeDecodeError) as exc:
        parser.exit(2, f'file error: {exc}\n')
    except CorpusError as exc:
        parser.exit(2, f'corpus error: {exc}\n')

    if args.json:
        payload = {
            'stats': engine.stats() if args.stats else None,
            'results': [
                {
                    'path': item.path,
                    'score': round(item.score, 6),
                    'matched_terms': item.matched_terms,
                    'contributions': [
                        {'term': term, 'score': round(score, 6)} for term, score in item.contributions
                    ],
                }
                for item in results
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.stats:
        stats = engine.stats()
        print(f"documents={stats['documents']} terms={stats['terms']} postings={stats['postings']}")
    print(format_results(results))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
