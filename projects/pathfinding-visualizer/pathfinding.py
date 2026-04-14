import argparse
from collections import deque


def neighbors(grid, r, c):
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nr, nc = r+dr, c+dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != '#':
            yield nr, nc


def shortest_path(grid):
    start = end = None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S': start = (r,c)
            if ch == 'E': end = (r,c)
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == end:
            break
        for nxt in neighbors(grid, *cur):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    if end not in prev:
        return None
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def render_path(grid, path):
    g = [list(row) for row in grid]
    for r, c in path[1:-1]:
        g[r][c] = '*'
    return [''.join(row) for row in g]


def main(argv=None):
    p = argparse.ArgumentParser(description='ASCII pathfinding visualizer')
    p.add_argument('mapfile')
    args = p.parse_args(argv)
    grid = open(args.mapfile).read().splitlines()
    path = shortest_path(grid)
    for row in render_path(grid, path):
        print(row)

if __name__ == '__main__':
    main()
