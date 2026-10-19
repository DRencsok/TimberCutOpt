from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .errors import CutOptError
from .greedy import greedycut
from .io import parse_stock, read_cut_list, stock_for_sections
from .metrics import Metrics
from .models import Problem

app = typer.Typer()
console = Console()


@app.callback()
def main():
    """Turn a timber cut list into a cutting plan with minimal waste"""


@app.command()
def solve(
    cut_list: Annotated[
        Path,
        typer.Argument(help="CSV with label,length,quantity,section", exists=True, dir_okay=False),
    ],
    stock: Annotated[
        str, typer.Option(help="Comma-separated stock lengths in mm")
    ] = "2400,3600,4800,6000",
    kerf: Annotated[int, typer.Option(help="Saw blade width in mm")] = 3,
):
    """Optimise a cut list and print the cutting plan, shopping list and summary.

    Stock lengths apply to every section in the cut list.
    """

    try:
        pieces = read_cut_list(cut_list)
        sections = {p.section for p in pieces}
        lengths = parse_stock(stock)
        stocks = stock_for_sections(sections, lengths)
        boards = greedycut(Problem(stock=stocks, kerf=kerf, pieces=pieces))
        metrics = Metrics.from_boards(boards)

        # Print Tables of summary

        table = Table(title="Cutting Plan")
        table.add_column("Id")
        table.add_column("Section")
        table.add_column("Stock")
        table.add_column("Cuts")
        table.add_column("Offcut (mm)", justify="center")
        for i, board in enumerate(boards, start=1):
            table.add_row(
                str(i),
                board.section,
                str(board.stock_length),
                _format_cuts(board),
                str(board.offcut),
            )

        console.print(table)

        table = Table(title="Shopping List")
        table.add_column("Section")
        table.add_column("Length")
        table.add_column("Quantity")
        for (section, length), qty in sorted(metrics.shopping_list.items()):
            table.add_row(section, str(length), str(qty))

        console.print(table)

        table = Table(title="Summary")
        table.add_column("Boards")
        table.add_column("Stock length total")
        table.add_column("Piece length total")
        table.add_column("Waste")
        table.add_column("Waste %")
        table.add_row(
            str(metrics.board_count),
            str(metrics.stock_length_total),
            str(metrics.piece_length_total),
            str(metrics.waste),
            f"{metrics.waste_percent:.2f}",
        )
        console.print(table)

    except CutOptError as error:
        console.print(f"[bold red]Error: {error}[/bold red]")
        raise typer.Exit(code=1) from None


def _format_cuts(board):
    """Describe a board's cuts as text, grouping identical pieces,
    e.g. 'stud 1950 x2, nogging 550'."""

    counter = Counter((piece.label, piece.length) for piece in board.cuts)
    parts = []
    for (label, length), count in counter.items():
        if count == 1:
            parts.append(f"{label} {length}")
        else:
            parts.append(f"{label} {length} x{count}")
    return ", ".join(parts)


if __name__ == "__main__":
    app()
