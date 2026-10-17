import json

import numpy as np
import pytest

from neuroval.report import save_results
from neuroval.validation import FeatureComparator


def _results():
    """A validate()-style result with one ok, one missing and one zero-std feature."""

    comparator = FeatureComparator()
    time = np.linspace(0.0, 100.0, 11)

    comparison_a = comparator.compare(
        {"voltage_base": [-90.0, 1.0], "AP_amplitude": [70.0, 5.0]},
        {"voltage_base": -88.0, "AP_amplitude": None},
    )
    comparison_b = comparator.compare(
        {"Spikecount": [0.0, 0.0]},
        {"Spikecount": 1.0},
    )

    combined = {f"A<1>.soma.{k}": v for k, v in comparison_a.items()}
    combined.update({f"B.soma.{k}": v for k, v in comparison_b.items()})

    return {
        "protocols": {
            "A<1>": {
                "protocol": "A<1>",
                "time": time,
                "voltage": np.full_like(time, -90.0),
                "features": {"voltage_base": -88.0, "AP_amplitude": None},
                "comparison": comparison_a,
            },
            "B": {
                "protocol": "B",
                "time": time,
                "voltage": np.full_like(time, -80.0),
                "features": {"Spikecount": 1.0},
                "comparison": comparison_b,
            },
        },
        "summary": comparator.summarise(combined),
    }


def _strict_json(path):
    """Load JSON and fail on NaN or Infinity, which are not valid JSON."""

    def reject(constant):
        raise ValueError(f"non-standard JSON constant {constant}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def test_writes_all_outputs(tmp_path):
    paths = save_results(_results(), tmp_path, metadata={"cell_index": 0})

    for name in ("scores", "model_features", "experimental_features",
                 "traces_plot", "z_scores_plot", "report"):
        assert paths[name].exists()
        assert paths[name].stat().st_size > 0

    assert (tmp_path / "traces" / "B.csv").exists()


def test_scores_json_is_strict_and_complete(tmp_path):
    save_results(_results(), tmp_path, metadata={"cell_index": 0})

    scores = _strict_json(tmp_path / "scores.json")

    assert scores["metadata"] == {"cell_index": 0}
    assert scores["summary"]["passed"] is False
    assert scores["summary"]["problem_features"] == [
        "A<1>.soma.AP_amplitude", "B.soma.Spikecount"
    ]

    features = scores["features"]
    assert features["A<1>.soma.voltage_base"]["z_score"] == 2.0
    assert features["A<1>.soma.AP_amplitude"]["status"] == "missing"
    assert features["B.soma.Spikecount"]["z_score"] is None
    assert features["B.soma.Spikecount"]["status"] == "zero_std"


def test_feature_and_target_files(tmp_path):
    save_results(_results(), tmp_path)

    model = _strict_json(tmp_path / "model_features.json")
    targets = _strict_json(tmp_path / "experimental_features.json")

    assert model["A<1>"] == {"voltage_base": -88.0, "AP_amplitude": None}
    assert targets["B"] == {"soma": {"Spikecount": [0.0, 0.0]}}


def test_trace_csv_round_trip(tmp_path):
    save_results(_results(), tmp_path)

    data = np.loadtxt(tmp_path / "traces" / "B.csv", delimiter=",", skiprows=1)

    assert data.shape == (11, 2)
    assert np.allclose(data[:, 1], -80.0)


def test_html_is_escaped(tmp_path):
    """Protocol names are escaped in the HTML report."""

    save_results(_results(), tmp_path)

    html = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert "A&lt;1&gt;" in html
    assert "A<1>" not in html
    assert "plots/z_scores.png" in html


def test_simulation_error_is_reported(tmp_path):
    """A protocol whose simulation failed shows its error in JSON and HTML."""

    results = _results()
    results["protocols"]["B"]["error"] = "CVode <error>"
    results["protocols"]["B"]["time"] = np.array([])
    results["protocols"]["B"]["voltage"] = np.array([])

    save_results(results, tmp_path)

    scores = _strict_json(tmp_path / "scores.json")
    html = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert scores["errors"] == {"B": "CVode <error>"}
    assert "Simulation failed: CVode &lt;error&gt;" in html


def test_experimental_overlay(tmp_path):
    """Recorded traces are drawn: the plot differs from one without them."""

    time = np.linspace(0.0, 100.0, 11)
    with_overlay = save_results(
        _results(),
        tmp_path / "with",
        experimental_traces={"B": (time, np.full_like(time, -82.0))},
    )
    without = save_results(_results(), tmp_path / "without")

    assert (
        with_overlay["traces_plot"].read_bytes() != without["traces_plot"].read_bytes()
    )


def test_colliding_trace_names_rejected(tmp_path):
    """Two protocols must not overwrite each other's trace file."""

    results = _results()
    results["protocols"]["A_1_"] = results["protocols"]["A<1>"]

    with pytest.raises(ValueError):
        save_results(results, tmp_path)


def test_unserialisable_metadata_leaves_no_partial_file(tmp_path):
    with pytest.raises(TypeError):
        save_results(_results(), tmp_path, metadata={"path": tmp_path})

    assert not (tmp_path / "scores.json").exists()
