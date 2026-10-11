# Timber Cut Optimizer

**Turns a construction cut list into a cutting plan that wastes as little timber as possible.**
Includes a fast greedy heuristic and an exact CP-SAT model, plus a benchmark comparing the two.

> 🚧 Work in progress. See the [Roadmap](#roadmap) for current status.

---

## The problem

Building plans list the timber pieces a job needs: 16 wall studs at 1950 mm, 7 rafters at
2150 mm, and so on. Timber yards don't sell those lengths. They sell **standard stock lengths**
(typically 2400, 3600, 4800 and 6000 mm), and every piece has to be sawn out of a stock board.

Choosing which boards to buy and how to cut them decides how much timber ends up as offcuts
in the skip. Done by hand, this usually means over-ordering. Mathematically, it's the
**one-dimensional cutting stock problem**, which is NP-hard.

### Timber terms used in this project

| Term | Meaning |
|---|---|
| **Section** | The board's cross-section and grade, e.g. `47x100 C24`: 47 mm thick, 100 mm wide, strength class C24. Pieces can only be cut from stock of the same section. |
| **Stock length** | A length the timber yard sells, e.g. 4800 mm. Supply can be unlimited or limited. |
| **Kerf** | The width of wood the saw blade turns into dust on every cut (usually 2–4 mm). |
| **Offcut** | The leftover length after all pieces have been cut from a board. |

> Why 47 and not 50? Timber is sawn at a nominal 50 mm, then dried and planed/regularised,
> which removes a few millimetres. A "2×4" is really 47×100 in the UK/EU, or 38×89 in North America.

---

## Example

Input cut list (`examples/shed.csv`):

```csv
label,length,quantity,section
wall stud,1950,16,47x100 C24
nogging,550,12,47x100 C24
rafter,2150,7,47x150 C24
```

```
cutopt solve examples/shed.csv --stock 2400,3600,4800 --kerf 3 --solver ffd
```

_Example output will be added once the CLI is implemented._

---

## How it works

### Modelling decisions
- **Lengths are whole millimetres (`int`).** This avoids floating-point rounding errors, and
  CP-SAT only accepts integers.
- **Kerf is modelled exactly.** *n* pieces on a board need *n − 1* cuts between them, plus one
  more if an offcut is left. So a 2400 mm piece fits a 2400 mm board, but two 1200 mm pieces
  with a 3 mm kerf don't.
- **Each section is solved separately.** Different sections can never share a board, so a whole
  job splits into independent 1D problems, one per section.
- **Usage is data, not type.** A "stud" and a "nogging" are just labels. What decides which
  board a piece can come from is its section.

### Solvers
- **Greedy: First-Fit / Best-Fit Decreasing.** Sort pieces longest-first, then put each one on
  the first (or tightest-fitting) board it fits on. Open a new board if none fits. Very fast,
  usually close to optimal, with no guarantee.
- **CP-SAT (Google OR-Tools).** A constraint programming model that assigns pieces to boards
  under capacity and kerf constraints and minimises the total timber bought. Can prove
  optimality on small and medium instances, and is seeded with the greedy solution as a warm
  start. _(planned)_

---

## Results: greedy vs CP-SAT

_Planned: benchmark across problem sizes (10–500 pieces) comparing waste %, boards used,
runtime and optimality gap._

---

## Installation & usage

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd TimberCutOpt
uv sync --extra dev
uv run cutopt --help
uv run pytest
```

---

## Project structure

```
src/cutopt/      core package: models, solvers, metrics, I/O, CLI (no web dependencies)
tests/           pytest unit and property-based tests
examples/        sample cut lists
benchmarks/      greedy vs CP-SAT comparison (planned)
api/             Django REST API (planned)
```

The optimizer core is a plain Python package. The CLI, the REST API and the benchmarks are
thin layers on top of the same code.

---

## Roadmap

- [ ] Core data models (pieces, stock, sections, kerf)
- [ ] Greedy solvers (FFD, BFD) + CLI
- [ ] CP-SAT solver
- [ ] Benchmark and results charts
- [ ] Django REST API
- [ ] Web frontend with visual cutting diagrams
- [ ] 2D sheet goods (plywood/OSB panels)
