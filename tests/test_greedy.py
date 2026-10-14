import pytest

from cutopt.errors import CutOptError, NoStockForSectionError, PieceTooLongError
from cutopt.greedy import greedycut
from cutopt.models import Piece, Problem, StockLength

SECTION1 = "47x100 C24"
SECTION2 = "47x150 C24"


# Helper function that checks there are no overflow and no losses or duplicates that return
def assert_valid(result, problem):
    for i, board in enumerate(result):
        # Check if all cut sections are the same as board section
        cut_sections = {p.section for p in board.cuts}
        assert cut_sections == {board.section}, (
            f"cut is from {cut_sections} while board is {board.section}"
        )

        used = sum(p.length for p in board.cuts) + (len(board.cuts) - 1) * board.kerf
        assert used <= board.stock_length, (
            f"board {i + 1} overflows: used {used} > {board.stock_length}"
        )

    lengths = []
    for p in problem.pieces:
        for _ in range(p.quantity):
            lengths.append(p.length)

    result_lengths = []
    for board in result:
        for piece in board.cuts:
            result_lengths.append(piece.length)

    assert sorted(lengths) == sorted(result_lengths), (
        f"Expected {sorted(lengths)}, got {sorted(result_lengths)}"
    )


def make_problem(pieces, stocks, kerf=0, section=SECTION1):
    """Build a single-section Problem from plain numbers.

    pieces is a list of (length, quantity) pairs, stocks a list of lengths.
    """
    return Problem(
        stock=tuple(StockLength(section, length) for length in stocks),
        kerf=kerf,
        pieces=tuple(Piece(section, "piece", length, qty) for length, qty in pieces),
    )


def solve(problem):
    """Run greedycut and check the result is valid before returning it."""
    result = greedycut(problem)
    assert_valid(result, problem)
    return result


def test_single_piece_single_board_no_kerf():
    result = solve(make_problem(pieces=[(2000, 1)], stocks=[2400]))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2000


def test_two_1200s_no_kerf_fits_single_2400():
    result = solve(make_problem(pieces=[(1200, 2)], stocks=[2400]))
    assert len(result) == 1
    assert [p.length for p in result[0].cuts] == [1200, 1200]


def test_kerf_prevents_two_1200s_on_2400():
    result = solve(make_problem(pieces=[(1200, 2)], stocks=[2400], kerf=3))
    assert len(result) == 2


def test_one_2400_fits_one_2400_with_kerf():
    result = solve(make_problem(pieces=[(2400, 1)], stocks=[2400], kerf=3))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2400


def test_exact_fit_with_kerf():
    result = solve(make_problem(pieces=[(1200, 1), (1197, 1)], stocks=[2400], kerf=3))
    assert len(result) == 1


def test_first_fit_reuses_earlier_board():
    pieces = (
        Piece(SECTION1, "rafter", 2000, 1),
        Piece(SECTION1, "nogging", 800, 1),
        Piece(SECTION1, "stud", 1500, 1),
        Piece(SECTION1, "stud", 400, 1),
    )
    stock = StockLength(SECTION1, 2400)
    problem = Problem((stock,), 0, pieces)
    result = greedycut(problem)
    assert_valid(result, problem)
    assert len(result) == 2
    assert result[0].cuts[0].length == 2000
    assert result[0].cuts[1].length == 400
    assert result[1].cuts[0].length == 1500
    assert result[1].cuts[1].length == 800


def test_piece_longer_than_stock():
    pieces = (
        Piece(SECTION1, "rafter", 2600, 1),
        Piece(SECTION1, "nogging", 801, 1),
    )
    stock = StockLength(SECTION1, 800)
    with pytest.raises(PieceTooLongError, match="is longer than stock"):
        greedycut(Problem((stock,), 0, pieces))


def test_no_pieces_returns_empty_list():
    assert solve(make_problem(pieces=[], stocks=[2400])) == []


def test_no_stock_raises():
    piece = Piece(SECTION1, "stud", 1475, 1)
    with pytest.raises(CutOptError, match="There is no stock to choose boards from"):
        greedycut(Problem((), 0, (piece,)))


def test_no_piece_and_no_stock_raises():
    with pytest.raises(CutOptError, match="There is no stock to choose boards from"):
        greedycut(Problem((), 0, ()))


def test_different_sections_never_share_a_board():
    pieces = (
        Piece(SECTION1, "stud", 1000, 1),
        Piece(SECTION2, "stud", 1000, 1),
    )
    stock = (
        StockLength(SECTION1, 4800),
        StockLength(SECTION2, 2400),
    )
    problem = Problem(stock, 0, pieces)
    result = greedycut(problem)
    assert_valid(result, problem)
    assert len(result) == 2


def test_section_without_stock_raises():
    piece = Piece(SECTION1, "stud", 2400, 1)
    stock = StockLength(SECTION2, 2400)
    with pytest.raises(NoStockForSectionError, match="No stock for section"):
        greedycut(Problem((stock,), 0, (piece,)))


def test_too_long_check_if_uses_own_section():
    piece = Piece(SECTION1, "rafter", 3000, 1)
    stocks = (
        StockLength(SECTION1, 2400),
        StockLength(SECTION2, 4800),
    )
    problem = Problem(stocks, 0, (piece,))
    with pytest.raises(PieceTooLongError, match="longer than stock"):
        greedycut(problem)

def test_shrinks():
    result = solve(make_problem(pieces=[(1950, 1)], stocks=[2400, 4800], kerf=3))
    assert result[0].stock_length == 2400

def test_picks_the_middle():
    result = solve(make_problem(pieces = [(1700, 2)], stocks=[2400, 3600, 4800], kerf=3))
    assert result[0].stock_length == 3600

def test_keeps_a_full_board():
    result = solve(make_problem(pieces = [(4700, 1)], stocks=[2400, 4800]))
    assert result[0].stock_length == 4800
