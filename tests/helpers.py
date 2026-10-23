from cutopt.models import Piece, Problem, StockLength

SECTION1 = "47x100 C24"
SECTION2 = "47x150 C24"


# Helper function that checks there are no overflow and no losses or duplicates that return
def assert_valid(result, problem):
    for i, board in enumerate(result):
        # Check if all cut sections are the same as board section
        cut_sections = {p.section for p in board.cuts}
        assert cut_sections == {board.section}, (
            f"cut is from {cut_sections} while board is {board.section}"
        )

        used = sum(p.length for p in board.cuts) + (len(board.cuts) - 1) * board.kerf
        assert used <= board.stock_length, (
            f"board {i + 1} overflows: used {used} > {board.stock_length}"
        )

    lengths = []
    for p in problem.pieces:
        for _ in range(p.quantity):
            lengths.append(p.length)

    result_lengths = []
    for board in result:
        for piece in board.cuts:
            result_lengths.append(piece.length)

    assert sorted(lengths) == sorted(result_lengths), (
        f"Expected {sorted(lengths)}, got {sorted(result_lengths)}"
    )


def make_problem(pieces, stocks, kerf=0, section=SECTION1):
    """Build a single-section Problem from plain numbers.

    pieces is a list of (length, quantity) pairs, stocks a list of lengths.
    """
    return Problem(
        stock=tuple(StockLength(section, length) for length in stocks),
        kerf=kerf,
        pieces=tuple(Piece(section, "piece", length, qty) for length, qty in pieces),
    )
