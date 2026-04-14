import argparse


def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def valid(board, row, col, value):
    if value in board[row]:
        return False
    if any(board[r][col] == value for r in range(9)):
        return False
    br, bc = row // 3 * 3, col // 3 * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == value:
                return False
    return True


def solve(board):
    pos = find_empty(board)
    if pos is None:
        return True
    r, c = pos
    for value in range(1, 10):
        if valid(board, r, c, value):
            board[r][c] = value
            if solve(board):
                return True
            board[r][c] = 0
    return False


def main(argv=None):
    p = argparse.ArgumentParser(description='Sudoku solver')
    p.add_argument('board', help='81 chars, use 0 for empty')
    args = p.parse_args(argv)
    nums = [int(ch) for ch in args.board.strip()]
    board = [nums[i:i+9] for i in range(0, 81, 9)]
    solve(board)
    for row in board:
        print(' '.join(map(str, row)))

if __name__ == '__main__':
    main()
