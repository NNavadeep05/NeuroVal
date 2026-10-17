"""
Save validation results: JSON files, trace CSVs, plots and an HTML report.

The outputs follow HippoUnit's (feature values, feature errors and final
scores as JSON, validation plots, simulation traces), with the file names
of the NeuroVal design: scores.json, model_features.json and
experimental_features.json.
"""

import json
import math
import re
from pathlib import Path

import numpy as np

from neuroval.report.html import write_html
from neuroval.report.plots import plot_traces, plot_z_scores


def save_results(
    results: dict,
    output_dir: str | Path,
    metadata: dict | None = None,
    experimental_traces: dict | None = None,
) -> dict[str, Path]:
    """Write all outputs of a ValidationPipeline.validate() result.

    experimental_traces optionally maps protocol names to recorded
    (time, voltage), drawn under the simulated traces. Returns the paths
    of the written files. Non-finite numbers are written as null so the
    JSON files stay valid.
    """

    file_names = [_safe_name(name) for name in results["protocols"]]

    if len(set(file_names)) != len(file_names):
        raise ValueError("Protocol names map to the same trace file name.")

    output_dir = Path(output_dir)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)
    (output_dir / "traces").mkdir(exist_ok=True)

    protocols = results["protocols"]
    features = {
        f"{name}.soma.{feature}": values
        for name, result in protocols.items()
        for feature, values in result["comparison"].items()
    }

    paths = {
        "scores": output_dir / "scores.json",
        "model_features": output_dir / "model_features.json",
        "experimental_features": output_dir / "experimental_features.json",
        "traces_plot": output_dir / "plots" / "traces.png",
        "z_scores_plot": output_dir / "plots" / "z_scores.png",
        "report": output_dir / "report.html",
    }

    _write_json(paths["scores"], {
        "metadata": metadata or {},
        "summary": results["summary"],
        "errors": {
            name: result["error"]
            for name, result in protocols.items()
            if "error" in result
        },
        "features": features,
    })

    _write_json(paths["model_features"], {
        name: result["features"] for name, result in protocols.items()
    })

    _write_json(paths["experimental_features"], {
        name: {
            "soma": {
                feature: [values["experimental_mean"], values["experimental_std"]]
                for feature, values in result["comparison"].items()
            }
        }
        for name, result in protocols.items()
    })

    for name, result in protocols.items():
        np.savetxt(
            output_dir / "traces" / f"{_safe_name(name)}.csv",
            np.column_stack([result["time"], result["voltage"]]),
            delimiter=",",
            header="time_ms,voltage_mV",
            comments="",
        )

    plot_traces(protocols, paths["traces_plot"], experimental_traces)
    plot_z_scores(features, paths["z_scores_plot"])
    write_html(paths["report"], protocols, results["summary"], metadata or {})

    return paths


def _write_json(file_path: Path, data) -> None:
    """Write JSON with non-finite numbers replaced by null."""

    text = json.dumps(_clean(data), indent=4, allow_nan=False)
    file_path.write_text(text, encoding="utf-8")


def _clean(value):
    """Convert numpy numbers to Python numbers and NaN/inf to None."""

    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]

    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if isinstance(value, (int, np.integer)):
        return int(value)

    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None

    return value


def _safe_name(name: str) -> str:
    """Make a protocol name safe to use as a file name."""

    return re.sub(r"[^A-Za-z0-9._-]", "_", name)
