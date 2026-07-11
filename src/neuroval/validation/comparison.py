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

            comparison[feature] = {
                "experimental": experimental_value,
                "simulated": simulated_value,
                "error": abs(
                    simulated_value - experimental_value
                ),
            }

        return comparison