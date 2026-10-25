class CutOptError(ValueError):
    """Base class for invalid cutting problems."""


class NoStockForSectionError(CutOptError):
    """A piece's section has no matching stock length."""


class PieceTooLongError(CutOptError):
    """A piece is longer than every stock length of its section."""


class UnknownSolverError(CutOptError):
    """User asked for a solver that does not exist"""
