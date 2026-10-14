from collections import Counter
from dataclasses import dataclass
from typing import Self

from .models import CutPattern


@dataclass(frozen=True)
class Metrics:
    board_count: int
    stock_length_total: int
    piece_length_total: int
    shopping_list: dict[tuple[str, int], int]

    @property
    def waste(self) -> int:
        return self.stock_length_total - self.piece_length_total

    @property
    def waste_percent(self) -> float:
        if self.stock_length_total == 0:
            return 0.0
        return (self.waste / self.stock_length_total) * 100


    """Summarize the cutting plan from any solver """
    @classmethod
    def from_boards(cls, boards: list[CutPattern]) -> Self:
        stock_length_total = sum(b.stock_length for b in boards)
        piece_length_total = sum(p.length for b in boards for p in b.cuts)
        shopping_list = dict(Counter((board.section, board.stock_length) for board in boards))
        return cls(
            board_count=len(boards),
            stock_length_total=stock_length_total,
            piece_length_total=piece_length_total,
            shopping_list=shopping_list,
        )
