import pytest

from cutopt.errors import CutOptError
from cutopt.models import CutPattern, Piece, Problem, StockLength

SECTION = "47x100 C24"


def make_board(stock_length, lengths, kerf=3):
    return CutPattern(
        stock_length=stock_length,
        kerf=kerf,
        section=SECTION,
        cuts=[Piece(SECTION, "piece", length) for length in lengths],
    )


def test_zero_length_piece():
    with pytest.raises(CutOptError, match="must be bigger than 0, got 0"):
        Piece(section=SECTION, label="stud", length=0, quantity=1)


def test_negative_quantity_piece():
    with pytest.raises(CutOptError, match="must be bigger than 0, got -1"):
        Piece(section=SECTION, label="stud", length=2000, quantity=-1)


def test_zero_length_stock():
    with pytest.raises(CutOptError, match="must be bigger than 0, got 0"):
        StockLength(section=SECTION, length=0, quantity=1)


def test_negative_kerf_problem():
    with pytest.raises(CutOptError, match="kerf must be 0 or more, got -1"):
        Problem(
            stock=(StockLength(section=SECTION, length=2000, quantity=1),),
            kerf=-1,
            pieces=(Piece(section=SECTION, label="stud", length=1950, quantity=1),),
        )


def test_negative_or_zero_stock_length():
    with pytest.raises(CutOptError, match="stock quantity: must be bigger than 0, got -1"):
        StockLength(section=SECTION, length=1550, quantity=-1)
    with pytest.raises(CutOptError, match="stock quantity: must be bigger than 0, got 0"):
        StockLength(section=SECTION, length=1550, quantity=0)


def test_unlimited_stock_quantity_is_valid():
    stock = StockLength(section=SECTION, length=2400)
    assert stock.quantity is None


def test_offcut_loses_one_kerf_to_the_last_cut():
    assert make_board(4800, [2150, 2150]).offcut == 494


def test_exact_fit_leaves_no_offcut():
    assert make_board(2400, [2400]).offcut == 0


def test_leftover_narrower_than_kerf_turns_to_dust():
    assert make_board(2400, [2398]).offcut == 0


def test_empty_board_is_all_offcut():
    assert make_board(2400, []).offcut == 2400
