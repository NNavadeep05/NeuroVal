import math

import pytest

from neuroval.validation import FeatureComparator
from neuroval.validation.comparison import MISSING_FEATURE_Z


def test_z_score():
    """z = |simulated - mean| / std, as in HippoUnit, BasalUnit and validate.py."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {"voltage_base": [-90.0, 2.0]},
        {"voltage_base": -87.0},
    )

    result = comparison["voltage_base"]

    assert result["experimental_mean"] == -90.0
    assert result["experimental_std"] == 2.0
    assert result["simulated"] == -87.0
    assert result["z_score"] == 1.5
    assert result["status"] == "ok"


def test_missing_feature_is_reported_not_skipped():
    """A feature the model could not produce gets the validate.py penalty."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {
            "AP_amplitude": [70.0, 5.0],
            "voltage_base": [-90.0, 2.0],
        },
        {
            "AP_amplitude": None,
        },
    )

    assert set(comparison) == {"AP_amplitude", "voltage_base"}

    for feature in comparison.values():
        assert feature["status"] == "missing"
        assert feature["z_score"] == MISSING_FEATURE_Z


def test_zero_std_gives_infinite_z():
    """Zero experimental std is flagged like HippoUnit and BasalUnit do."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {"Spikecount": [0.0, 0.0]},
        {"Spikecount": 1.0},
    )

    assert math.isinf(comparison["Spikecount"]["z_score"])
    assert comparison["Spikecount"]["status"] == "zero_std"


def test_summary_uses_max_z_for_pass():
    """Pass/fail follows validate.py: max z must be below 3.0."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {
            "a": [0.0, 1.0],
            "b": [0.0, 1.0],
        },
        {
            "a": 1.0,
            "b": 2.0,
        },
    )

    summary = comparator.summarise(comparison)

    assert summary["mean_abs_z"] == 1.5
    assert summary["max_z"] == 2.0
    assert summary["passed"] is True
    assert summary["problem_features"] == []


def test_summary_fails_with_problem_feature():
    """Problem features are listed and push max z over the threshold."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {
            "a": [0.0, 1.0],
            "b": [0.0, 1.0],
        },
        {
            "a": 1.0,
            "b": None,
        },
    )

    summary = comparator.summarise(comparison)

    assert summary["mean_abs_z"] == 1.0
    assert summary["max_z"] == MISSING_FEATURE_Z
    assert summary["passed"] is False
    assert summary["problem_features"] == ["b"]


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf")])
def test_non_finite_simulated_value_is_missing(bad_value):
    """NaN or inf from a failed simulation counts as missing, not as a pass."""

    comparator = FeatureComparator()

    comparison = comparator.compare(
        {
            "a": [0.0, 1.0],
            "b": [0.0, 1.0],
        },
        {
            "a": 1.0,
            "b": bad_value,
        },
    )

    summary = comparator.summarise(comparison)

    assert comparison["b"]["status"] == "missing"
    assert summary["passed"] is False
    assert summary["problem_features"] == ["b"]


def test_empty_comparison_does_not_pass():
    """No scored features is not a pass."""

    summary = FeatureComparator().summarise({})

    assert summary["passed"] is False
    assert math.isnan(summary["max_z"])
