"""
Feature extraction utilities for NeuroVal.

This module extracts electrophysiological
features from voltage traces using eFEL.
"""
from unittest import result

import numpy as np
import efel

import efel


class FeatureExtractor:
    """Extract electrophysiological features."""

    def extract(
        self,
        time,
        voltage,
        stimulus_start,
        stimulus_end,
    ):
        """Extract electrophysiological features."""

        trace = {
            "T": time,
            "V": voltage,
            "stim_start": [stimulus_start],
            "stim_end": [stimulus_end],
        }

        feature_names = [
            "Spikecount",
            "voltage_base",
            "AP_amplitude",
            "AP_width",
        ]

        features = efel.getFeatureValues(
            [trace],
            feature_names,
        )

        result = features[0]

        summary = {
            "Spikecount": int(result["Spikecount"][0]),
            "RestingPotential": round(float(result["voltage_base"][0]), 3),
            "Mean_AP_amplitude": round(float(np.mean(result["AP_amplitude"])), 3),
            "Mean_AP_width": round(float(np.mean(result["AP_width"])), 3),
        }

        return summary