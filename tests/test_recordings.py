import numpy as np
import pytest

from neuroval.data import load_trace


DAT_TEXT = """#
# VERSION#2
# DATE#18/01/2016 (2)
0\t-80.0
0.1\t-80.5
0.2\t-81.0
"""


def test_load_lab_dat_file(tmp_path):
    """Two tab-separated columns with '#' header lines, as in the lab's expdata/."""

    file_path = tmp_path / "ECall_IV_ch3_546.dat"
    file_path.write_text(DAT_TEXT, encoding="utf-8")

    time, voltage = load_trace(file_path)

    assert np.allclose(time, [0.0, 0.1, 0.2])
    assert np.allclose(voltage, [-80.0, -80.5, -81.0])


def test_junction_potential_is_subtracted(tmp_path):
    """ljp is given as a positive number and subtracted (BluePyEfe, lab utils.py)."""

    file_path = tmp_path / "trace.dat"
    file_path.write_text(DAT_TEXT, encoding="utf-8")

    _, voltage = load_trace(file_path, ljp=11.5)

    assert np.allclose(voltage, [-91.5, -92.0, -92.5])


def test_load_csv(tmp_path):
    """Comma-separated files load with delimiter=','."""

    file_path = tmp_path / "trace.csv"
    file_path.write_text("# time,voltage\n0,-80\n0.1,-81\n", encoding="utf-8")

    time, voltage = load_trace(file_path, delimiter=",")

    assert np.allclose(time, [0.0, 0.1])
    assert np.allclose(voltage, [-80.0, -81.0])


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_trace(tmp_path / "missing.dat")


@pytest.mark.parametrize(
    "text",
    [
        "0\n0.1\n",                  # one column
        "0\t-80\n",                  # one sample
        "0\t-80\n0\t-81\n",          # time not increasing
        "0\t-80\n0.1\tnan\n",        # non-finite voltage
    ],
)
def test_invalid_trace_rejected(tmp_path, text):
    file_path = tmp_path / "bad.dat"
    file_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError):
        load_trace(file_path)
