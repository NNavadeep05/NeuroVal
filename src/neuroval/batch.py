"""
Helpers for validating several Hall of Fame cells of one model.

The lab's variate.py runs every parameter set in hall_of_fame.json. With
exported hoc files each Cell_<n>.hoc must run in its own Python process,
because NeuroVal allows one hoc model per process (NEURON templates are
global). These helpers list the exported cells and collect the results
that examples/validate_all_cells.py writes per cell.
"""

import json
import re
from pathlib import Path


def available_cells(model_path: str | Path) -> list[int]:
    """Return the indices of the exported Cell_<n>.hoc files."""

    checkpoints = Path(model_path) / "checkpoints"

    if not checkpoints.exists():
        raise FileNotFoundError(f"No checkpoints folder in {model_path}")

    indices = []

    for path in checkpoints.glob("Cell_*.hoc"):
        match = re.fullmatch(r"Cell_(\d+)\.hoc", path.name)

        if match:
            indices.append(int(match.group(1)))

    return sorted(indices)


def summarise_cells(output_dir: str | Path, cells: list[int]) -> dict:
    """Collect the summary of each cell from <output_dir>/Cell_<n>/scores.json.

    A cell without a scores.json (for example a failed run) is reported
    with an error entry instead of being left out.
    """

    summary = {}

    for cell in cells:
        scores_file = Path(output_dir) / f"Cell_{cell}" / "scores.json"

        if not scores_file.exists():
            summary[f"Cell_{cell}"] = {"error": "no scores.json"}
            continue

        scores = json.loads(scores_file.read_text(encoding="utf-8"))
        summary[f"Cell_{cell}"] = scores["summary"]

    return summary
