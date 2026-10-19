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
**Context:** Several solvers (FFD and CP-SAT) must all produce valid plans.
**Decision:** Every test result goes through `assert_valid`, which checks that no board overflows, no board mixes sections, and no piece is lost or duplicated. "What" tests (board counts, errors) are meant to be shared between solvers. "How" tests (exact first-fit placement) stay solver-specific. `make_problem` and `solve` helpers keep tests short.
**Alternatives:** Only assert specific outputs. Rejected, because a result can have the right
board count and still be physically impossible.
**Trade-off:** The invariant recomputes the used length independently of the solver, so a bug in the solver's formula can't hide.


## 10. Metrics is a frozen dataclass with derived waste
**Context:** The CLI, the API and the benchmark all need the same summary of a cutting plan.
**Decision:** `Metrics` is a frozen dataclass storing only the raw facts (board count, timber bought, timber in pieces, shopping list). `waste` and `waste_percent` are computed as properties.
**Alternatives:** Return a dict, or store waste as fields. Rejected: a dict has no fixed field names or autocomplete, and stored waste values could disagree with the totals.
**Trade-off:** Waste is recalculated on every access, which costs nothing at this size. Waste includes kerf dust, since that timber is bought but never becomes a piece. Rounding happens only when displaying.

## 11. Metrics are built with a classmethod, independent of the solver
**Context:** Metrics must work on results from FFD and CP-SAT alike.
**Decision:** `Metrics.from_boards(boards)` is an alternative constructor that takes only a list of boards. It knows nothing about how they were produced.
**Alternatives:** A plain `summarize(boards)` function (equally valid), or metrics computed inside each solver (rejected: duplicated code, and the benchmark couldn't compare solvers fairly).
**Trade-off:** None notable. Construction lives next to the data it produces, and an empty plan gives zero metrics instead of a division-by-zero crash.

## 12. CSV input is validated at the file level
**Context:** cut lists come from users, often exported from Excel.
**Decision:** read with utf-8-sig (handles Excel's hidden marker), strip spaces from header names, require the four columns but allow extra ones (e.g. notes), and report bad values with their row number. read_cut_list returns one Piece per row; quantities are expanded later by the solver.
**Alternatives:** regex-validate the section format (rejected, because sections are free labels like KVH 60x120), or fail on extra columns (rejected as unfriendly).
**Trade-off:** the format is permissive, so a typo in a section name creates a separate section instead of an error.

## 13. The core has no web dependencies
**Context:** The optimizer will be used from a CLI, a REST API and a benchmark.
**Decision:** The core package (`src/cutopt/`) never imports Django or any other web library.
It takes Python objects in and returns Python objects. The dependency goes one way only:
`api/` imports `cutopt`, never the other way round. Each entry point (CLI, API, benchmark) is a
thin layer that wires the same core modules together.
**Why:**
- **Lightweight to use:** the CLI, or calling `greedycut` from a script, doesn't require
  installing Django and its stack.
- **Easy to test:** the whole test suite runs in under a second, with no server or database.
- **Replaceable front end:** switching from Django to another framework (e.g. FastAPI) would
  only touch `api/`; solvers, models and metrics stay unchanged.
- **Clear boundaries:** web concerns (HTTP, JSON, authentication, databases) stay in the web
  layer, and optimisation stays in the core.

**Alternatives:** Build the solver inside the Django project. Rejected: every use of the solver
would then need Django, and tests would need its setup.
**Trade-off:** The CLI ships inside the package, so the core does depend on the small CLI
libraries `typer` and `rich`. Django will go into a separate dependency group, not the core
dependencies.