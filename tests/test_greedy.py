from cutopt.greedy import greedycut
from cutopt.models import Piece, StockLength, Problem

def test_single_piece_single_board_no_kerf():
    piece = Piece("47x100 C24", "stud", 2000, 1)
    stock= StockLength("47x100 C24", 2400)
    result = greedycut(Problem((stock,), 0, (piece,)))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2000



def test_two_1200s_no_kerf_fits_single_2400():
    piece = Piece("47x100 C24", "stud", 1200, 2)
    stock= StockLength("47x100 C24", 2400)
    result = greedycut(Problem((stock,), 0, (piece,)))
    assert len(result[0].cuts) == 2
    assert result[0].cuts[0].length == 1200
    assert len(result) == 1

def test_kerf_prevents_two_1200s_on_2400():
    piece = Piece("47x100 C24", "stud", 1200, 2)
    stock= StockLength("47x100 C24", 2400)
    result = greedycut(Problem((stock,), 3, (piece,)))
    assert len(result) == 2

def test_one_2400_fits_one_2400_with_kerf():
    piece = Piece("47x100 C24", "stud", 2400, 1)
    stock= StockLength("47x100 C24", 2400)
    result = greedycut(Problem((stock,), 3, (piece,)))
    assert len(result) == 1
    assert result[0].cuts[0].length == 2400

def test_exact_fit_with_kerf():
    pieces =( Piece("47x100 C24", "stud", 1200, 1),
              Piece("47x100 C24", "stud", 1197, 1),
    )
    stock= StockLength("47x100 C24", 2400)
    result = greedycut(Problem((stock,), 3, pieces))
    assert len(result) == 1