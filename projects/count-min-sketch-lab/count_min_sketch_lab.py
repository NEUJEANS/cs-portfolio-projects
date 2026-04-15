from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class SketchConfig:
    epsilon: float = 0.02
    delta: float = 0.01
    seed: int = 0
    conservative_update: bool = False

    @property
    def width(self) -> int:
        return max(1, math.ceil(math.e / self.epsilon))

    @property
    def depth(self) -> int:
        return max(1, math.ceil(math.log(1 / self.delta)))


class CountMinSketch:
    def __init__(
        self,
        epsilon: float = 0.02,
        delta: float = 0.01,
        seed: int = 0,
        conservative_update: bool = False,
    ) -> None:
        if epsilon <= 0 or delta <= 0 or delta >= 1:
            raise ValueError('epsilon must be > 0 and delta must be in (0, 1)')
        self.config = SketchConfig(
            epsilon=epsilon,
            delta=delta,
            seed=seed,
            conservative_update=conservative_update,
        )
        self.width = self.config.width
        self.depth = self.config.depth
        self.tables: List[List[int]] = [[0] * self.width for _ in range(self.depth)]
        self.total_count = 0
        self._observed: Counter[str] = Counter()

    def _index_for(self, item: str, row: int) -> int:
        payload = f'{self.config.seed}:{row}:{item}'.encode('utf-8')
        digest = hashlib.blake2b(payload, digest_size=8).digest()
        return int.from_bytes(digest, 'big') % self.width

    def _cell_locations(self, item: str) -> List[tuple[int, int]]:
        return [(row, self._index_for(item, row)) for row in range(self.depth)]

    def _add_standard(self, item: str, count: int) -> None:
        for row, column in self._cell_locations(item):
            self.tables[row][column] += count

    def _add_conservative(self, item: str, count: int) -> None:
        locations = self._cell_locations(item)
        for _ in range(count):
            current_values = [self.tables[row][column] for row, column in locations]
            minimum = min(current_values)
            for row, column in locations:
                if self.tables[row][column] == minimum:
                    self.tables[row][column] += 1

    def add(self, item: str, count: int = 1) -> None:
        if count < 0:
            raise ValueError('count must be non-negative')
        if count == 0:
            return
        if self.config.conservative_update:
            self._add_conservative(item, count)
        else:
            self._add_standard(item, count)
        self.total_count += count
        self._observed[item] += count

    def estimate(self, item: str) -> int:
        if self.total_count == 0:
            return 0
        return min(self.tables[row][self._index_for(item, row)] for row in range(self.depth))

    def merge(self, other: 'CountMinSketch') -> None:
        if (
            self.width != other.width
            or self.depth != other.depth
            or self.config.seed != other.config.seed
            or self.config.conservative_update != other.config.conservative_update
        ):
            raise ValueError('sketches must share width, depth, seed, and update mode to merge')
        for row in range(self.depth):
            for column in range(self.width):
                self.tables[row][column] += other.tables[row][column]
        self.total_count += other.total_count
        self._observed.update(other._observed)

    def heavy_hitters(self, threshold: int) -> List[Dict[str, int]]:
        if threshold < 0:
            raise ValueError('threshold must be non-negative')
        hitters = []
        for item in sorted(self._observed):
            estimate = self.estimate(item)
            if estimate >= threshold:
                hitters.append(
                    {
                        'item': item,
                        'estimate': estimate,
                        'exact_count': self._observed[item],
                    }
                )
        hitters.sort(key=lambda entry: (-entry['estimate'], entry['item']))
        return hitters

    def error_bound(self) -> float:
        return self.config.epsilon * self.total_count

    def to_dict(self) -> Dict[str, object]:
        return {
            'epsilon': self.config.epsilon,
            'delta': self.config.delta,
            'seed': self.config.seed,
            'conservative_update': self.config.conservative_update,
            'width': self.width,
            'depth': self.depth,
            'total_count': self.total_count,
            'tables': self.tables,
            'observed': dict(self._observed),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> 'CountMinSketch':
        sketch = cls(
            epsilon=float(payload['epsilon']),
            delta=float(payload['delta']),
            seed=int(payload.get('seed', 0)),
            conservative_update=bool(payload.get('conservative_update', False)),
        )
        sketch.tables = [list(map(int, row)) for row in payload['tables']]
        if len(sketch.tables) != sketch.depth or any(len(row) != sketch.width for row in sketch.tables):
            raise ValueError('serialized table shape does not match epsilon/delta-derived dimensions')
        sketch.total_count = int(payload['total_count'])
        sketch._observed = Counter({str(k): int(v) for k, v in dict(payload.get('observed', {})).items()})
        return sketch


def build_sketch(
    items: Iterable[str],
    epsilon: float,
    delta: float,
    seed: int = 0,
    conservative_update: bool = False,
) -> CountMinSketch:
    sketch = CountMinSketch(
        epsilon=epsilon,
        delta=delta,
        seed=seed,
        conservative_update=conservative_update,
    )
    for item in items:
        if item:
            sketch.add(item)
    return sketch


def load_tokens_from_text(text: str) -> List[str]:
    return [token.strip() for token in text.split() if token.strip()]


def load_tokens_from_file(path: Path) -> List[str]:
    return load_tokens_from_text(path.read_text(encoding='utf-8'))


def save_sketch(path: Path, sketch: CountMinSketch) -> None:
    path.write_text(json.dumps(sketch.to_dict(), indent=2), encoding='utf-8')


def load_sketch(path: Path) -> CountMinSketch:
    return CountMinSketch.from_dict(json.loads(path.read_text(encoding='utf-8')))


def deep_size_bytes(value: Any, seen: set[int] | None = None) -> int:
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)

    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size_bytes(key, seen) + deep_size_bytes(item, seen) for key, item in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        size += sum(deep_size_bytes(item, seen) for item in value)
    elif hasattr(value, '__dict__'):
        size += deep_size_bytes(vars(value), seen)
    return size


def sketch_core_size_bytes(sketch: CountMinSketch) -> int:
    return deep_size_bytes(sketch.tables)


def benchmark_memory(
    items: Sequence[str],
    epsilon: float,
    delta: float,
    seed: int = 0,
    sample_size: int = 10,
    conservative_update: bool = False,
) -> Dict[str, Any]:
    sketch = build_sketch(
        items,
        epsilon=epsilon,
        delta=delta,
        seed=seed,
        conservative_update=conservative_update,
    )
    exact_counter = Counter(items)
    top_items = exact_counter.most_common(max(0, sample_size))

    sketch_core_bytes = sketch_core_size_bytes(sketch)
    sketch_full_bytes = deep_size_bytes(sketch)
    exact_bytes = deep_size_bytes(exact_counter)

    sample_estimates = []
    for item, exact_count in top_items:
        estimate = sketch.estimate(item)
        sample_estimates.append(
            {
                'item': item,
                'exact_count': exact_count,
                'estimate': estimate,
                'overestimate': estimate - exact_count,
            }
        )

    return {
        'stream_items': len(items),
        'unique_items': len(exact_counter),
        'epsilon': epsilon,
        'delta': delta,
        'width': sketch.width,
        'depth': sketch.depth,
        'seed': seed,
        'conservative_update': conservative_update,
        'exact_counter_bytes': exact_bytes,
        'sketch_core_bytes': sketch_core_bytes,
        'sketch_full_bytes': sketch_full_bytes,
        'core_vs_exact_ratio': round(sketch_core_bytes / exact_bytes, 4) if exact_bytes else None,
        'full_vs_exact_ratio': round(sketch_full_bytes / exact_bytes, 4) if exact_bytes else None,
        'error_bound': sketch.error_bound(),
        'top_item_estimates': sample_estimates,
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Count-Min Sketch lab for approximate stream frequencies.')
    parser.add_argument('--epsilon', type=float, default=0.02)
    parser.add_argument('--delta', type=float, default=0.01)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument(
        '--conservative-update',
        action='store_true',
        help='Use conservative updates to reduce overestimation under collisions.',
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    build_parser = subparsers.add_parser('build', help='Build a sketch from a text file of whitespace-separated tokens.')
    build_parser.add_argument('input', type=Path)
    build_parser.add_argument('--output', type=Path, required=True)

    estimate_parser = subparsers.add_parser('estimate', help='Estimate one or more token frequencies.')
    estimate_parser.add_argument('sketch', type=Path)
    estimate_parser.add_argument('items', nargs='+')

    hitters_parser = subparsers.add_parser('heavy-hitters', help='Report items whose estimated count passes a threshold.')
    hitters_parser.add_argument('sketch', type=Path)
    hitters_parser.add_argument('--threshold', type=int, required=True)

    merge_parser = subparsers.add_parser('merge', help='Merge two compatible sketches.')
    merge_parser.add_argument('left', type=Path)
    merge_parser.add_argument('right', type=Path)
    merge_parser.add_argument('--output', type=Path, required=True)

    benchmark_parser = subparsers.add_parser('benchmark-memory', help='Compare Count-Min Sketch memory with an exact Counter for a token stream.')
    benchmark_parser.add_argument('input', type=Path)
    benchmark_parser.add_argument('--sample-size', type=int, default=10, help='How many top exact items to include in the estimate sample.')

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == 'build':
        sketch = build_sketch(
            load_tokens_from_file(args.input),
            epsilon=args.epsilon,
            delta=args.delta,
            seed=args.seed,
            conservative_update=args.conservative_update,
        )
        save_sketch(args.output, sketch)
        print(
            json.dumps(
                {
                    'output': str(args.output),
                    'total_count': sketch.total_count,
                    'width': sketch.width,
                    'depth': sketch.depth,
                    'conservative_update': sketch.config.conservative_update,
                },
                indent=2,
            )
        )
        return 0

    if args.command == 'estimate':
        sketch = load_sketch(args.sketch)
        result = {
            'total_count': sketch.total_count,
            'error_bound': sketch.error_bound(),
            'conservative_update': sketch.config.conservative_update,
            'estimates': {item: sketch.estimate(item) for item in args.items},
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == 'heavy-hitters':
        sketch = load_sketch(args.sketch)
        print(
            json.dumps(
                {
                    'threshold': args.threshold,
                    'conservative_update': sketch.config.conservative_update,
                    'heavy_hitters': sketch.heavy_hitters(args.threshold),
                },
                indent=2,
            )
        )
        return 0

    if args.command == 'merge':
        left = load_sketch(args.left)
        right = load_sketch(args.right)
        left.merge(right)
        save_sketch(args.output, left)
        print(
            json.dumps(
                {
                    'output': str(args.output),
                    'total_count': left.total_count,
                    'conservative_update': left.config.conservative_update,
                },
                indent=2,
            )
        )
        return 0

    if args.command == 'benchmark-memory':
        payload = benchmark_memory(
            load_tokens_from_file(args.input),
            epsilon=args.epsilon,
            delta=args.delta,
            seed=args.seed,
            sample_size=args.sample_size,
            conservative_update=args.conservative_update,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    parser.error('Unknown command')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
