"""First-Fit Decreasing solver for the 1D cutting stock problem."""

from collections import defaultdict

from .errors import CutOptError, NoStockForSectionError, PieceTooLongError
from .models import CutPattern, Piece, Problem


def _pack(pieces, stocks, kerf):
    """Pack one section's pieces onto boards using first fit.

    Args:
        pieces: Pieces of a single section, expanded to quantity 1 and
            sorted longest first.
        stocks: Stock lengths of the same section, sorted longest first.
            Every new board uses stocks[0], the longest one.
        kerf: Saw blade width in mm, lost on every cut between two pieces.

    Returns:
        The boards in the order they were opened, each holding its cuts.
    """
    # Create a list of boards and check if the piece fits, if not create a new one
    boards = []
    for piece in pieces:
        placed = False
        for board in boards:
            # n pieces need n - 1 kerfs between them
            used = sum(p.length for p in board.cuts) + (len(board.cuts) - 1) * board.kerf
            if used + board.kerf + piece.length <= board.stock_length:
                board.cuts.append(piece)
                placed = True
                break

        if not placed:
            new_board = CutPattern(
                stock_length=stocks[0].length, kerf=kerf, section=stocks[0].section
            )
            new_board.cuts.append(piece)
            boards.append(new_board)

    return boards


def _shrink(boards, stocks):
    for board in boards:
        used = sum(p.length for p in board.cuts) + (len(board.cuts) - 1) * board.kerf
        for s in reversed(stocks):
            if s.length >= used:
                board.stock_length = s.length
                break
    return boards


def greedycut(problem: Problem) -> list[CutPattern]:
    """Solve a cutting problem with First-Fit Decreasing.

    Each section is solved separately, since sections can never share a board.
    Within a section, pieces are placed longest first onto the first open
    board they fit on, and a new board of the longest stock length is opened
    when none fits.

    Args:
        problem: The pieces to cut, the available stock lengths and the kerf.

    Returns:
        The boards for all sections in one list. An empty list if there
        are no pieces.

    Raises:
        CutOptError: If no stock lengths are given at all.
        NoStockForSectionError: If a piece's section has no stock length.
        PieceTooLongError: If a piece is longer than the longest stock
            length of its section.
    """
    pieces = sorted(problem.pieces, key=lambda item: item.length, reverse=True)
    stocks = sorted(problem.stock, key=lambda item: item.length, reverse=True)
    if not stocks:
        raise CutOptError("There is no stock to choose boards from")

    # Group pieces by section
    pieces_by_section = defaultdict(list)
    for piece in pieces:
        pieces_by_section[piece.section].append(piece)

    # Group stock by section
    stocks_by_section = defaultdict(list)
    for stock in stocks:
        stocks_by_section[stock.section].append(stock)

    all_boards = []
    # Sections can never share a board so each one is packed seperately
    for section, section_pieces in pieces_by_section.items():
        if section not in stocks_by_section:
            raise NoStockForSectionError(f"No stock for section {section}")
        section_stocks = stocks_by_section[section]

        # Expand pieces from quantity into single items
        exp_pieces = []
        for piece in section_pieces:
            if piece.length > section_stocks[0].length:
                raise PieceTooLongError(
                    f"Piece {piece.label} ({piece.length}) is longer than stock"
                    f" {section_stocks[0].length}"
                )
            for _ in range(piece.quantity):
                exp_pieces.append(
                    Piece(section=piece.section, label=piece.label, length=piece.length)
                )

        all_boards.extend(_shrink(_pack(exp_pieces, section_stocks, problem.kerf), section_stocks))

    return all_boards
