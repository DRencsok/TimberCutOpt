from collections import defaultdict

from ortools.sat.python import cp_model

from .greedy import greedycut
from .io import parse_stock, read_cut_list, stock_for_sections
from .models import CutPattern, Problem


def cp_sat(problem: Problem) -> list[CutPattern]:
    cutpattern = greedycut(problem)
    boards_by_section = defaultdict(list)

    for board in cutpattern:
        boards_by_section[board.section].append(board)

    # Expand boards by sections and add its pieces
    for section, boards in boards_by_section.items():
        section_pieces = []
        for board in boards:
            for piece in board.cuts:
                section_pieces.append(piece)

        # Create a 2D Table with pieces and boards, ask if piece is on board
        model = cp_model.CpModel()
        x = []
        for p in range(len(section_pieces)):
            row = []
            for b in range(len(boards)):
                row.append(model.new_bool_var(f"x_{p}_{b}"))
            x.append(row)

        for row in x:
            model.add(sum(row) == 1)

        section_lengths = [stock.length for stock in problem.stock if stock.section == section]

        # Create a 2D Table with boards and their stock lengths
        use = []
        for b in range(len(boards)):
            board_row = []
            for s in range(len(section_lengths)):
                board_row.append(model.new_bool_var(f"use_{b}_{s}"))
            use.append(board_row)

        for row in use:
            model.add(sum(row) <= 1)

        # Sum of board's used lengths cannot be bigger than the board's length
        for b in range(len(x[0])):
            left = sum(section_pieces[p].length * x[p][b] for p in range(len(x)))
            right = sum(section_lengths[s] * use[b][s] for s in range(len(use[0])))

            model.add(left <= right)

        # Add a goal to minimize the timber bought
        total = sum(
            section_lengths[s] * use[b][s]
            for b in range(len(use))
            for s in range(len(section_lengths))
        )
        model.minimize(total)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        status = solver.solve(model)
        print(solver.objective_value)
        print(solver.status_name(status))

        for p in range(len(x)):
            for b in range(len(boards)):
                if solver.value(x[p][b]) == 1:
                    print(f" Piece {p} {section_pieces[p].length} -> board {b}")

        for b in range(len(use)):
            for s in range(len(use[b])):
                if solver.value(use[b][s]) == 1:
                    print(f"Board {b} length: {section_lengths[s]}")


if __name__ == "__main__":
    pieces = read_cut_list("examples/shed.csv")
    sections = {p.section for p in pieces}
    lengths = parse_stock("2400,3600,4800")
    stocks = stock_for_sections(sections, lengths)
    cp_sat(Problem(stock=stocks, kerf=3, pieces=pieces))
