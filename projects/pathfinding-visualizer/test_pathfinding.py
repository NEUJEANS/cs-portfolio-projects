import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from pathfinding import MapError, compare_algorithms, format_comparison, format_result, parse_grid, shortest_path


class PathfindingTests(unittest.TestCase):
    def test_parse_grid_rejects_non_rectangular_map(self):
        with self.assertRaises(MapError):
            parse_grid(['S..', '..', '..E'])

    def test_parse_grid_rejects_blank_internal_row(self):
        with self.assertRaises(MapError):
            parse_grid(['S..', '', '..E'])

    def test_bfs_finds_shortest_unweighted_path(self):
        grid = parse_grid([
            'S..',
            '.#.',
            '..E',
        ])
        result = shortest_path(grid, algorithm='bfs')
        self.assertIsNotNone(result.path)
        self.assertEqual(result.path[0], (0, 0))
        self.assertEqual(result.path[-1], (2, 2))
        self.assertEqual(result.path_cost, 4)

    def test_dijkstra_matches_astar_weighted_optimal_cost(self):
        grid = parse_grid([
            'S...',
            '....',
            '....',
            '.W.E',
        ])
        dijkstra_result = shortest_path(grid, algorithm='dijkstra')
        astar_result = shortest_path(grid, algorithm='astar')
        self.assertEqual(dijkstra_result.path_cost, 6)
        self.assertEqual(astar_result.path_cost, 6)
        self.assertEqual(dijkstra_result.path[-1], astar_result.path[-1])
        self.assertLess(astar_result.visited_nodes, dijkstra_result.visited_nodes)

    def test_bfs_can_choose_higher_cost_route_on_weighted_map(self):
        grid = parse_grid([
            'SWWE',
            '....',
        ])
        bfs_result = shortest_path(grid, algorithm='bfs')
        self.assertEqual(len(bfs_result.path) - 1, 3)
        self.assertEqual(bfs_result.path_cost, 7)

    def test_compare_algorithms_highlights_optimal_cost_match(self):
        grid = parse_grid([
            'SWWE',
            '....',
        ])
        results = compare_algorithms(grid)
        rendered = format_comparison(grid, results)
        self.assertIn('comparison: bfs vs dijkstra vs astar', rendered)
        self.assertIn('algorithm: bfs', rendered)
        self.assertIn('optimal_cost_match: no', rendered)
        self.assertEqual(results[1].path_cost, 5)
        self.assertEqual(results[2].path_cost, 5)

    def test_no_path_is_reported_cleanly(self):
        grid = parse_grid([
            'S#E',
            '###',
            '...',
        ])
        result = shortest_path(grid, algorithm='bfs')
        self.assertIsNone(result.path)
        rendered = format_result(grid, result)
        self.assertIn('path_found: no', rendered)
        self.assertIn('path_cost: n/a', rendered)

    def test_cli_outputs_summary_and_rendered_map(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
            handle.write(textwrap.dedent('''\
                S.WE
                ....
            '''))
            map_path = handle.name

        completed = subprocess.run(
            [sys.executable, str(project_dir / 'pathfinding.py'), map_path, '--algorithm', 'astar'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('algorithm: astar', completed.stdout)
        self.assertIn('path_found: yes', completed.stdout)
        self.assertIn('*', completed.stdout)

    def test_cli_accepts_dijkstra_algorithm(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
            handle.write('SWWE\n....\n')
            map_path = handle.name

        completed = subprocess.run(
            [sys.executable, str(project_dir / 'pathfinding.py'), map_path, '--algorithm', 'dijkstra'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('algorithm: dijkstra', completed.stdout)
        self.assertIn('path_cost: 5', completed.stdout)

    def test_cli_compare_prints_all_algorithms(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
            handle.write('SWWE\n....\n')
            map_path = handle.name

        completed = subprocess.run(
            [sys.executable, str(project_dir / 'pathfinding.py'), map_path, '--compare'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('comparison: bfs vs dijkstra vs astar', completed.stdout)
        self.assertEqual(completed.stdout.count('algorithm: '), 3)
        self.assertIn('optimal_cost_match: no', completed.stdout)

    def test_cli_compare_returns_non_zero_when_all_algorithms_fail(self):
        project_dir = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
            handle.write('S#E\n###\n...\n')
            map_path = handle.name

        completed = subprocess.run(
            [sys.executable, str(project_dir / 'pathfinding.py'), map_path, '--compare'],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout.count('path_found: no'), 3)


if __name__ == '__main__':
    unittest.main()
