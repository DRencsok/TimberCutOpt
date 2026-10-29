from functools import partial
from pathlib import Path

import pandas as pd
from problems import hardcoded_problems, random_problem
from timing import timer

from cutopt.cp_sat import cp_sat
from cutopt.greedy import greedycut
from cutopt.metrics import Metrics

SIZES = [10, 25, 50, 100, 250, 500]
SEEDS = range(3)
TIME_LIMIT = 30
RESULTS_DIR = Path(__file__).parent / "results"
SOLVERS = {"greedy": (greedycut, 5), "cp_sat": (partial(cp_sat, time_limit=TIME_LIMIT), 2)}


def solve_all(problem, labels):
    """Run every solver on one problem and return one row per solver.

    labels is a dict of columns that say which problem this was
    (e.g. {"problem": "tiny"} or {"size": 10, "seed": 0}).
    """
    rows = []
    for name, (solver, repeats) in SOLVERS.items():
        runtime_s, plan = timer(solver, problem, repeats)
        metrics = Metrics.from_boards(plan)
        rows.append(
            {
                **labels,
                "solver": name,
                "boards": metrics.board_count,
                "stock_total": metrics.stock_length_total,
                "waste_percent": metrics.waste_percent,
                "runtime_s": runtime_s,
            }
        )
    return rows


def save(rows, filename):
    """Print the rows as a table and save them to results/<filename>."""
    df = pd.DataFrame(rows)
    print(df.round({"waste_percent": 2, "runtime_s": 5}))
    RESULTS_DIR.mkdir(exist_ok=True)
    df.to_csv(RESULTS_DIR / filename, index=False)


def main():
    # Pipeline check: answers are known, so check these first
    rows = []
    for problem_name, problem in hardcoded_problems().items():
        rows.extend(solve_all(problem, {"problem": problem_name}))
    save(rows, "hardcoded.csv")

    # The published results
    rows = []
    for size in SIZES:
        for seed in SEEDS:
            problem = random_problem(size, seed)
            rows.extend(solve_all(problem, {"size": size, "seed": seed}))
    save(rows, "results.csv")


if __name__ == "__main__":
    main()
