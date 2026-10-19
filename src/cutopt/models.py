from dataclasses import dataclass, field

from .errors import CutOptError


@dataclass(frozen=True)
class Piece:
    section: str
    label: str
    length: int
    quantity: int = 1

    def __post_init__(self):
        if self.length <= 0:
            raise CutOptError(f"length: must be bigger than 0, got {self.length}")
        if self.quantity <= 0:
            raise CutOptError(f"quantity: must be bigger than 0, got {self.quantity}")


@dataclass(frozen=True)
class StockLength:
    section: str
    length: int
    quantity: int | None = None

    def __post_init__(self):
        if self.length <= 0:
            raise CutOptError(f"length: must be bigger than 0, got {self.length}")

        if self.quantity is not None and self.quantity <= 0:
            raise CutOptError(f"stock quantity: must be bigger than 0, got {self.quantity}")


@dataclass(frozen=True)
class Problem:
    stock: tuple[StockLength, ...]
    kerf: int
    pieces: tuple[Piece, ...]

    def __post_init__(self):
        if self.kerf < 0:
            raise CutOptError(f"kerf must be 0 or more, got {self.kerf}")


@dataclass
class CutPattern:
    stock_length: int
    kerf: int
    section: str
    cuts: list[Piece] = field(default_factory=list)

    @property
    def used_length(self) -> int:
        if not self.cuts:
            return 0
        return sum(piece.length for piece in self.cuts) + (len(self.cuts) - 1) * self.kerf

    @property
    def offcut(self) -> int:
        if not self.cuts:
            return self.stock_length
        return max(self.stock_length - self.used_length - self.kerf, 0)
