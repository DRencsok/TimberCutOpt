import pytest

from cutopt.metrics import Metrics
from cutopt.models import CutPattern, Piece

SECTION = "47x100 C24"


def make_board(stock_length, lengths, section=SECTION, kerf=0):
    """Build a board with one piece per length, e.g. make_board(2400, [1000, 1000])."""
    return CutPattern(
        stock_length=stock_length,
        kerf=kerf,
        section=section,
        cuts=[Piece(section, "piece", length) for length in lengths],
    )


def test_return_values():
    result = Metrics.from_boards([make_board(2400, [2000]), make_board(2400, [1000, 1000])])
    assert result.board_count == 2
    assert result.stock_length_total == 4800
    assert result.piece_length_total == 4000
    assert result.waste == 800
    assert result.waste_percent == pytest.approx(16.67, abs=0.01)
    assert result.shopping_list == {(SECTION, 2400): 2}


def test_empty_list():
    result = Metrics.from_boards([])
    assert result.board_count == 0
    assert result.waste_percent == 0.0
