from helpers import SECTION1, assert_valid

from cutopt.greedy import greedycut
from cutopt.models import Piece, Problem, StockLength


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
