import pytest
from helpers import SECTION1, SECTION2, assert_valid, make_problem

from cutopt.cp_sat import cp_sat
from cutopt.errors import CutOptError, NoStockForSectionError, PieceTooLongError, UnknownSolverError
from cutopt.get_solver import SOLVERS as VALID_SOLVERS
from cutopt.get_solver import get_solver
from cutopt.greedy import greedycut
from cutopt.models import Piece, Problem, StockLength

# Solvers the shared tests below run against
SOLVERS = [greedycut, cp_sat]


@pytest.mark.parametrize("solver", SOLVERS)
def test_single_piece_single_board_no_kerf(solver):
    problem = make_problem(pieces=[(2000, 1)], stocks=[2400])
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 1
    assert result[0].cuts[0].length == 2000


@pytest.mark.parametrize("solver", SOLVERS)
def test_two_1200s_no_kerf_fits_single_2400(solver):
    problem = make_problem(pieces=[(1200, 2)], stocks=[2400])
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 1
    assert [p.length for p in result[0].cuts] == [1200, 1200]


@pytest.mark.parametrize("solver", SOLVERS)
def test_kerf_prevents_two_1200s_on_2400(solver):
    problem = make_problem(pieces=[(1200, 2)], stocks=[2400], kerf=3)
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 2


@pytest.mark.parametrize("solver", SOLVERS)
def test_one_2400_fits_one_2400_with_kerf(solver):
    problem = make_problem(pieces=[(2400, 1)], stocks=[2400], kerf=3)
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 1
    assert result[0].cuts[0].length == 2400


@pytest.mark.parametrize("solver", SOLVERS)
def test_exact_fit_with_kerf(solver):
    problem = make_problem(pieces=[(1200, 1), (1197, 1)], stocks=[2400], kerf=3)
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 1


@pytest.mark.parametrize("solver", SOLVERS)
def test_piece_longer_than_stock(solver):
    pieces = (
        Piece(SECTION1, "rafter", 2600, 1),
        Piece(SECTION1, "nogging", 801, 1),
    )
    stock = StockLength(SECTION1, 800)
    with pytest.raises(PieceTooLongError, match="is longer than stock"):
        solver(Problem((stock,), 0, pieces))


@pytest.mark.parametrize("solver", SOLVERS)
def test_no_pieces_returns_empty_list(solver):
    problem = make_problem(pieces=[], stocks=[2400])
    result = solver(problem)
    assert_valid(result, problem)
    assert result == []


@pytest.mark.parametrize("solver", SOLVERS)
def test_no_stock_raises(solver):
    piece = Piece(SECTION1, "stud", 1475, 1)
    with pytest.raises(CutOptError, match="There is no stock to choose boards from"):
        solver(Problem((), 0, (piece,)))


@pytest.mark.parametrize("solver", SOLVERS)
def test_no_piece_and_no_stock_raises(solver):
    with pytest.raises(CutOptError, match="There is no stock to choose boards from"):
        solver(Problem((), 0, ()))


@pytest.mark.parametrize("solver", SOLVERS)
def test_different_sections_never_share_a_board(solver):
    pieces = (
        Piece(SECTION1, "stud", 1000, 1),
        Piece(SECTION2, "stud", 1000, 1),
    )
    stock = (
        StockLength(SECTION1, 4800),
        StockLength(SECTION2, 2400),
    )
    problem = Problem(stock, 0, pieces)
    result = solver(problem)
    assert_valid(result, problem)
    assert len(result) == 2


@pytest.mark.parametrize("solver", SOLVERS)
def test_section_without_stock_raises(solver):
    piece = Piece(SECTION1, "stud", 2400, 1)
    stock = StockLength(SECTION2, 2400)
    with pytest.raises(NoStockForSectionError, match="No stock for section"):
        solver(Problem((stock,), 0, (piece,)))


@pytest.mark.parametrize("solver", SOLVERS)
def test_too_long_check_if_uses_own_section(solver):
    piece = Piece(SECTION1, "rafter", 3000, 1)
    stocks = (
        StockLength(SECTION1, 2400),
        StockLength(SECTION2, 4800),
    )
    problem = Problem(stocks, 0, (piece,))
    with pytest.raises(PieceTooLongError, match="longer than stock"):
        solver(problem)


@pytest.mark.parametrize("solver", SOLVERS)
def test_shrinks(solver):
    problem = make_problem(pieces=[(1950, 1)], stocks=[2400, 4800], kerf=3)
    result = solver(problem)
    assert_valid(result, problem)
    assert result[0].stock_length == 2400


@pytest.mark.parametrize("solver", SOLVERS)
def test_picks_the_middle(solver):
    problem = make_problem(pieces=[(1700, 2)], stocks=[2400, 3600, 4800], kerf=3)
    result = solver(problem)
    assert_valid(result, problem)
    assert result[0].stock_length == 3600


@pytest.mark.parametrize("solver", SOLVERS)
def test_keeps_a_full_board(solver):
    problem = make_problem(pieces=[(4700, 1)], stocks=[2400, 4800])
    result = solver(problem)
    assert_valid(result, problem)
    assert result[0].stock_length == 4800


def test_unknown_solver_raises():
    name = "banana"
    valid = ", ".join(VALID_SOLVERS)
    with pytest.raises(UnknownSolverError, match=f"Solver named {name} is not valid, try {valid}"):
        get_solver(name)
