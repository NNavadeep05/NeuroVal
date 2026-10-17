"""
Feature extraction utilities for NeuroVal.

This module extracts electrophysiological
features from voltage traces using eFEL.
"""

import efel
import numpy as np


# Spike threshold for somatic recordings, as in the lab's
# cell_evaluator.py and BasalUnit's define_fitness_calculator().
SOMA_THRESHOLD = -20.0


class FeatureExtractor:
    """Extract electrophysiological features."""

    def extract(
        self,
        time: np.ndarray,
        voltage: np.ndarray,
        stimulus_start: float,
        stimulus_end: float,
        feature_names: list[str],
        threshold: float = SOMA_THRESHOLD,
    ) -> dict[str, float | None]:
        """Extract electrophysiological features.

        Returns {eFEL feature name: value}. Names are kept as in eFEL so
        they match BluePyEfe and BluePyOpt target files. A feature eFEL
        cannot compute (for example AP_amplitude without spikes) is None.
        """

        trace = {
            "T": time,
            "V": voltage,
            "stim_start": [stimulus_start],
            "stim_end": [stimulus_end],
        }

        # set_setting is global in eFEL; restore the previous value after.
        previous_threshold = efel.get_settings().Threshold
        efel.set_setting("Threshold", threshold)

        try:
            results = efel.get_feature_values(
                [trace],
                feature_names,
                raise_warnings=False,
            )[0]
        finally:
            efel.set_setting("Threshold", previous_threshold)

        return {
            name: self._summarise(results[name])
            for name in feature_names
        }

    @staticmethod
    def _summarise(values) -> float | None:
        """Reduce eFEL output to one value per trace.

        Same reduction as BluePyEfe's Recording.compute_efeatures: the mean
        of the values, or no value when eFEL returns nothing.
        """

        if values is None:
            return None

        values = [
            value for value in values
            if value is not None and not np.isnan(value)
        ]

        if len(values) == 0:
            return None

        mean = float(np.mean(values))

        if not np.isfinite(mean):
            return None

        return mean
