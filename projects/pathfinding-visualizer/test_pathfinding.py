import unittest
from pathfinding import shortest_path, render_path

class PathfindingTests(unittest.TestCase):
    def test_shortest_path(self):
        grid = ['S..', '.#.', '..E']
        path = shortest_path(grid)
        self.assertEqual(path[0], (0,0))
        self.assertEqual(path[-1], (2,2))
        rendered = render_path(grid, path)
        self.assertIn('*', ''.join(rendered))

if __name__ == '__main__':
    unittest.main()
