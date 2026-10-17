import numpy as np

from neuroval.features import FeatureExtractor


def _flat_trace():
    """Return a 1000 ms trace with a small, spike-free step response."""

    time = np.arange(0.0, 1000.0, 0.025)
    voltage = np.full_like(time, -90.0)
    voltage[(time >= 200.0) & (time < 700.0)] = -80.0
    return time, voltage


def test_no_spikes_does_not_crash():
    """Spike features are None when there are no spikes (BasalUnit convention)."""

    time, voltage = _flat_trace()

    features = FeatureExtractor().extract(
        time,
        voltage,
        stimulus_start=200.0,
        stimulus_end=700.0,
        feature_names=["Spikecount", "voltage_base", "AP_amplitude"],
    )

    assert features["Spikecount"] == 0.0
    assert abs(features["voltage_base"] + 90.0) < 0.1
    assert features["AP_amplitude"] is None


def test_raw_efel_names_are_kept():
    """Features are returned under their eFEL names, not renamed."""

    time, voltage = _flat_trace()

    features = FeatureExtractor().extract(
        time,
        voltage,
        stimulus_start=200.0,
        stimulus_end=700.0,
        feature_names=["voltage_base"],
    )

    assert list(features) == ["voltage_base"]


def test_threshold_setting_is_restored():
    """eFEL settings are global; extract() leaves them as it found them."""

    import efel

    time, voltage = _flat_trace()
    before = efel.get_settings().Threshold

    FeatureExtractor().extract(
        time,
        voltage,
        stimulus_start=200.0,
        stimulus_end=700.0,
        feature_names=["Spikecount"],
        threshold=0.0,
    )

    assert efel.get_settings().Threshold == before


def test_summarise_ignores_nan_values():
    """NaN entries are dropped before averaging; all-NaN gives None."""

    assert FeatureExtractor._summarise(np.array([1.0, np.nan, 3.0])) == 2.0
    assert FeatureExtractor._summarise(np.array([np.nan, np.nan])) is None


def test_threshold_restored_when_efel_raises():
    """The previous eFEL threshold is restored even if extraction fails."""

    import efel
    import pytest

    time, voltage = _flat_trace()
    before = efel.get_settings().Threshold

    with pytest.raises(Exception):
        FeatureExtractor().extract(
            time,
            voltage,
            stimulus_start=200.0,
            stimulus_end=700.0,
            feature_names=["not_an_efel_feature"],
            threshold=0.0,
        )

    assert efel.get_settings().Threshold == before
