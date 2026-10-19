import pytest

from cutopt.errors import CutOptError
from cutopt.models import Piece, Problem, StockLength


def test_zero_length_piece():
    with pytest.raises(CutOptError, match="must be bigger than 0, got 0"):
        Piece(section="47x100 C24", label="stud", length=0, quantity=1)


def test_negative_quantity_piece():
    with pytest.raises(CutOptError, match="must be bigger than 0, got -1"):
        Piece(section="47x100 C24", label="stud", length=2000, quantity=-1)


def test_zero_length_stock():
    with pytest.raises(CutOptError, match="must be bigger than 0, got 0"):
        StockLength(section="47x100 C24", length=0, quantity=1)


def test_negative_kerf_problem():
    with pytest.raises(CutOptError, match="kerf must be 0 or more, got -1"):
        Problem(
            stock=(StockLength(section="47x100 C24", length=2000, quantity=1),),
            kerf=-1,
            pieces=(Piece(section="47x100 C24", label="stud", length=1950, quantity=1),),
        )


def test_negative_or_zero_stock_length():
    with pytest.raises(CutOptError, match="stock quantity: must be bigger than 0, got -1"):
        StockLength(section="47x150 C24", length=1550, quantity=-1)
    with pytest.raises(CutOptError, match="stock quantity: must be bigger than 0, got 0"):
        StockLength(section="47x150 C24", length=1550, quantity=0)


def test_unlimited_stock_quantity_is_valid():
    stock = StockLength(section="47x100 C24", length=2400)
    assert stock.quantity is None
