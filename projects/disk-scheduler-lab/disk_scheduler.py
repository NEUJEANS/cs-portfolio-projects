from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class SimulationRequest:
    start: int
    requests: List[int]
    max_cylinder: int
    direction: str = 'up'

    def __post_init__(self) -> None:
        if self.max_cylinder < 1:
            raise ValueError('max_cylinder must be at least 1')
        if not 0 <= self.start <= self.max_cylinder:
            raise ValueError('start must be within disk bounds')
        if self.direction not in {'up', 'down'}:
            raise ValueError("direction must be 'up' or 'down'")
        for request in self.requests:
            if not 0 <= request <= self.max_cylinder:
                raise ValueError('all requests must be within disk bounds')


@dataclass(frozen=True)
class SimulationResult:
    algorithm: str
    start: int
    direction: str
    service_order: List[int]
    path: List[int]
    total_head_movement: int
    average_seek: float
    max_cylinder: int

    def to_dict(self) -> dict[str, object]:
        return {
            'algorithm': self.algorithm,
            'start': self.start,
            'direction': self.direction,
            'service_order': self.service_order,
            'path': self.path,
            'total_head_movement': self.total_head_movement,
            'average_seek': self.average_seek,
            'max_cylinder': self.max_cylinder,
        }


class DiskScheduler:
    def __init__(self, request: SimulationRequest) -> None:
        self.request = request

    def simulate(self, algorithm: str) -> SimulationResult:
        normalized = algorithm.lower()
        if normalized == 'fcfs':
            return self._fcfs()
        if normalized == 'sstf':
            return self._sstf()
        if normalized == 'scan':
            return self._scan(circular=False)
        if normalized == 'cscan':
            return self._scan(circular=True)
        raise ValueError(f'Unsupported algorithm: {algorithm}')

    def compare(self, algorithms: Iterable[str]) -> List[SimulationResult]:
        return [self.simulate(name) for name in algorithms]

    def _fcfs(self) -> SimulationResult:
        order = list(self.request.requests)
        path = [self.request.start, *order]
        return self._result('fcfs', order, path)

    def _sstf(self) -> SimulationResult:
        pending = list(self.request.requests)
        order: List[int] = []
        path = [self.request.start]
        position = self.request.start

        while pending:
            next_request = min(pending, key=lambda value: (abs(value - position), value))
            pending.remove(next_request)
            order.append(next_request)
            path.append(next_request)
            position = next_request

        return self._result('sstf', order, path)

    def _scan(self, circular: bool) -> SimulationResult:
        start = self.request.start
        lower = sorted(value for value in self.request.requests if value < start)
        higher = sorted(value for value in self.request.requests if value >= start)
        path = [start]

        if not self.request.requests:
            return self._result('cscan' if circular else 'scan', [], path)

        if self.request.direction == 'up':
            if circular:
                order = higher + lower
                if higher:
                    path.extend(higher)
                path.append(self.request.max_cylinder)
                if lower:
                    path.append(0)
                    path.extend(lower)
            else:
                order = higher + list(reversed(lower))
                if higher:
                    path.extend(higher)
                if lower:
                    path.append(self.request.max_cylinder)
                    path.extend(reversed(lower))
                elif higher:
                    path.append(self.request.max_cylinder)
                elif path[-1] != self.request.max_cylinder:
                    path.append(self.request.max_cylinder)
        else:
            if circular:
                order = list(reversed(lower)) + list(reversed(higher))
                if lower:
                    path.extend(reversed(lower))
                path.append(0)
                if higher:
                    path.append(self.request.max_cylinder)
                    path.extend(reversed(higher))
            else:
                order = list(reversed(lower)) + higher
                if lower:
                    path.extend(reversed(lower))
                if higher:
                    path.append(0)
                    path.extend(higher)
                elif lower:
                    path.append(0)
                elif path[-1] != 0:
                    path.append(0)

        deduped_path = [path[0]]
        for point in path[1:]:
            if point != deduped_path[-1]:
                deduped_path.append(point)

        return self._result('cscan' if circular else 'scan', order, deduped_path)

    def _result(self, algorithm: str, order: List[int], path: List[int]) -> SimulationResult:
        total = sum(abs(right - left) for left, right in zip(path, path[1:]))
        average = total / len(order) if order else 0.0
        return SimulationResult(
            algorithm=algorithm,
            start=self.request.start,
            direction=self.request.direction,
            service_order=order,
            path=path,
            total_head_movement=total,
            average_seek=round(average, 2),
            max_cylinder=self.request.max_cylinder,
        )


def load_request(path: Path) -> SimulationRequest:
    payload = json.loads(path.read_text(encoding='utf-8'))
    return SimulationRequest(
        start=int(payload['start']),
        requests=[int(value) for value in payload['requests']],
        max_cylinder=int(payload.get('max_cylinder', 199)),
        direction=str(payload.get('direction', 'up')),
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Simulate classic disk scheduling algorithms.')
    parser.add_argument('--input', type=Path, help='Path to JSON request payload.')
    parser.add_argument('--start', type=int, default=50)
    parser.add_argument('--max-cylinder', type=int, default=199)
    parser.add_argument('--direction', choices=['up', 'down'], default='up')
    parser.add_argument('--requests', nargs='*', type=int, default=[])

    subparsers = parser.add_subparsers(dest='command', required=True)

    simulate_parser = subparsers.add_parser('simulate', help='Run one scheduling algorithm.')
    simulate_parser.add_argument('--algorithm', choices=['fcfs', 'sstf', 'scan', 'cscan'], required=True)

    compare_parser = subparsers.add_parser('compare', help='Compare multiple scheduling algorithms.')
    compare_parser.add_argument('--algorithms', nargs='+', choices=['fcfs', 'sstf', 'scan', 'cscan'], required=True)

    return parser


def build_request(args: argparse.Namespace) -> SimulationRequest:
    if args.input:
        return load_request(args.input)
    return SimulationRequest(
        start=args.start,
        requests=list(args.requests),
        max_cylinder=args.max_cylinder,
        direction=args.direction,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    request = build_request(args)
    scheduler = DiskScheduler(request)

    if args.command == 'simulate':
        print(json.dumps(scheduler.simulate(args.algorithm).to_dict(), indent=2))
        return 0

    if args.command == 'compare':
        results = [result.to_dict() for result in scheduler.compare(args.algorithms)]
        print(json.dumps({'results': results}, indent=2))
        return 0

    parser.error('Unknown command')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
