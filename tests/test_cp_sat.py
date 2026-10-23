from pathlib import Path

from helpers import assert_valid, make_problem

from cutopt.cp_sat import cp_sat
from cutopt.greedy import greedycut
from cutopt.io import parse_stock, read_cut_list, stock_for_sections
from cutopt.metrics import Metrics
from cutopt.models import Problem

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_beats_greedy():
    problem = make_problem(pieces=[(2500, 1), (2000, 1), (1500, 3), (1000, 1)], stocks=[5000])
    result = cp_sat(problem)
    assert_valid(result, problem)
    assert len(result) == 2
    assert len(greedycut(problem)) == 3


def test_never_worse_than_greedy():
    pieces = read_cut_list(EXAMPLES / "shed.csv")
    sections = {p.section for p in pieces}
    lengths = parse_stock("2400,3600,4800")
    stocks = stock_for_sections(sections, lengths)
    problem = Problem(stock=stocks, kerf=3, pieces=pieces)
    cp_sat_boards = cp_sat(problem)
    greedy_boards = greedycut(problem)
    assert_valid(cp_sat_boards, problem)
    assert_valid(greedy_boards, problem)

    cp_sat_total = Metrics.from_boards(cp_sat_boards).stock_length_total
    greedy_total = Metrics.from_boards(greedy_boards).stock_length_total
    assert greedy_total >= cp_sat_total
