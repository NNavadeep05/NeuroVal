import json

import pytest

from neuroval.data import ExperimentalData


TARGETS = {
    "IV_546": {
        "soma": {
            "Spikecount": [0.0, 0.001],
            "voltage_base": [-90.5752, 0.0976],
        }
    },
    "IDthresh_587": {
        "soma": {
            "mean_frequency": [4.0615, 0.4062],
        }
    },
}


def test_create_experimental_data():
    """ExperimentalData should store BluePyOpt-style targets."""

    experimental = ExperimentalData(TARGETS)

    assert experimental.protocols() == ["IV_546", "IDthresh_587"]
    assert experimental.features("IV_546") == {
        "Spikecount": [0.0, 0.001],
        "voltage_base": [-90.5752, 0.0976],
    }


def test_from_json(tmp_path):
    """Targets load from a features.json file."""

    file_path = tmp_path / "features.json"
    file_path.write_text(json.dumps(TARGETS), encoding="utf-8")

    experimental = ExperimentalData.from_json(file_path)

    assert experimental.features("IDthresh_587") == {
        "mean_frequency": [4.0615, 0.4062],
    }


def test_empty_dictionary():
    """ExperimentalData should reject an empty target dictionary."""

    with pytest.raises(ValueError):
        ExperimentalData({})


def test_target_must_be_mean_and_std():
    """Each feature needs [mean, std], as in BluePyEfe output."""

    with pytest.raises(ValueError):
        ExperimentalData({"IV": {"soma": {"voltage_base": -90.0}}})


def test_negative_std_rejected():
    """A standard deviation cannot be negative."""

    with pytest.raises(ValueError):
        ExperimentalData({"IV": {"soma": {"voltage_base": [-90.0, -1.0]}}})


def test_unknown_protocol():
    """Asking for a protocol without targets raises a clear error."""

    experimental = ExperimentalData(TARGETS)

    with pytest.raises(KeyError):
        experimental.features("IDthresh_999")


@pytest.mark.parametrize(
    "target",
    [
        [float("nan"), 1.0],
        [-90.0, float("nan")],
        [float("inf"), 1.0],
        [-90.0, float("inf")],
    ],
)
def test_non_finite_target_rejected(target):
    """NaN or infinite means and stds cannot be scored, so they are rejected."""

    with pytest.raises(ValueError):
        ExperimentalData({"IV": {"soma": {"voltage_base": target}}})
