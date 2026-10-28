import random
from pathlib import Path

from cutopt.io import read_cut_list, stock_for_sections
from cutopt.models import Piece, Problem, StockLength

STOCK = (2400, 3600, 4800, 6000)
SHED_CSV = Path(__file__).parent.parent / "examples" / "shed.csv"


def make_problem(pieces, stocks=STOCK, kerf=3, section="47x100 C24"):
    """Build a single-section Problem from plain numbers.

    pieces is a list of (length, quantity) pairs, stocks a list of lengths.
    """
    return Problem(
        stock=tuple(StockLength(section, length) for length in stocks),
        kerf=kerf,
        pieces=tuple(Piece(section, "piece", length, qty) for length, qty in pieces),
    )


def _shed() -> Problem:
    """Load examples/shed.csv the same way the CLI does."""
    pieces = read_cut_list(SHED_CSV)
    sections = {p.section for p in pieces}
    return Problem(stock=stock_for_sections(sections, STOCK), kerf=3, pieces=pieces)


def hardcoded_problems() -> dict[str, Problem]:
    """Return a small set of hand-made problems, keyed by name.

    Each one checks something specific, so the benchmark's numbers can be
    compared against answers known in advance.
    """
    return {
        # Fits exactly: 1 board, 0 % waste
        "tiny": make_problem([(1200, 2)], stocks=[2400], kerf=0),
        # Same pieces, but the kerf no longer fits: 2 boards
        "kerf_boundary": make_problem([(1200, 2)], stocks=[2400], kerf=3),
        # Greedy buys 16800 mm, CP-SAT 14400 mm
        "greedy_loses": make_problem([(2300, 3), (1700, 3), (900, 2)], stocks=[2400, 3600, 4800]),
        # 100 pieces from only 4 lengths
        "big_repeats": make_problem([(1950, 40), (550, 30), (2150, 20), (1200, 10)]),
        # A real job with two sections
        "shed": _shed(),
    }


def random_problem(n_pieces: int, seed: int) -> Problem:
    rng = random.Random(seed)
    problem = make_problem((rng.randrange(300, 3001, 50), 1) for _ in range(n_pieces))
    return problem
