from .models import Piece, StockLength, Problem, CutPattern


# First-fit algorithm


def greedycut(problem):
    # Sort the lists longest to shortest
    pieces = sorted(problem.pieces, key=lambda item: item.length, reverse=True)
    stocks = sorted(problem.stock, key=lambda item: item.length, reverse=True)

    # Expand the quantitys to single items
    exp_pieces = []
    for piece in pieces:
        for _ in range(piece.quantity):
            exp_pieces.append(Piece(section=piece.section, label=piece.label, length=piece.length))

    # Create a list of boards and check if the piece fits, if not create a new one
    boards = []
    for piece in exp_pieces:
        placed = False
        for board in boards:
            used = sum(p.length for p in board.cuts) + (len(board.cuts) - 1) * board.kerf
            if used + board.kerf + piece.length <= board.stock_length:
                board.cuts.append(piece)
                placed = True
                break

        if not placed:
            new_board = CutPattern(stock_length=stocks[0].length, kerf=problem.kerf)
            new_board.cuts.append(piece)
            boards.append(new_board)

    return boards
