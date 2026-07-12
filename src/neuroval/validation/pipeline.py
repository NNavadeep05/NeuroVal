"""
Validation pipeline for NeuroVal.
"""

from neuroval.validation.comparison import FeatureComparator
from neuroval.features.extractor import FeatureExtractor
from neuroval.simulation.simulate import SimulationRunner
from neuroval.protocols import CurrentClamp


class ValidationPipeline:
    """Coordinate simulation and feature extraction."""

    def __init__(self, model_path):
        """Initialize the validation pipeline."""

        self.runner = SimulationRunner(model_path)
        self.extractor = FeatureExtractor()
        self.comparator = FeatureComparator()

    def run(
        self,
        protocol=None,
    ):
        """Run a simulation and extract electrophysiological features."""

        if protocol is None:
            protocol = CurrentClamp()

        self.runner.load_model()

        time, voltage = self.runner.run_simulation(
            **protocol.to_dict()
        )

        features = self.extractor.extract(
            time,
            voltage,
            stimulus_start=protocol.delay,
            stimulus_end=protocol.delay + protocol.duration,
        )

        return {
            "time": time,
            "voltage": voltage,
            "features": features,
        }

    def validate(
        self,
        experimental_features,
        protocol=None,
    ):
        """Run a validation experiment."""

        results = self.run(
            protocol=protocol,
        )

        comparison = self.comparator.compare(
            experimental_features,
            results["features"],
        )

        score = self.comparator.score(
            comparison
        )

        results["comparison"] = comparison
        results["score"] = score

        return results