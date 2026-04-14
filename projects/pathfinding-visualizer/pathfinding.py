import argparse
import heapq
from collections import deque
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

Coordinate = Tuple[int, int]
PASSABLE_TILES = {'.', 'S', 'E', 'W'}
TILE_COSTS = {'.': 1, 'S': 1, 'E': 1, 'W': 3}


@dataclass(frozen=True)
class SearchResult:
    algorithm: str
    path: Optional[List[Coordinate]]
    visited_nodes: int
    path_cost: Optional[int]


class MapError(ValueError):
    pass


def parse_grid(lines: Sequence[str]) -> List[str]:
    grid = [line.rstrip('\n') for line in lines]
    while grid and grid[-1] == '':
        grid.pop()
    if not grid:
        raise MapError('map must not be empty')

    width = len(grid[0])
    if width == 0:
        raise MapError('map rows must not be empty')

    starts = ends = 0
    for row in grid:
        if len(row) != width:
            raise MapError('map must be rectangular')
        for ch in row:
            if ch == 'S':
                starts += 1
            elif ch == 'E':
                ends += 1
            elif ch not in PASSABLE_TILES and ch != '#':
                raise MapError(f'unsupported tile: {ch}')

    if starts != 1:
        raise MapError('map must contain exactly one start tile S')
    if ends != 1:
        raise MapError('map must contain exactly one end tile E')
    return grid


def find_points(grid: Sequence[str]) -> Tuple[Coordinate, Coordinate]:
    start = end = None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S':
                start = (r, c)
            elif ch == 'E':
                end = (r, c)
    return start, end


def neighbors(grid: Sequence[str], r: int, c: int) -> Iterable[Coordinate]:
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != '#':
            yield nr, nc


def movement_cost(grid: Sequence[str], coord: Coordinate) -> int:
    tile = grid[coord[0]][coord[1]]
    return TILE_COSTS.get(tile, 1)


def reconstruct_path(prev: dict, end: Coordinate) -> List[Coordinate]:
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def path_cost(grid: Sequence[str], path: Optional[Sequence[Coordinate]]) -> Optional[int]:
    if not path:
        return None
    return sum(movement_cost(grid, coord) for coord in path[1:])


def bfs_search(grid: Sequence[str]) -> SearchResult:
    start, end = find_points(grid)
    q = deque([start])
    prev = {start: None}
    visited_nodes = 0

    while q:
        cur = q.popleft()
        visited_nodes += 1
        if cur == end:
            path = reconstruct_path(prev, end)
            return SearchResult('bfs', path, visited_nodes, path_cost(grid, path))
        for nxt in neighbors(grid, *cur):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)

    return SearchResult('bfs', None, visited_nodes, None)


def heuristic(a: Coordinate, b: Coordinate) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_search(grid: Sequence[str]) -> SearchResult:
    start, end = find_points(grid)
    frontier = [(0, 0, start)]
    prev = {start: None}
    best_cost = {start: 0}
    visited_nodes = 0

    while frontier:
        _, current_cost, cur = heapq.heappop(frontier)
        if current_cost != best_cost.get(cur):
            continue
        visited_nodes += 1

        if cur == end:
            path = reconstruct_path(prev, end)
            return SearchResult('astar', path, visited_nodes, path_cost(grid, path))

        for nxt in neighbors(grid, *cur):
            next_cost = current_cost + movement_cost(grid, nxt)
            if next_cost < best_cost.get(nxt, float('inf')):
                best_cost[nxt] = next_cost
                prev[nxt] = cur
                priority = next_cost + heuristic(nxt, end)
                heapq.heappush(frontier, (priority, next_cost, nxt))

    return SearchResult('astar', None, visited_nodes, None)


def shortest_path(grid: Sequence[str], algorithm: str = 'bfs') -> SearchResult:
    if algorithm == 'bfs':
        return bfs_search(grid)
    if algorithm == 'astar':
        return a_star_search(grid)
    raise ValueError(f'unsupported algorithm: {algorithm}')


def render_path(grid: Sequence[str], path: Optional[Sequence[Coordinate]]) -> List[str]:
    rendered = [list(row) for row in grid]
    if path:
        for r, c in path[1:-1]:
            if rendered[r][c] not in {'S', 'E'}:
                rendered[r][c] = '*'
    return [''.join(row) for row in rendered]


def format_result(grid: Sequence[str], result: SearchResult) -> str:
    lines = [f'algorithm: {result.algorithm}', f'visited_nodes: {result.visited_nodes}']
    if result.path is None:
        lines.append('path_found: no')
        lines.append('path_cost: n/a')
    else:
        lines.append('path_found: yes')
        lines.append(f'path_length: {len(result.path) - 1}')
        lines.append(f'path_cost: {result.path_cost}')
    lines.append('')
    lines.extend(render_path(grid, result.path))
    return '\n'.join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='ASCII pathfinding visualizer')
    parser.add_argument('mapfile', help='text file containing S=start, E=end, #=wall, .=floor, W=weighted tile')
    parser.add_argument('--algorithm', choices=('bfs', 'astar'), default='bfs')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.mapfile, 'r', encoding='utf-8') as handle:
            grid = parse_grid(handle.read().splitlines())
        result = shortest_path(grid, algorithm=args.algorithm)
    except OSError as exc:
        parser.exit(2, f'file error: {exc}\n')
    except MapError as exc:
        parser.exit(2, f'map error: {exc}\n')

    print(format_result(grid, result))
    if result.path is None:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
