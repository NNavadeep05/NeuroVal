"""
Feature comparison utilities for NeuroVal.

Scoring follows the z-score method shared by HippoUnit, BasalUnit and
the lab's own validate.py (humanspn optimisations):

    z = |simulated - experimental mean| / experimental std
"""

import math


# validate.py gives a feature the model cannot produce this z-score.
# BluePyOpt's eFELFeature uses max_score = 250 instead; NeuroVal keeps
# validate.py's value.
MISSING_FEATURE_Z = 13.13

# validate.py accepts a model when its largest z-score is below this.
PASS_THRESHOLD = 3.0


class FeatureComparator:
    """Compare simulated and experimental features."""

    def compare(
        self,
        targets: dict,
        simulated: dict,
    ) -> dict:
        """Compare simulated features with experimental targets.

        targets is {feature: [mean, std]}; simulated is {feature: value},
        with None for features the model could not produce. Every target
        feature appears in the result, so nothing is dropped silently.
        """

        comparison = {}

        for feature, (mean, std) in targets.items():

            value = simulated.get(feature)
            z_score, status = self._z_score(value, mean, std)

            comparison[feature] = {
                "experimental_mean": mean,
                "experimental_std": std,
                "simulated": value,
                "z_score": z_score,
                "status": status,
            }

        return comparison

    @staticmethod
    def _z_score(value, mean: float, std: float) -> tuple[float, str]:
        """Return (z-score, status) for one feature.

        A zero std gives an infinite z even for an exact match, as in
        HippoUnit and BasalUnit, so that feature always fails.
        """

        if value is None or not math.isfinite(value):
            return MISSING_FEATURE_Z, "missing"

        if std == 0:
            return math.inf, "zero_std"

        return abs(value - mean) / std, "ok"

    def summarise(self, comparison: dict) -> dict:
        """Summarise a comparison.

        mean_abs_z: mean over valid features (HippoUnit, BasalUnit score).
        max_z: largest z over all features (validate.py score).
        passed: max_z < PASS_THRESHOLD (validate.py acceptance).
        problem_features: missing or zero-std features (HippoUnit
        bad_features, BasalUnit prob_list).
        """

        valid = [
            values["z_score"]
            for values in comparison.values()
            if values["status"] == "ok"
        ]

        problems = [
            feature
            for feature, values in comparison.items()
            if values["status"] != "ok"
        ]

        all_z = [values["z_score"] for values in comparison.values()]

        if not all_z or any(math.isnan(z) for z in all_z):
            max_z = math.nan
        else:
            max_z = max(all_z)

        return {
            "mean_abs_z": sum(valid) / len(valid) if valid else math.nan,
            "max_z": max_z,
            "passed": not math.isnan(max_z) and max_z < PASS_THRESHOLD,
            "problem_features": problems,
        }
