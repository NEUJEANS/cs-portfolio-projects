import argparse
import sys
from pathlib import Path

DIGITS = set(range(1, 10))


class BoardError(ValueError):
    """Raised when a Sudoku board is malformed or contradictory."""


def normalize_board_text(text):
    invalid = sorted({ch for ch in text if not (ch.isdigit() or ch == '.' or ch.isspace())})
    if invalid:
        joined = ', '.join(repr(ch) for ch in invalid)
        raise BoardError(f'board contains invalid characters: {joined}')
    return ''.join(ch for ch in text if ch.isdigit() or ch == '.')


def parse_board(text):
    raw = normalize_board_text(text.strip())
    if len(raw) != 81:
        raise BoardError('board must contain exactly 81 cells using digits or . for blanks')

    numbers = []
    for ch in raw:
        if ch == '.':
            numbers.append(0)
        elif ch.isdigit():
            value = int(ch)
            if value < 0 or value > 9:
                raise BoardError('board values must be digits between 0 and 9')
            numbers.append(value)
        else:
            raise BoardError(f'invalid character in board: {ch!r}')

    board = [numbers[index:index + 9] for index in range(0, 81, 9)]
    validate_board(board)
    return board


def load_board_from_file(path):
    return parse_board(Path(path).read_text(encoding='utf-8'))


def duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value == 0:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_board(board):
    if len(board) != 9 or any(len(row) != 9 for row in board):
        raise BoardError('board must be a 9x9 grid')

    for row_index, row in enumerate(board):
        invalid = [value for value in row if value not in range(10)]
        if invalid:
            raise BoardError(f'row {row_index + 1} contains out-of-range values: {invalid}')
        duplicates = sorted(duplicate_values(row))
        if duplicates:
            raise BoardError(f'row {row_index + 1} contains duplicate values: {duplicates}')

    for col_index in range(9):
        column = [board[row_index][col_index] for row_index in range(9)]
        duplicates = sorted(duplicate_values(column))
        if duplicates:
            raise BoardError(f'column {col_index + 1} contains duplicate values: {duplicates}')

    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            box = [
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            ]
            duplicates = sorted(duplicate_values(box))
            if duplicates:
                raise BoardError(
                    f'box ({box_row // 3 + 1}, {box_col // 3 + 1}) contains duplicate values: {duplicates}'
                )


def find_empty(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                return row, col
    return None


def valid(board, row, col, value):
    if value in board[row]:
        return False
    if any(board[r][col] == value for r in range(9)):
        return False
    box_row, box_col = (row // 3) * 3, (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == value:
                return False
    return True


def candidate_values(board, row, col):
    if board[row][col] != 0:
        return []
    used = set(board[row])
    used.update(board[r][col] for r in range(9))
    box_row, box_col = (row // 3) * 3, (col // 3) * 3
    used.update(board[r][c] for r in range(box_row, box_row + 3) for c in range(box_col, box_col + 3))
    return sorted(DIGITS - used)


def find_best_empty(board):
    best = None
    best_candidates = None
    for row in range(9):
        for col in range(9):
            if board[row][col] != 0:
                continue
            candidates = candidate_values(board, row, col)
            if best is None or len(candidates) < len(best_candidates):
                best = (row, col)
                best_candidates = candidates
                if len(best_candidates) == 1:
                    return best, best_candidates
    return best, best_candidates


def solve(board):
    position, candidates = find_best_empty(board)
    if position is None:
        return True

    row, col = position
    if not candidates:
        return False

    for value in candidates:
        if valid(board, row, col, value):
            board[row][col] = value
            if solve(board):
                return True
            board[row][col] = 0
    return False


def format_board(board, compact=False):
    if compact:
        return ''.join(str(value) for row in board for value in row)

    lines = []
    for row_index, row in enumerate(board):
        chunks = [' '.join(str(value) for value in row[start:start + 3]) for start in (0, 3, 6)]
        lines.append(' | '.join(chunks))
        if row_index in {2, 5}:
            lines.append('-' * 21)
    return '\n'.join(lines)


def build_parser():
    parser = argparse.ArgumentParser(description='Sudoku solver')
    parser.add_argument('board', nargs='?', help='81 cells using digits or . for blanks')
    parser.add_argument('--file', help='read board text from a file')
    parser.add_argument('--compact', action='store_true', help='print solved board as a single 81-char string')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if bool(args.board) == bool(args.file):
        parser.error('provide exactly one input source: positional board or --file')

    try:
        board = load_board_from_file(args.file) if args.file else parse_board(args.board)
    except OSError as exc:
        print(f'file error: {exc}', file=sys.stderr)
        return 2
    except BoardError as exc:
        print(f'board error: {exc}', file=sys.stderr)
        return 2

    if not solve(board):
        print('no solution found', file=sys.stderr)
        return 1

    print(format_board(board, compact=args.compact))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
