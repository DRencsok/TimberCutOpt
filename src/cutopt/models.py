from dataclasses import dataclass, field

@dataclass(frozen=True)
class Piece: 
    section: str
    label: str
    length: int
    quantity: int = 1

@dataclass(frozen=True)
class StockLength:
    section: str
    length: int
    quantity: int | None = None



@dataclass(frozen=True)
class Problem:
    stock: tuple[StockLength]
    kerf: int
    pieces: tuple[Piece, ...]

@dataclass
class CutPattern:
    stock_length: int
    kerf: int
    cuts: list[Piece] = field(default_factory=list)


