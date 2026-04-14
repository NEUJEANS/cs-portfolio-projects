import unittest
from sudoku_solver import solve

class SudokuSolverTests(unittest.TestCase):
    def test_solver(self):
        board = [
            [5,3,0,0,7,0,0,0,0],
            [6,0,0,1,9,5,0,0,0],
            [0,9,8,0,0,0,0,6,0],
            [8,0,0,0,6,0,0,0,3],
            [4,0,0,8,0,3,0,0,1],
            [7,0,0,0,2,0,0,0,6],
            [0,6,0,0,0,0,2,8,0],
            [0,0,0,4,1,9,0,0,5],
            [0,0,0,0,8,0,0,7,9],
        ]
        self.assertTrue(solve(board))
        self.assertEqual(board[0], [5,3,4,6,7,8,9,1,2])

if __name__ == '__main__':
    unittest.main()
