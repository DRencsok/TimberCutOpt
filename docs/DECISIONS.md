# Decisions during development

A log of the design decisions behind TimberCutOpt: what was decided, what else was considered, and what it costs. New entries go at the bottom.

## 1. Lengths are whole millimetres
**Context:** Lengths could be stored as floats (metres) or integers (millimetres).
**Decision:** All lengths and the kerf are `int` millimetres.
**Alternatives:** Floats in metres. Rejected, because rounding errors make fit checks like `used <= stock_length` unreliable, and CP-SAT only accepts integers.
**Trade-off:** No sub-millimetre precision, which a saw can't deliver anyway.

## 2. Kerf is modelled exactly
**Context:** Every saw cut turns 2–4 mm of wood into dust, which decides whether pieces fit.
**Decision:** A board holding *n* pieces uses `sum(lengths) + (n − 1) × kerf`. No cut is needed before the first piece, so a 2400 mm piece fits a 2400 mm board.
**Alternatives:** Ignore kerf, or add one kerf per piece. Both give wrong answers at the boundary: two 1200 mm pieces would wrongly fit a 2400 mm board with a 3 mm kerf, or a single 2400 mm piece would wrongly not fit.
**Trade-off:** A slightly more complex fit check, pinned down by boundary tests.

## 3. Inputs are immutable
**Context:** Greedy and CP-SAT will solve the same problem and be compared in a benchmark.
**Decision:** `Piece`, `StockLength` and `Problem` are frozen dataclasses holding tuples.
**Alternatives:** Plain mutable classes and lists. Rejected, because one solver could change the input (for example, sort it in place) and silently corrupt the comparison.
**Trade-off:** Callers must pass tuples. Type hints are not enforced at runtime, so a list can
still slip through.

## 4. Each section is solved separately
**Context:** Pieces can only be cut from stock of the same section (e.g. `47x100 C24`).
**Decision:** Pieces and stock are grouped by section, and each group is packed independently.
**Alternatives:** One big problem with a "same section" rule in the fit check. Rejected as more complex, with no benefit.
**Trade-off:** None in practice. Sections can never share a board, so splitting loses nothing and gives several smaller problems, which also helps CP-SAT.

## 5. Custom errors share one base class
**Context:** Invalid input must be reported clearly to CLI and API users.
**Decision:** `NoStockForSectionError` and `PieceTooLongError` subclass `CutOptError`, which subclasses `ValueError`.
**Alternatives:** Plain `ValueError` everywhere. Rejected, because callers couldn't tell the cases apart, and tests couldn't prove the right error was raised.
**Trade-off:** One extra module (`errors.py`).

## 6. No pieces returns an empty list, and impossible input raises
**Context:** Edge cases need defined behaviour.
**Decision:** Raise only when there is no sensible answer: a piece longer than any stock of its section, or a section without stock. An empty cut list returns `[]`, meaning "buy nothing".
**Alternatives:** Raise on empty input. Rejected, because it forces every caller into a `try/except` for a valid situation (like `sum([])` returning `0`).
**Trade-off:** User-facing messages such as "your cut list is empty" belong in the CLI or API layer, not in the solver.

## 7. Packing and shrinking are separate functions
**Context:** The solver both decides which pieces share a board and which stock length each board is cut from.
**Decision:** `_pack` does first-fit packing for one section; `_shrink` post-processes the boards. `greedycut` coordinates: validate, group, pack, shrink.
**Alternatives:** One function doing everything. Rejected as harder to read, test and extend.
**Trade-off:** Two passes over the boards, which costs nothing noticeable.
Best-Fit Decreasing will be able to reuse `_shrink` unchanged.

## 8. Boards are shrunk after packing, not during
**Context:** `_pack` always opens the longest stock board, which wastes timber on boards that end up half empty.
**Decision:** After packing, each board moves to the shortest stock length that still fits its contents.
**Alternatives:** Choose the board size while packing. Rejected, because a board's final contents aren't known until packing ends.
**Trade-off:** Cheap and simple, but not optimal: a smarter packing could plan around short boards from the start. CP-SAT is expected to do better here, and the benchmark will show by how much.


## 9. Tests are split into invariants, behaviour and solver-specific checks
**Context:** Several solvers (FFD, later BFD and CP-SAT) must all produce valid plans.
**Decision:** Every test result goes through `assert_valid`, which checks that no board overflows, no board mixes sections, and no piece is lost or duplicated. "What" tests (board counts, errors) are meant to be shared between solvers. "How" tests (exact first-fit placement) stay solver-specific. `make_problem` and `solve` helpers keep tests short.
**Alternatives:** Only assert specific outputs. Rejected, because a result can have the right
board count and still be physically impossible.
**Trade-off:** The invariant recomputes the used length independently of the solver, so a bug in the solver's formula can't hide.
