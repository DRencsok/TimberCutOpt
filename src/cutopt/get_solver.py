"""Look up a solver by name, shared by the CLI and the API."""

from .cp_sat import cp_sat
from .errors import UnknownSolverError
from .greedy import greedycut

SOLVERS = {"cp_sat": cp_sat, "greedy": greedycut}


def get_solver(name: str):
    """Return the solver function registered under a name.

    Args:
        name: The solver's name, a key of SOLVERS (e.g. "greedy" or "cp_sat").

    Returns:
        The solver function itself, not yet called.

    Raises:
        UnknownSolverError: If no solver has that name. The message lists
            the valid names.
    """
    try:
        solver = SOLVERS[name]
    except KeyError:
        names = ", ".join(SOLVERS)
        raise UnknownSolverError(f"Solver named {name} is not valid, try {names}") from None
    return solver
