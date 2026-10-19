import csv

from .errors import CutOptError
from .models import Piece, StockLength

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
                    f"row {i}'s length {row['length']}"
                    f" and quantity {row['quantity']}"
                    f" must be a positive integer"
                ) from None
        return tuple(pieces)


def parse_stock(text) -> list[int]:
    try:
        stock_ints = [int(part) for part in text.split(",")]
    except ValueError:
        raise CutOptError(f"Expected integers, got {text}") from None
    else:
        return stock_ints


def stock_for_sections(sections, lengths):
    return tuple(
        StockLength(section=section, length=length) for section in sections for length in lengths
    )
