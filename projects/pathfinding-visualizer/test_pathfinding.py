import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from pathfinding import MapError, format_result, parse_grid, shortest_path


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

    def test_a_star_prefers_lower_cost_weighted_route(self):
        grid = parse_grid([
            'SWWE',
            '....',
        ])
        bfs_result = shortest_path(grid, algorithm='bfs')
        astar_result = shortest_path(grid, algorithm='astar')
        self.assertEqual(len(bfs_result.path) - 1, 3)
        self.assertEqual(bfs_result.path_cost, 7)
        self.assertEqual(astar_result.path_cost, 5)
        self.assertGreater(len(astar_result.path), len(bfs_result.path))

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


if __name__ == '__main__':
    unittest.main()
