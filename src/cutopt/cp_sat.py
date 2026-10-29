"""Exact CP-SAT solver for the 1D cutting stock problem."""

from collections import defaultdict

from ortools.sat.python import cp_model

from .greedy import greedycut
from .metrics import Metrics
from .models import CutPattern, Problem


def cp_sat(problem: Problem, time_limit: float = 10) -> list[CutPattern]:
    """Solve a cutting problem with Google OR-Tools' CP-SAT solver.

    Greedy runs first: it validates the input, and its board count per section
    is the most boards CP-SAT may use. Each section is solved separately,
    minimising the total stock length bought.

    Args:
        problem: The pieces to cut, the available stock lengths and the kerf.
        time_limit: The maximum time limit for the CP-SAT solver

    Returns:
        The boards for all sections in one list. An empty list if there are no pieces.

    Raises:
        CutOptError, NoStockForSectionError, PieceTooLongError: Same as greedycut.
    """

    cutpattern = greedycut(problem)
    boards_by_section = defaultdict(list)

    for board in cutpattern:
        boards_by_section[board.section].append(board)

    result = []

    # Expand boards by sections and add its pieces
    for section, boards in boards_by_section.items():
        section_pieces = []
        greedy_board_of = []
        for board_index, board in enumerate(boards):
            for piece in board.cuts:
                section_pieces.append(piece)
                greedy_board_of.append(board_index)

        num_boards = len(boards)
        num_pieces = len(section_pieces)

        # Create a 2D Table with pieces and boards, ask if piece is on board
        model = cp_model.CpModel()
        x = []
        for p in range(num_pieces):
            row = []
            for b in range(num_boards):
                row.append(model.new_bool_var(f"x_{p}_{b}"))
            x.append(row)

        for row in x:
            model.add(sum(row) == 1)

        section_lengths = [stock.length for stock in problem.stock if stock.section == section]
        num_lengths = len(section_lengths)

        # Create a 2D Table with boards and their stock lengths
        use = []
        for b in range(num_boards):
            board_row = []
            for s in range(num_lengths):
                board_row.append(model.new_bool_var(f"use_{b}_{s}"))
            use.append(board_row)

        for row in use:
            model.add(sum(row) <= 1)

        # Hint for cp_sat so it starts where greedy stopped
        for p in range(num_pieces):
            for b in range(num_boards):
                if b == greedy_board_of[p]:
                    model.add_hint(x[p][b], 1)
                else:
                    model.add_hint(x[p][b], 0)

        for b in range(num_boards):
            for s in range(num_lengths):
                if boards[b].stock_length == section_lengths[s]:
                    model.add_hint(use[b][s], 1)
                else:
                    model.add_hint(use[b][s], 0)

        # Sum of board's used lengths cannot be bigger than the board's length
        for b in range(num_boards):
            left = sum(
                ((section_pieces[p].length + problem.kerf) * x[p][b]) for p in range(num_pieces)
            )
            right = sum((section_lengths[s] + problem.kerf) * use[b][s] for s in range(num_lengths))

            model.add(left <= right)

        # Add a goal to minimize the timber bought
        total = sum(
            section_lengths[s] * use[b][s] for b in range(num_boards) for s in range(num_lengths)
        )
        model.minimize(total)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        status = solver.solve(model)

        # No plan found in time, so keep greedy's boards for this section
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            result.extend(boards)
            continue

        # CP-SAT is worse than greedy, so append greedy's boards
        if solver.value(total) > Metrics.from_boards(boards).stock_length_total:
            result.extend(boards)
            continue

        for b in range(num_boards):
            for s in range(num_lengths):
                if solver.value(use[b][s]) == 1:
                    cuts = []
                    for p in range(num_pieces):
                        if solver.value(x[p][b]) == 1:
                            cuts.append(section_pieces[p])
                    result.append(
                        CutPattern(
                            stock_length=section_lengths[s],
                            kerf=problem.kerf,
                            section=section,
                            cuts=sorted(cuts, key=lambda piece: piece.length, reverse=True),
                        )
                    )
    return result
