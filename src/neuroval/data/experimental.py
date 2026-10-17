"""
Experimental data utilities for NeuroVal.
"""

import json
import math
from pathlib import Path


class ExperimentalData:
    """Represent experimental electrophysiological targets.

    Uses the format written by BluePyEfe and read by BluePyOpt and
    BasalUnit (config/features.json):

        {protocol: {location: {efel_feature: [mean, std]}}}
    """

    def __init__(self, targets: dict) -> None:
        """Initialize experimental data."""

        self._validate(targets)

        self.targets = targets

    def protocols(self) -> list[str]:
        """Return the protocol names that have targets."""

        return list(self.targets)

    def features(self, protocol: str, location: str = "soma") -> dict:
        """Return {feature: [mean, std]} for one protocol and location."""

        if protocol not in self.targets:
            raise KeyError(
                f"No experimental targets for protocol '{protocol}'. "
                f"Available: {self.protocols()}"
            )

        locations = self.targets[protocol]

        if location not in locations:
            raise KeyError(
                f"No '{location}' targets for protocol '{protocol}'."
            )

        return locations[location]

    def _validate(self, targets: dict) -> None:
        """Validate the target dictionary."""

        if not isinstance(targets, dict):
            raise TypeError(
                "Experimental targets must be a dictionary."
            )

        if len(targets) == 0:
            raise ValueError(
                "Experimental target dictionary cannot be empty."
            )

        for protocol, locations in targets.items():

            if not isinstance(locations, dict):
                raise ValueError(
                    f"Protocol '{protocol}' must map locations to features."
                )

            for location, features in locations.items():

                if not isinstance(features, dict):
                    raise ValueError(
                        f"'{protocol}.{location}' must map features to [mean, std]."
                    )

                for feature, value in features.items():
                    self._validate_target(f"{protocol}.{location}.{feature}", value)

    @staticmethod
    def _validate_target(name: str, value) -> None:
        """Check that a target is a finite [mean, std] with std >= 0."""

        if (
            not isinstance(value, (list, tuple))
            or len(value) != 2
            or not all(
                isinstance(item, (int, float))
                and not isinstance(item, bool)
                and math.isfinite(item)
                for item in value
            )
        ):
            raise ValueError(
                f"Target '{name}' must be [mean, std], got {value!r}."
            )

        if value[1] < 0:
            raise ValueError(
                f"Target '{name}' has a negative standard deviation."
            )

    def to_json(self, file_path: str | Path) -> None:
        """Save the targets in the features.json format."""

        with Path(file_path).open("w", encoding="utf-8") as file:
            json.dump(self.targets, file, indent=4)

    @classmethod
    def from_json(cls, file_path: str | Path) -> "ExperimentalData":
        """Load experimental targets from a JSON file."""

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"JSON file not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as file:
            targets = json.load(file)

        return cls(targets)
