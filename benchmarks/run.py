from pathlib import Path

import pandas as pd
from problems import hardcoded_problems
from timing import timer

from cutopt.get_solver import SOLVERS
from cutopt.metrics import Metrics


def main():
    problems = hardcoded_problems()

    rows = []
    for problem_name, problem in problems.items():
        for solver_name, solver in SOLVERS.items():
            runtime_s, plan = timer(solver, problem, 5)
            metrics = Metrics.from_boards(plan)
            rows.append(
                {
                    "problem": problem_name,
                    "solver": solver_name,
                    "boards": metrics.board_count,
                    "stock_total": metrics.stock_length_total,
                    "waste_percent": metrics.waste_percent,
                    "runtime_s": runtime_s,
                }
            )

    df = pd.DataFrame(rows)
    print(df.round({"waste_percent": 2, "runtime_s": 5}))

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    df.to_csv(results_dir / "results.csv", index=False)


if __name__ == "__main__":
    main()
