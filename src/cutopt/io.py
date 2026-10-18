import csv

from .errors import CutOptError
from .models import Piece

REQUIRED = {"label", "length", "quantity", "section"}


def read_cut_list(path) -> tuple[Piece, ...]:
    with open(path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        # Error checking
        reader.fieldnames = [name.strip() for name in reader.fieldnames or []]
        columns = set(reader.fieldnames)
        missing = REQUIRED - columns
        if missing:
            raise CutOptError(f"missing columns: {', '.join(sorted(missing))}")

        pieces = []
        for i, row in enumerate(reader, start=2):
            try:
                pieces.append(
                    Piece(
                        label=row["label"].strip(),
                        length=int(row["length"]),
                        quantity=int(row["quantity"]),
                        section=row["section"].strip(),
                    )
                )
            except ValueError:
                raise CutOptError(
                    f"row {i - 1}'s length {row['length']}"
                    f" and quantity {row['quantity']}"
                    f" must be whole numbers"
                ) from None
        return tuple(pieces)
