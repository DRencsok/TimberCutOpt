import pytest

from cutopt.greedy import greedycut
from cutopt.models import Piece, StockLength, Problem


SECTION1 = "47x100 C24"
SECTION2 = "47x150 C24"


def test_single_piece_single_board_no_kerf():
    piece = Piece(SECTION1, "stud", 2000, 1)
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 0, (piece,)))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2000


def test_two_1200s_no_kerf_fits_single_2400():
    piece = Piece(SECTION1, "stud", 1200, 2)
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 0, (piece,)))
    assert len(result[0].cuts) == 2
    assert result[0].cuts[0].length == 1200
    assert len(result) == 1


def test_kerf_prevents_two_1200s_on_2400():
    piece = Piece(SECTION1, "stud", 1200, 2)
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 3, (piece,)))
    assert len(result) == 2


def test_one_2400_fits_one_2400_with_kerf():
    piece = Piece(SECTION1, "stud", 2400, 1)
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 3, (piece,)))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2400


def test_exact_fit_with_kerf():
    pieces = (
        Piece(SECTION1, "stud", 1200, 1),
        Piece(SECTION1, "stud", 1197, 1),
    )
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 3, pieces))
    assert len(result) == 1


def test_first_fit_reuses_earlier_board():
    pieces = (
        Piece(SECTION1, "rafter", 2000, 1),
        Piece(SECTION1, "nogging", 800, 1),
        Piece(SECTION1, "stud", 1500, 1),
        Piece(SECTION1, "stud", 400, 1),
    )
    stock = StockLength(SECTION1, 2400)
    result = greedycut(Problem((stock,), 0, pieces))
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
    with pytest.raises(ValueError, match="is longer than stock"):
        greedycut(Problem((stock,), 0, pieces))


def test_no_pieces_returns_empty_list():
    stock = StockLength(SECTION1, 2400)
    assert greedycut(Problem((stock,), 0, ())) == []


def test_no_stock_raises():
    piece = Piece(SECTION1, "stud", 1475, 1)
    with pytest.raises(ValueError, match="There is no stock to choose boards from"):
        greedycut(Problem((), 0, (piece,)))


def test_no_piece_and_no_stock_raises():
    with pytest.raises(ValueError, match="There is no stock to choose boards from"):
        greedycut(Problem((), 0, ()))
