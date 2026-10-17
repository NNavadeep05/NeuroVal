"""
Integration test: rebuild the lab's targets from its raw recordings.

Needs a model folder with expdata/ (no NEURON). Set NEUROVAL_MODEL_PATH.
"""

import os
from pathlib import Path

import pytest

MODEL_PATH = os.environ.get("NEUROVAL_MODEL_PATH")

pytestmark = pytest.mark.skipif(
    not MODEL_PATH or not (Path(MODEL_PATH or ".") / "expdata").exists(),
    reason="Set NEUROVAL_MODEL_PATH to a model folder with expdata/.",
)

# The lab's target files store values with 4 decimals.
LAB_PRECISION = 1e-4


def _build(features_file, protocols_file):
    from neuroval.data import ExperimentalData, load_trace
    from neuroval.data.lab_files import find_recording, read_ljp
    from neuroval.data.statistics import DEFAULT_STD_VALUE, build_targets
    from neuroval.protocols import load_bluepyopt_protocols

    model = Path(MODEL_PATH)
    ljp = read_ljp(model / "config")

    lab = ExperimentalData.from_json(model / "config" / features_file)
    protocols = load_bluepyopt_protocols(model / "config" / protocols_file)

    recordings = {}

    for name in lab.protocols():
        file_path = find_recording(model / "expdata", name)

        if file_path is not None:
            recordings[name] = [load_trace(file_path, ljp=ljp)]

    feature_names = {name: list(lab.features(name)) for name in recordings}
    built, sizes = build_targets(recordings, protocols, feature_names)

    return lab, built, sizes, DEFAULT_STD_VALUE


def test_optimisation_targets_rebuilt_from_recordings():
    """All 37 means in features.json come out of the raw recordings."""

    lab, built, sizes, default_std = _build("features.json", "protocols.json")

    assert built.protocols() == lab.protocols()

    for name in lab.protocols():
        assert set(built.features(name)) == set(lab.features(name))

        for feature, (lab_mean, _) in lab.features(name).items():
            mean, std = built.features(name)[feature]

            assert mean == pytest.approx(lab_mean, abs=LAB_PRECISION)
            assert std == default_std
            assert sizes[name][feature] == 1


def test_full_lab_extraction_rebuilt_from_recordings():
    """Every feature of every recorded protocol in the lab's full file matches.

    The full file (<cell>-features.json, 59 protocols) has recordings in
    expdata/ for its IV, IV-supra, IDthresh and IDthresh-sub protocols.
    """

    config = Path(MODEL_PATH) / "config"
    full_files = sorted(config.glob("*-features.json"))

    if not full_files:
        pytest.skip("No full <cell>-features.json in this model folder.")

    features_file = full_files[0].name
    protocols_file = features_file.replace("-features.json", "-protocols.json")

    lab, built, _, _ = _build(features_file, protocols_file)

    assert len(built.protocols()) > 0

    for name in built.protocols():
        assert set(built.features(name)) == set(lab.features(name))

        for feature, (lab_mean, _) in lab.features(name).items():
            mean, _ = built.features(name)[feature]
            assert mean == pytest.approx(lab_mean, abs=LAB_PRECISION + 1e-4 * abs(lab_mean))
