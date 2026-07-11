"""
Experimental data utilities for NeuroVal.
"""

import json
from pathlib import Path


class ExperimentalData:
    """Represent experimental electrophysiological data."""

    def __init__(self, features):
        """Initialize experimental data."""

        self._validate(features)

        self.features = features

    def _validate(self, features):
        """Validate experimental feature dictionary."""

        if not isinstance(features, dict):
            raise TypeError(
                "Experimental features must be a dictionary."
            )

        if len(features) == 0:
            raise ValueError(
                "Experimental feature dictionary cannot be empty."
            )

        for feature, value in features.items():

            if not isinstance(feature, str):
                raise TypeError(
                    "Feature names must be strings."
                )

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Feature '{feature}' must be numeric."
                )

    @classmethod
    def from_json(cls, file_path):
        """Load experimental features from a JSON file."""

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"JSON file not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as file:
            features = json.load(file)

        return cls(features)