"""
Integration tests against a real BluePyOpt model.

Needs NEURON, compiled mechanisms and a model folder. Set the
NEUROVAL_MODEL_PATH environment variable to the model folder, e.g.
.../humanspn/models/optimisations/hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15
and optionally NEUROVAL_CELL_INDEX (default 0).
"""

import json
import math
import os
from pathlib import Path

import pytest

MODEL_PATH = os.environ.get("NEUROVAL_MODEL_PATH")
CELL_INDEX = int(os.environ.get("NEUROVAL_CELL_INDEX", "0"))

pytestmark = pytest.mark.skipif(
    not MODEL_PATH,
    reason="Set NEUROVAL_MODEL_PATH to run integration tests.",
)


def _expected_globals():
    """Read celsius and v_init straight from the model's parameters.json."""

    params_file = Path(MODEL_PATH) / "config" / "parameters.json"
    parameters = json.loads(params_file.read_text(encoding="utf-8"))

    return {
        parameter["param_name"]: parameter["value"]
        for parameter in parameters
        if parameter.get("type") == "global"
    }


@pytest.fixture(scope="module")
def loaded():
    """Load the model once and record the working directory around it."""

    from neuroval.validation import ValidationPipeline

    pipeline = ValidationPipeline(MODEL_PATH, cell_index=CELL_INDEX)

    cwd_before = os.getcwd()
    pipeline.runner.load_model()
    cwd_after = os.getcwd()

    return pipeline, cwd_before, cwd_after


def test_working_directory_restored(loaded):
    _, cwd_before, cwd_after = loaded

    assert cwd_after == cwd_before


def test_template_matches_cell_index(loaded):
    """The instantiated hoc template is the one selected by cell_index."""

    pipeline, _, _ = loaded

    assert pipeline.runner.hoc_file.name == f"Cell_{CELL_INDEX}.hoc"
    assert pipeline.runner.cell.hname().startswith(f"Cell_{CELL_INDEX}[")


def test_simulation_settings_applied(loaded):
    """The run uses celsius and v_init from parameters.json."""

    from neuron import h

    from neuroval.protocols import CurrentClamp

    pipeline, _, _ = loaded
    expected = _expected_globals()

    results = pipeline.run(protocol=CurrentClamp(amplitude=0.0))

    assert h.celsius == pytest.approx(expected["celsius"])
    assert results["voltage"][0] == pytest.approx(expected["v_init"])


def test_cvode_is_default(loaded):
    """Runs use CVode with minstep 1e-3, as in the lab's optimize.py."""

    from neuron import h

    from neuroval.protocols import CurrentClamp

    pipeline, _, _ = loaded
    minstep_before = h.CVode().minstep()

    pipeline.run(protocol=CurrentClamp(amplitude=0.0))

    assert h.cvode_active() == 1.0
    assert h.CVode().minstep() == minstep_before


def test_fixed_step_option(loaded):
    """cvode_active=False switches to the fixed 0.025 ms step."""

    from neuron import h

    from neuroval.protocols import CurrentClamp

    pipeline, _, _ = loaded
    pipeline.runner.cvode_active = False

    try:
        results = pipeline.run(protocol=CurrentClamp(amplitude=0.0))
    finally:
        pipeline.runner.cvode_active = True

    assert h.cvode_active() == 0.0
    assert h.dt == pytest.approx(0.025)
    assert len(results["time"]) == int(round(700 / 0.025)) + 1


def test_holding_current_changes_trace(loaded):
    """The whole-sweep holding current is injected."""

    from neuroval.protocols import CurrentClamp

    pipeline, _, _ = loaded

    without = pipeline.run(protocol=CurrentClamp(amplitude=0.0))
    with_holding = pipeline.run(protocol=CurrentClamp(amplitude=0.0, holding=0.05))

    assert with_holding["voltage"][-1] > without["voltage"][-1]


def test_no_spike_protocol(loaded):
    """A subthreshold run returns None for spike features instead of crashing."""

    from neuroval.protocols import CurrentClamp

    pipeline, _, _ = loaded

    results = pipeline.run(protocol=CurrentClamp(amplitude=0.0))

    assert results["features"]["Spikecount"] == 0.0
    assert results["features"]["AP_amplitude"] is None


def test_validation_against_model_targets(loaded):
    """Validate against the model's own features.json and protocols.json."""

    from neuroval.data import ExperimentalData
    from neuroval.protocols import load_bluepyopt_protocols
    from neuroval.validation.comparison import PASS_THRESHOLD

    pipeline, _, _ = loaded

    config = Path(MODEL_PATH) / "config"
    experimental = ExperimentalData.from_json(config / "features.json")
    protocols = load_bluepyopt_protocols(config / "protocols.json")

    raw_protocols = json.loads(
        (config / "protocols.json").read_text(encoding="utf-8")
    )

    for name, protocol in protocols.items():
        assert protocol.holding == raw_protocols[name]["stimuli"][1]["amp"]

    results = pipeline.validate(experimental, protocols)

    summary = results["summary"]
    n_targets = sum(
        len(experimental.features(name)) for name in experimental.protocols()
    )
    n_scored = sum(
        len(protocol["comparison"]) for protocol in results["protocols"].values()
    )

    assert set(results["protocols"]) == set(experimental.protocols())
    assert n_scored == n_targets
    assert summary["problem_features"] == []
    assert math.isfinite(summary["mean_abs_z"])
    assert math.isfinite(summary["max_z"])
    assert summary["passed"] == (summary["max_z"] < PASS_THRESHOLD)

    for protocol in results["protocols"].values():
        assert set(protocol["comparison"]) == set(
            experimental.features(protocol["protocol"])
        )

        for values in protocol["comparison"].values():
            assert values["status"] == "ok"
            assert math.isfinite(values["simulated"])
            assert math.isfinite(values["z_score"])
