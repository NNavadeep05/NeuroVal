"""
Integration test: validate every exported Hall of Fame cell.

Runs examples/validate_all_cells.py, which starts one Python process per
cell. Needs NEURON and a model folder in NEUROVAL_MODEL_PATH.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

MODEL_PATH = os.environ.get("NEUROVAL_MODEL_PATH")

pytestmark = pytest.mark.skipif(
    not MODEL_PATH,
    reason="Set NEUROVAL_MODEL_PATH to run integration tests.",
)

SCRIPT = Path(__file__).resolve().parents[1] / "examples" / "validate_all_cells.py"


def test_all_exported_cells_validated(tmp_path):
    from neuroval.batch import available_cells

    cells = available_cells(MODEL_PATH)

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), MODEL_PATH,
         "--output", str(tmp_path), "--jobs", str(len(cells))],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))

    assert list(summary) == [f"Cell_{cell}" for cell in cells]

    for cell in cells:
        cell_summary = summary[f"Cell_{cell}"]
        scores = json.loads(
            (tmp_path / f"Cell_{cell}" / "scores.json").read_text(encoding="utf-8")
        )

        assert "error" not in cell_summary
        assert scores["metadata"]["cell"] == f"Cell_{cell}"
        assert cell_summary["problem_features"] == []
        max_z = cell_summary["max_z"]
        assert cell_summary["passed"] == (max_z is not None and max_z < 3.0)
