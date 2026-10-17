import json

import numpy as np
import pytest

from neuroval.data import ExperimentalData
from neuroval.data.statistics import DEFAULT_STD_VALUE, build_targets
from neuroval.protocols import CurrentClamp


def _trace(base):
    """Spike-free 1000 ms trace with a given baseline (mV)."""

    time = np.arange(0.0, 1000.0, 0.1)
    voltage = np.full_like(time, base)
    voltage[(time >= 200.0) & (time < 700.0)] = base + 10.0
    return time, voltage


PROTOCOLS = {"P": CurrentClamp(delay=200, duration=500, tstop=1000, name="P")}


def test_mean_std_n_across_recordings():
    """mean = nanmean, std = nanstd, n = values, as BluePyEfe's Target."""

    targets, sizes = build_targets(
        {"P": [_trace(-90.0), _trace(-80.0)]},
        PROTOCOLS,
        ["voltage_base"],
    )

    mean, std = targets.features("P")["voltage_base"]

    assert mean == pytest.approx(-85.0, abs=0.1)
    assert std == pytest.approx(5.0, abs=0.1)
    assert sizes["P"]["voltage_base"] == 2


def test_zero_std_replaced_by_default():
    """A single recording gives std 0, replaced by 1e-3 (BluePyEfe default)."""

    targets, sizes = build_targets(
        {"P": [_trace(-90.0)]},
        PROTOCOLS,
        ["voltage_base"],
    )

    assert targets.features("P")["voltage_base"][1] == DEFAULT_STD_VALUE
    assert sizes["P"]["voltage_base"] == 1


def test_feature_without_values_is_not_saved():
    """Features with fewer values than threshold_nvalue_save are dropped."""

    targets, sizes = build_targets(
        {"P": [_trace(-90.0)]},
        PROTOCOLS,
        ["voltage_base", "AP_amplitude"],
    )

    assert set(targets.features("P")) == {"voltage_base"}
    assert "AP_amplitude" not in sizes["P"]


def test_per_protocol_feature_lists():
    targets, _ = build_targets(
        {"P": [_trace(-90.0)]},
        PROTOCOLS,
        {"P": ["Spikecount"]},
    )

    assert set(targets.features("P")) == {"Spikecount"}


def test_unknown_protocol_raises():
    with pytest.raises(KeyError):
        build_targets({"Q": [_trace(-90.0)]}, PROTOCOLS, ["voltage_base"])


def test_no_values_at_all_raises():
    with pytest.raises(ValueError):
        build_targets({"P": [_trace(-90.0)]}, PROTOCOLS, ["AP_amplitude"])


def test_targets_round_trip_through_json(tmp_path):
    """Built targets save in the features.json format and load back."""

    targets, _ = build_targets(
        {"P": [_trace(-90.0), _trace(-80.0)]},
        PROTOCOLS,
        ["voltage_base"],
    )

    file_path = tmp_path / "features.json"
    targets.to_json(file_path)

    loaded = ExperimentalData.from_json(file_path)

    assert loaded.targets == json.loads(file_path.read_text(encoding="utf-8"))
    assert loaded.features("P") == targets.features("P")
