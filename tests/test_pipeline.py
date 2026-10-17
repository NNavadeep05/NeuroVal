"""
ValidationPipeline tests with a stub runner (no NEURON simulation).
"""

import numpy as np
import pytest

from neuroval.data import ExperimentalData
from neuroval.protocols import CurrentClamp
from neuroval.validation import ValidationPipeline
from neuroval.validation.comparison import MISSING_FEATURE_Z


class StubRunner:
    """Return a flat, spike-free trace instead of running NEURON."""

    cell = object()

    def run_simulation(self, delay, duration, amplitude, tstop, holding):
        time = np.arange(0.0, tstop, 0.025)
        voltage = np.full_like(time, -90.0)
        return time, voltage


@pytest.fixture
def pipeline(tmp_path):
    pipeline = ValidationPipeline(tmp_path)
    pipeline.runner = StubRunner()
    return pipeline


TARGETS = {
    "P": {
        "soma": {
            "Spikecount": [0.0, 0.5],
            "AP_amplitude": [70.0, 5.0],
        }
    }
}


def test_validate_names_features_like_bluepyopt(pipeline):
    """Combined keys are protocol.soma.feature, as BluePyOpt names objectives."""

    results = pipeline.validate(
        ExperimentalData(TARGETS),
        {"P": CurrentClamp(name="P")},
    )

    comparison = results["protocols"]["P"]["comparison"]

    assert comparison["Spikecount"]["z_score"] == 0.0
    assert comparison["AP_amplitude"]["status"] == "missing"
    assert results["summary"]["problem_features"] == ["P.soma.AP_amplitude"]
    assert results["summary"]["passed"] is False


def test_protocol_without_targets_raises(pipeline):
    with pytest.raises(ValueError):
        pipeline.validate(
            ExperimentalData(TARGETS),
            {"Q": CurrentClamp(name="Q")},
        )


def test_non_soma_targets_raise(pipeline):
    """Dendritic targets are refused instead of silently dropped."""

    targets = {
        "P": {
            "soma": {"Spikecount": [0.0, 0.5]},
            "dend1": {"Spikecount": [0.0, 0.5]},
        }
    }

    with pytest.raises(ValueError):
        pipeline.validate(
            ExperimentalData(targets),
            {"P": CurrentClamp(name="P")},
        )


class FailingRunner(StubRunner):
    """Fails like a CVode error on protocol F, works on the others."""

    def run_simulation(self, delay, duration, amplitude, tstop, holding):
        from neuroval.simulation import SimulationError

        if tstop == 900:
            raise SimulationError("variable step integrator error")

        return super().run_simulation(delay, duration, amplitude, tstop, holding)


def test_failed_simulation_scores_features_as_missing(tmp_path):
    """As BluePyOpt's SweepProtocol: a failed run gives no responses."""

    pipeline = ValidationPipeline(tmp_path)
    pipeline.runner = FailingRunner()

    targets = ExperimentalData({
        "P": {"soma": {"Spikecount": [0.0, 0.5]}},
        "F": {"soma": {"Spikecount": [0.0, 0.5], "voltage_base": [-90.0, 1.0]}},
    })
    protocols = {
        "P": CurrentClamp(name="P"),
        "F": CurrentClamp(tstop=900, name="F"),
    }

    results = pipeline.validate(targets, protocols)

    failed = results["protocols"]["F"]

    assert "integrator error" in failed["error"]
    assert len(failed["time"]) == 0
    assert all(v["simulated"] is None for v in failed["comparison"].values())
    assert all(v["z_score"] == MISSING_FEATURE_Z for v in failed["comparison"].values())
    assert {v["status"] for v in failed["comparison"].values()} == {"simulation_failed"}
    assert results["protocols"]["P"]["comparison"]["Spikecount"]["status"] == "ok"
    assert results["summary"]["problem_features"] == [
        "F.soma.Spikecount", "F.soma.voltage_base"
    ]
    assert results["summary"]["passed"] is False


def test_configuration_errors_are_not_masked(tmp_path):
    """Other errors (e.g. a failed check_simulator) still stop the run."""

    class BrokenRunner(StubRunner):
        def run_simulation(self, *args, **kwargs):
            raise RuntimeError("Parameter v_init has different value")

    pipeline = ValidationPipeline(tmp_path)
    pipeline.runner = BrokenRunner()

    with pytest.raises(RuntimeError, match="v_init"):
        pipeline.validate(ExperimentalData(TARGETS), {"P": CurrentClamp(name="P")})


def test_no_protocols_raises(pipeline):
    with pytest.raises(ValueError):
        pipeline.validate(ExperimentalData(TARGETS), {})
