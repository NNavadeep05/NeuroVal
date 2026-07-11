"""
Validation pipeline for NeuroVal.
"""

from neuroval.validation.comparison import FeatureComparator
from neuroval.features.extractor import FeatureExtractor
from neuroval.simulation.simulate import SimulationRunner


class ValidationPipeline:
    """Coordinate simulation and feature extraction."""

    def __init__(self, model_path):
        """Initialize the validation pipeline."""

        self.runner = SimulationRunner(model_path)
        self.extractor = FeatureExtractor()
        self.comparator = FeatureComparator()

    def run(
        self,
        amplitude=0.2,
        delay=100,
        duration=500,
        tstop=700,
        v_init=-87,
    ):
        """Run a simulation and extract electrophysiological features."""

        self.runner.load_model()

        time, voltage = self.runner.run_simulation(
            amplitude=amplitude,
            delay=delay,
            duration=duration,
            tstop=tstop,
            v_init=v_init,
        )

        features = self.extractor.extract(
            time,
            voltage,
            stimulus_start=delay,
            stimulus_end=delay + duration,
    )
        
        return {
            "time": time,
            "voltage": voltage,
            "features": features,
        }
    
    def validate(
        self,
        experimental_features,
        amplitude=0.2,
        delay=100,
         duration=500,
        tstop=700,
        v_init=-87,
    ):
        
        """Run a validation experiment."""

        results = self.run(
             amplitude=amplitude,
            delay=delay,
            duration=duration,
            tstop=tstop,
            v_init=v_init,
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