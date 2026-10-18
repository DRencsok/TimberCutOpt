from pathlib import Path

import pytest

from cutopt.errors import CutOptError
from cutopt.io import read_cut_list
from cutopt.models import Piece

EXAMPLES = Path(__file__).parent.parent / "examples"


def write_csv(tmp_path, text):
    path = tmp_path / "cut.csv"
    path.write_text(text, encoding="utf-8-sig")
    pieces = read_cut_list(path)
    return pieces


def test_read_cut_list(tmp_path):
    pieces = write_csv(
        tmp_path,
        "label,length,quantity,section\nstud,1950,2,47x100 C24\n",
    )
    assert pieces == (Piece(section="47x100 C24", label="stud", length=1950, quantity=2),)


def test_read_cut_list_multiple(tmp_path):
    pieces = write_csv(
        tmp_path,
        "label,length,quantity,section\nrafter,2400,1,47x100 C24\nstud,1780,1,47x150 C18",
    )
    assert pieces == (
        Piece(section="47x100 C24", label="rafter", length=2400, quantity=1),
        Piece(section="47x150 C18", label="stud", length=1780, quantity=1),
    )


def test_extra_headers(tmp_path):
    pieces = write_csv(
        tmp_path,
        "label,length,quantity,section,notes\nstud,1746,3,47x150 C18,Color-dark\n",
    )
    assert pieces == (Piece(section="47x150 C18", label="stud", length=1746, quantity=3),)


def test_missing_column(tmp_path):
    with pytest.raises(CutOptError, match="missing columns"):
        write_csv(tmp_path, "label,quantiy,section\nstud,1,47x100\n")


def test_wrong_values(tmp_path):
    with pytest.raises(CutOptError, match="row 2"):
        write_csv(
            tmp_path,
            "label,length,quantity,section\nstud,1950,1,47x150 C24\nstud,abc,1,47x100 C18\n ",
        )


def test_empty_file(tmp_path):
    with pytest.raises(CutOptError, match="missing columns"):
        write_csv(tmp_path, "")


def test_spacing(tmp_path):
    pieces = write_csv(
        tmp_path,
        "  label,length , quantity, section, \nstud  ,1746,3 ,  47x150 C18\n",
    )
    assert pieces == (Piece(section="47x150 C18", label="stud", length=1746, quantity=3),)


def test_headers_only(tmp_path):
    pieces = write_csv(
        tmp_path,
        "label,length,quantity,section\n",
    )
    assert pieces == ()


def test_shed_example_is_readable():
    pieces = read_cut_list(EXAMPLES / "shed.csv")

    assert pieces == (
        Piece(label="wall stud", length=1950, quantity=16, section="47x100 C24"),
        Piece(label="nogging", length=550, quantity=12, section="47x100 C24"),
        Piece(label="rafter", length=2150, quantity=7, section="47x150 C24"),
    )
