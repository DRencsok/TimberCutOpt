from pathlib import Path

import pytest
from typer.testing import CliRunner

from cutopt.cli import app
from cutopt.get_solver import SOLVERS

runner = CliRunner()

EXAMPLES = Path(__file__).parent.parent / "examples"

# Two 1200 mm pieces exactly fill a 2400 mm board, but only when the kerf is 0
TWO_HALVES = "label,length,quantity,section\nbeam,1200,2,47x100 C24\n"


def write_cut_list(tmp_path, text):
    """Write a cut list CSV into pytest's temporary folder and return its path as a string."""
    path = tmp_path / "cuts.csv"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_shed_example_with_greedy():
    shed = str(EXAMPLES / "shed.csv")
    result = runner.invoke(app, ["solve", shed, "--stock", "2400,3600,4800", "--solver", "greedy"])
    assert result.exit_code == 0, result.output


def test_default_solver_prints_all_tables(tmp_path):
    cut_list = write_cut_list(tmp_path, TWO_HALVES)
    result = runner.invoke(app, ["solve", cut_list])
    assert result.exit_code == 0, result.output
    for title in ("Cutting Plan", "Shopping List", "Summary"):
        assert title in result.output


@pytest.mark.parametrize("solver", SOLVERS)
def test_every_solver_runs(tmp_path, solver):
    cut_list = write_cut_list(tmp_path, TWO_HALVES)
    result = runner.invoke(app, ["solve", cut_list, "--stock", "2400", "--solver", solver])
    assert result.exit_code == 0, result.output
    assert "beam 1200" in result.output


def test_unknown_solver_exits_with_error(tmp_path):
    cut_list = write_cut_list(tmp_path, TWO_HALVES)
    result = runner.invoke(app, ["solve", cut_list, "--solver", "nonsense"])
    assert result.exit_code == 1
    # A crash also exits with 1, so check it was our handler that stopped the program
    assert isinstance(result.exception, SystemExit)
    assert "nonsense" in result.output
    for name in SOLVERS:
        assert name in result.output


def test_missing_cut_list_is_usage_error(tmp_path):
    result = runner.invoke(app, ["solve", str(tmp_path / "missing.csv")])
    assert result.exit_code == 2


def test_zero_kerf_fits_both_pieces_on_one_board(tmp_path):
    cut_list = write_cut_list(tmp_path, TWO_HALVES)
    result = runner.invoke(app, ["solve", cut_list, "--stock", "2400", "--kerf", "0"])
    assert result.exit_code == 0, result.output
    assert "beam 1200 x2" in result.output
    assert "0.00" in result.output


def test_kerf_forces_a_second_board(tmp_path):
    cut_list = write_cut_list(tmp_path, TWO_HALVES)
    result = runner.invoke(app, ["solve", cut_list, "--stock", "2400", "--kerf", "3"])
    assert result.exit_code == 0, result.output
    assert "x2" not in result.output
    assert "50.00" in result.output
