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
- **Easy to test:** the whole test suite runs with no server or database.
- **Replaceable front end:** switching from Django to another framework (e.g. FastAPI) would
  only touch `api/`; solvers, models and metrics stay unchanged.
- **Clear boundaries:** web concerns (HTTP, JSON, authentication, databases) stay in the web
  layer, and optimisation stays in the core.

**Alternatives:** Build the solver inside the Django project. Rejected: every use of the solver
would then need Django, and tests would need its setup.
**Trade-off:** The CLI ships inside the package, so the core does depend on the small CLI
libraries `typer` and `rich`, plus OR-Tools for the CP-SAT solver (see decision 15). Django will
go into a separate dependency group, not the core dependencies.

## 14. CP-SAT runs greedy first and uses its board count as a ceiling
**Context:** The CP-SAT model needs a fixed number of boards up front: one yes/no variable per piece × board. Too few boards could cut off the best plan; too many slow the solver down.

**Decision:** `cp_sat` calls `greedycut` first and, per section, uses greedy's board count as the maximum number of boards. Greedy's plan is one valid way to fill that grid, so CP-SAT's best answer can never be worse than greedy's. Unused boards stay empty, which means "don't buy".
Calling greedy also validates the input, so both solvers raise the same errors.
**Alternatives:**
- One board per piece (always enough, needs no greedy). Rejected: the grid grows as n × n (28 × 28 = 784 boxes instead of 28 × 9 = 252 for the shed), and the extra columns add many duplicate copies of the same plan (symmetry) for the solver to search through.
- Move expansion and validation out of `greedycut` into shared helpers. Rejected for now: it still doesn't give a board count.

**Trade-off:** CP-SAT depends on greedy, so a greedy bug can affect both. Greedy takes milliseconds, so it barely affects CP-SAT's runtime in the benchmark.

## 15. OR-Tools is a required dependency
**Context:** `cp_sat.py` imports OR-Tools at the top of the module. As an optional extra, a plain install would crash with an `ImportError` as soon as `cp_sat` is imported, even for users who only want greedy.

**Decision:** `ortools` is in the core `dependencies`, so every install can use both solvers.

**Alternatives:** Keep it as an optional `cpsat` extra and import it lazily, with a clear error when it's missing. Rejected for now: CP-SAT is a main feature of the project, not an add-on, and the extra adds import guards and an install step to remember.

**Trade-off:** The install gets heavier: OR-Tools is a ~25 MB wheel and pulls in `numpy`, `pandas`, `protobuf` and `absl-py`. This doesn't conflict with decision 13, which is about keeping web libraries out of the core. OR-Tools is part of the optimisation itself.

## 16. `--time-limit` only applies to CP-SAT
**Context:** CP-SAT can run for a long time on large cut lists, so the CLI needs a way to cap its runtime. Greedy finishes in milliseconds and has no time limit parameter.

**Decision:** `solve` has a `--time-limit` option in seconds. The CLI passes it only when the solver is `cp_sat`. With `greedy` it is silently ignored. When the option is left out, `cp_sat` uses its own default (10 s).

**Alternatives:**
- Give every solver a `time_limit` parameter. Rejected: greedy would take an argument it never uses.
- Reject or warn about `--time-limit` with greedy. Rejected as unfriendly: the option does no harm there, and scripts can pass the same flags whichever solver they use.

**Trade-off:** The CLI has to know which solver takes which option. That's fine with two solvers.

## 17. Benchmark dependencies go in a `bench` extra
**Context:** The benchmark needs a table library to collect results and a plotting library for the charts in the README.

**Decision:** pandas and matplotlib are in an optional `bench` group, installed with `uv sync --extra bench`. pandas collects the result rows and writes the CSV; matplotlib draws the charts as PNG files.

**Alternatives:** Plotly. Rejected: its charts are interactive HTML, which GitHub doesn't render in a README, and saving them as PNG needs another heavy dependency (`kaleido`). It may still suit the planned web frontend.

**Trade-off:** One more install flag to remember. `uv sync --extra dev` alone removes the benchmark libraries again.

## 18. Solvers are timed from outside
**Context:** The benchmark compares runtimes, and a single measurement is noisy (other programs, first-call setup).

**Decision:** `benchmarks/timing.py` times a solver from outside with `perf_counter`, around the solver call only. Each solver first solves a tiny warm-up problem untimed, then runs `repeats` times; the median time and the last run's plan are returned. The solvers themselves contain no timing code.

**Alternatives:**
- Time the whole script. Rejected: it would include imports, problem generation and plotting.

**Trade-off:** CP-SAT can return a different plan on each run, so "the last run's plan" is a choice, not the only right answer. CP-SAT's time includes the greedy run it starts with (decision 14).

## 19. Results come from seeded random problems
**Context:** The benchmark needs problems to solve, and the choice of problems affects the conclusion.

**Decision:** The published results come only from random problems. `random_problem(n_pieces, seed)` uses its own `random.Random(seed)`, so every problem can be recreated exactly from its size and seed. Each problem has one section, quantity 1 per piece and lengths from 300 to 3000 mm in steps of 50. `hardcoded_problems()` stays in `benchmarks/problems.py` as a pipeline check: its answers are known in advance, so wrong numbers point to a bug in the benchmark.

**Alternatives:** Use hand-made problems for the results. Rejected: they are biased. `greedy_loses` was found by searching for a problem where greedy does badly, so including it would make greedy look worse than it is.

**Trade-off:** One section and quantity 1 are less realistic than a real cut list with repeated pieces, and the length range affects how hard the problems are. Both are stated next to the results.

## 20. Two solvers only, no Best-Fit
**Context:** Best-Fit Decreasing was planned as a second heuristic next to First-Fit Decreasing.

**Decision:** The project has two solvers: one heuristic (First-Fit Decreasing) and one exact solver (CP-SAT). Best-Fit is dropped.

**Alternatives:** Implement Best-Fit as well. Rejected: on 1D problems it gives almost the same results as First-Fit (the same worst-case guarantee, and usually the same board count or one apart), so a third line would sit on top of greedy's in the charts.

**Trade-off:** None for the benchmark question. If wanted later, Best-Fit would only need a new packing function (it can reuse `_shrink`, decision 7) and one entry in `SOLVERS`.

## 21. CP-SAT starts from greedy's plan and never returns a worse one
**Context:** CP-SAT already runs greedy first (decision 14), but it started its search from nothing. On large problems it could run out of time before finding a plan as good as greedy's.

**Decision:** Greedy's plan is passed to CP-SAT as a hint: every piece × board variable and every board × stock length variable gets the value greedy chose. After solving, if CP-SAT's total stock length is still larger than greedy's, greedy's boards are returned for that section.

**Alternatives:**
- No hint. Rejected: CP-SAT has to find a first good plan by itself, which gets slower as problems grow.
- Hint only the piece placement. Rejected: a partial hint is harder for the solver to complete, and the stock length of each board is known from greedy anyway.

**Trade-off:** The benchmark showed the same plans with and without the hint on every problem. The hint only changed runtimes: up to ~4.6× faster when CP-SAT proves the best plan before the limit (50 pieces seed 1: 4.65 s → 1.01 s, `shed`: 1.09 s → 0.25 s). Runs that hit the time limit still hit it, because the time goes into *proving* the plan is optimal, which a hint doesn't help with. The extra check makes "never worse than greedy" a guarantee instead of an expectation.

## 22. The benchmark uses a fixed 30 s time limit and fewer repeats
**Context:** The benchmark is extended to 100, 250 and 500 pieces. With the CLI default of 10 s (decision 16), most CP-SAT runs on large problems stop at the limit, and repeating a run that hits the limit only measures the limit again.

**Decision:** The benchmark gives CP-SAT a fixed 30 s limit for every size. CP-SAT is timed over 2 repeats instead of 5, and greedy keeps 5, because its microsecond timings are the noisy ones. The CLI default stays at 10 s. The time limit is stated next to the results.

**Alternatives:**
- Keep 10 s. Rejected: large problems would barely get a chance to improve on greedy's starting plan.
- Scale the limit with problem size. Rejected: the runtime chart would mix different limits, and it is harder to explain than one number.
- Keep 5 repeats for both. Rejected: at 30 s per timed-out run the benchmark would take far longer without telling us more.
- 2 repeats for both. Rejected: greedy's runs take microseconds, so its median needs more samples, and they cost nothing.

**Trade-off:** The benchmark results are from a 30 s limit, so a CLI user with the default 10 s may get slightly worse plans on large cut lists. The limit applies per section, so a cut list with several sections can run for a multiple of it (the random problems have one section, decision 19). The benchmark needs its own solver table instead of reusing `SOLVERS`.
