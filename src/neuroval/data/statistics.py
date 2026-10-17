"""
Build experimental targets from recordings, following BluePyEfe.

For each protocol, every recording gives one value per feature (the mean
over spikes, as in BluePyEfe's Recording.compute_efeatures). Across
recordings, as in BluePyEfe's Target:

    mean = nanmean(values), std = nanstd(values), n = number of values

A std of 0 (for example a single recording) is replaced by
default_std_value, and features with fewer than threshold_nvalue_save
values are not saved (BluePyEfe extract defaults: 1e-3 and 1).
"""

import numpy as np

from neuroval.data.experimental import ExperimentalData
from neuroval.features import FeatureExtractor
from neuroval.protocols import CurrentClamp


DEFAULT_STD_VALUE = 1e-3
THRESHOLD_NVALUE_SAVE = 1


def build_targets(
    recordings: dict[str, list[tuple[np.ndarray, np.ndarray]]],
    protocols: dict[str, CurrentClamp],
    feature_names: list[str] | dict[str, list[str]],
    default_std_value: float = DEFAULT_STD_VALUE,
    threshold_nvalue_save: int = THRESHOLD_NVALUE_SAVE,
) -> tuple[ExperimentalData, dict[str, dict[str, int]]]:
    """Return (targets, sample sizes) built from voltage recordings.

    recordings maps a protocol name to a list of (time, voltage) traces,
    one per recording (cell or repetition). protocols gives the stimulus
    timing used for feature extraction. feature_names is one list for
    all protocols or a list per protocol.
    """

    extractor = FeatureExtractor()
    targets = {}
    sizes = {}

    for name, traces in recordings.items():

        if name not in protocols:
            raise KeyError(f"No protocol definition for '{name}'.")

        protocol = protocols[name]
        names = (
            feature_names[name] if isinstance(feature_names, dict) else feature_names
        )

        values = {feature: [] for feature in names}

        for time, voltage in traces:
            features = extractor.extract(
                time,
                voltage,
                stimulus_start=protocol.stim_start,
                stimulus_end=protocol.stim_end,
                feature_names=names,
            )

            for feature, value in features.items():
                if value is not None:
                    values[feature].append(value)

        protocol_targets, protocol_sizes = _aggregate(
            values, default_std_value, threshold_nvalue_save
        )

        if protocol_targets:
            targets[name] = {"soma": protocol_targets}
            sizes[name] = protocol_sizes

    if not targets:
        raise ValueError("No feature had enough values to build a target.")

    return ExperimentalData(targets), sizes


def _aggregate(
    values: dict[str, list[float]],
    default_std_value: float,
    threshold_nvalue_save: int,
) -> tuple[dict, dict]:
    """Return ({feature: [mean, std]}, {feature: n}) for one protocol."""

    targets = {}
    sizes = {}

    for feature, feature_values in values.items():

        if len(feature_values) < max(threshold_nvalue_save, 1):
            continue

        mean = float(np.mean(feature_values))
        std = float(np.std(feature_values))

        if std == 0.0:
            std = default_std_value

        targets[feature] = [mean, std]
        sizes[feature] = len(feature_values)

    return targets, sizes
