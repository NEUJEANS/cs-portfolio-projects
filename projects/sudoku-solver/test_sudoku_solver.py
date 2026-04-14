import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sudoku_solver import BoardError, candidate_values, format_board, parse_board, solve


class SudokuSolverTests(unittest.TestCase):
    def test_solver_solves_known_board(self):
        board = parse_board('530070000600195000098000060800060003400803001700020006060000280000419005000080079')
        self.assertTrue(solve(board))
        self.assertEqual(board[0], [5, 3, 4, 6, 7, 8, 9, 1, 2])
        self.assertEqual(board[8], [3, 4, 5, 2, 8, 6, 1, 7, 9])

    def test_parse_board_accepts_dots_and_newlines(self):
        board = parse_board(
            '53..7....\n'
            '6..195...\n'
            '.98....6.\n'
            '8...6...3\n'
            '4..8.3..1\n'
            '7...2...6\n'
            '.6....28.\n'
            '...419..5\n'
            '....8..79\n'
        )
        self.assertEqual(board[0][:5], [5, 3, 0, 0, 7])

    def test_parse_board_rejects_duplicate_conflicts(self):
        with self.assertRaises(BoardError):
            parse_board('553070000600195000098000060800060003400803001700020006060000280000419005000080079')

    def test_parse_board_rejects_invalid_characters(self):
        with self.assertRaises(BoardError):
            parse_board('53a070000600195000098000060800060003400803001700020006060000280000419005000080079')

    def test_candidate_values_for_constrained_cell(self):
        board = parse_board('530070000600195000098000060800060003400803001700020006060000280000419005000080079')
        self.assertEqual(candidate_values(board, 0, 2), [1, 2, 4])

    def test_format_board_compact(self):
        board = parse_board('534678912672195348198342567859761423426853791713924856961537284287419635345286179')
        self.assertEqual(format_board(board, compact=True), '534678912672195348198342567859761423426853791713924856961537284287419635345286179')

    def test_cli_requires_exactly_one_input_source(self):
        script = Path(__file__).with_name('sudoku_solver.py')
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('provide exactly one input source', result.stderr)

    def test_cli_supports_file_input_and_compact_output(self):
        script = Path(__file__).with_name('sudoku_solver.py')
        with tempfile.TemporaryDirectory() as tmp:
            board_path = Path(tmp) / 'board.txt'
            board_path.write_text('530070000600195000098000060800060003400803001700020006060000280000419005000080079')
            result = subprocess.run(
                [sys.executable, str(script), '--file', str(board_path), '--compact'],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '534678912672195348198342567859761423426853791713924856961537284287419635345286179')

    def test_cli_returns_code_2_for_missing_file(self):
        script = Path(__file__).with_name('sudoku_solver.py')
        result = subprocess.run(
            [sys.executable, str(script), '--file', 'missing-puzzle.txt'],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('file error:', result.stderr)

    def test_cli_returns_code_2_for_invalid_board(self):
        script = Path(__file__).with_name('sudoku_solver.py')
        result = subprocess.run(
            [sys.executable, str(script), '553070000600195000098000060800060003400803001700020006060000280000419005000080079'],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('board error:', result.stderr)


if __name__ == '__main__':
    unittest.main()
