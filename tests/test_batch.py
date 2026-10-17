import json

import pytest

from neuroval.batch import available_cells, summarise_cells


def test_available_cells(tmp_path):
    """Cells are the exported Cell_<n>.hoc files, in numeric order."""

    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()

    for name in ("Cell_9.hoc", "Cell_0.hoc", "Cell_10.hoc", "Cell_5.hoc", "notes.txt"):
        (checkpoints / name).write_text("", encoding="utf-8")

    assert available_cells(tmp_path) == [0, 5, 9, 10]


def test_available_cells_needs_checkpoints(tmp_path):
    with pytest.raises(FileNotFoundError):
        available_cells(tmp_path)


def _write_scores(folder, mean_abs_z, max_z, passed, problems):
    folder.mkdir(parents=True)
    (folder / "scores.json").write_text(json.dumps({
        "metadata": {},
        "summary": {
            "mean_abs_z": mean_abs_z,
            "max_z": max_z,
            "passed": passed,
            "problem_features": problems,
        },
        "features": {},
    }), encoding="utf-8")


def test_summarise_cells(tmp_path):
    _write_scores(tmp_path / "Cell_0", 4.16, 30.42, False, [])
    _write_scores(tmp_path / "Cell_5", 2.0, 2.9, True, [])

    summary = summarise_cells(tmp_path, [0, 5])

    assert summary["Cell_0"] == {
        "mean_abs_z": 4.16, "max_z": 30.42, "passed": False, "problem_features": [],
    }
    assert summary["Cell_5"]["passed"] is True


def test_missing_cell_result_is_reported(tmp_path):
    """A cell whose run produced no scores.json is reported, not skipped."""

    _write_scores(tmp_path / "Cell_0", 4.16, 30.42, False, [])

    summary = summarise_cells(tmp_path, [0, 6])

    assert summary["Cell_6"] == {"error": "no scores.json"}
