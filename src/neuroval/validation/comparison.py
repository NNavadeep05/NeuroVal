"""
Feature comparison utilities for NeuroVal.
"""


class FeatureComparator:
    """Compare simulated and experimental features."""

    def compare(
        self,
        experimental,
        simulated,
    ):
        """Compare feature dictionaries."""

        comparison = {}

        for feature, experimental_value in experimental.items():

            if feature not in simulated:
                continue

            simulated_value = simulated[feature]

            absolute_error = abs(
                simulated_value - experimental_value
            )

            if experimental_value != 0:
                relative_error = (
                    absolute_error
                    / abs(experimental_value)
                ) * 100
            else:
                relative_error = None

            comparison[feature] = {
                "experimental": experimental_value,
                "simulated": simulated_value,
                "absolute_error": round(
                    absolute_error,
                    3,
                ),
                "relative_error": (
                    round(relative_error, 2)
                    if relative_error is not None
                    else None
                ),
            }

        return comparison

    def score(self, comparison):
        """Compute an overall validation score."""

        relative_errors = []

        for values in comparison.values():

            relative_error = values["relative_error"]

            if relative_error is not None:
                relative_errors.append(relative_error)

        if len(relative_errors) == 0:
            return 0.0

        average_error = (
            sum(relative_errors)
            / len(relative_errors)
        )

        score = max(
            0.0,
            100.0 - average_error,
        )

        return round(score, 2)