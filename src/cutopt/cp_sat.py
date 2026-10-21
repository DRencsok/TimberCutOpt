from ortools.sat.python import cp_model
from collections import defaultdict

from .models import Problem, CutPattern
from .greedy import greedycut
from .io import read_cut_list, parse_stock, stock_for_sections


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

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        print(solver.status_name(status))

        for p in range(len(x)):
            for b in range(len(boards)):
                if solver.value(x[p][b]) == 1:
                    print(f" Piece {p} {section_pieces[p].length} -> board {b}")


if __name__ == "__main__":
    pieces = read_cut_list("examples/shed.csv")
    sections = {p.section for p in pieces}
    lengths = parse_stock("2400,3600,4800")
    stocks = stock_for_sections(sections, lengths)
    cp_sat(Problem(stock=stocks, kerf=3, pieces=pieces))
