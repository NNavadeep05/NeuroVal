import json

import pytest

from neuroval.data.lab_files import find_recording, read_ljp


def test_read_ljp(tmp_path):
    (tmp_path / "160118_c7_D1-spec.json").write_text(
        json.dumps({"liquid_junction_potential": 11.5}), encoding="utf-8"
    )

    assert read_ljp(tmp_path) == 11.5


def test_read_ljp_needs_one_spec_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_ljp(tmp_path)


def test_find_recording(tmp_path):
    """Protocol IDthresh_587 maps to *_ch3_587.dat (lab select.ipynb)."""

    (tmp_path / "ECall_IDthresh_ch3_587.dat").write_text("", encoding="utf-8")
    (tmp_path / "ECall_IDthresh_ch2_587.dat").write_text("", encoding="utf-8")

    assert find_recording(tmp_path, "IDthresh_587").name == "ECall_IDthresh_ch3_587.dat"
    assert find_recording(tmp_path, "IDthresh_999") is None
