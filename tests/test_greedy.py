from cutopt.greedy import greedycut
from cutopt.models import Piece, StockLength, Problem

def test_single_piece_single_board():
    piece = Piece("47x100 C24", "stud", 2000, 1)
    stock = StockLength("47x100 C24", 2400)
    result = greedycut(Problem([stock], 0, [piece]))
    assert len(result) == 1 

    