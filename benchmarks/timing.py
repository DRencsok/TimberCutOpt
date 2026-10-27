import statistics
from collections.abc import Callable
from time import perf_counter

from cutopt.models import CutPattern, Piece, Problem, StockLength


def timer(solver: Callable, problem: Problem, repeats: int) -> tuple[float, list[CutPattern]]:
    """Time a solver on one problem and return its median runtime and plan.

    Args:
        solver: The solver function itself (e.g. greedycut or cp_sat
        problem: The problem to solve. The same one is used for every run.
        repeats: How many timed runs to do. Must be at least 1.

    Returns:
        The median runtime in seconds, and the plan from the last run.

    Raises:
        ValueError: If repeats is less than 1.
    """

    if repeats < 1:
        raise ValueError(f"The number of repeats must be at least 1, got {repeats}")

    # Warmup so everything is loaded (first runs are usually slower, so the comparision is fair)
    warmup_problem = Problem(
        stock=(StockLength("47x100", 2400),), kerf=3, pieces=(Piece("47x100", "stud", 1200, 2),)
    )
    solver(warmup_problem)

    times = []
    for _ in range(repeats):
        start = perf_counter()
        plan = solver(problem)
        end = perf_counter()
        times.append(end - start)

    return statistics.median(times), plan
