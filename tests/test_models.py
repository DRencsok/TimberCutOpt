import pytest
from helpers import make_problem

from cutopt.errors import CutOptError
from cutopt.greedy import greedycut
from cutopt.models import CutPattern, Piece, Problem, StockLength

SECTION = "47x100 C24"
CLEANUP_SECTIONS = [
    ("47x100 C24", "47x100 C24"),
    ("47X100 C24", "47x100 C24"),
    ("47x100 c24", "47x100 C24"),
    ("47x100    c24", "47x100 C24"),
    ("   47x100 c24   ", "47x100 C24"),
    ("47x150 c16", "47x150 C16"),
]
EMPTY = ["", " "]


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


@pytest.mark.parametrize("section, expected", CLEANUP_SECTIONS)
def test_section_is_normalised(section, expected):
    problem = make_problem(pieces=[(2200, 1)], stocks=[4800, 6000], section=section)
    assert problem.pieces[0].section == expected
    assert problem.stock[0].section == expected


def test_cleaned_up_sections_use_same_board():
    problem = Problem(
        stock=(StockLength(section="47X100 c24", length=6000),),
        kerf=0,
        pieces=(
            Piece(section="47x100    C24", label="stud", length=1200, quantity=1),
            Piece(section="   47X100 c24  ", label="nogging", length=1200, quantity=1),
        ),
    )
    result = greedycut(problem)
    assert len(result) == 1
    assert result[0].section == "47x100 C24"
    assert len(result[0].cuts) == 2
    assert result[0].cuts[0].section == "47x100 C24"
    assert result[0].cuts[1].section == "47x100 C24"


@pytest.mark.parametrize("empty", EMPTY)
def test_empty_section_input_doesnt_pass_throug_normalisation(empty):
    with pytest.raises(CutOptError, match="Section is a required field"):
        make_problem(pieces=[(2150, 2)], stocks=[3600, 4800], section=empty)
