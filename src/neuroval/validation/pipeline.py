"""
Validation pipeline for NeuroVal.
"""

import time

from neuroval.features.extractor import FeatureExtractor
from neuroval.simulation.simulate import SimulationRunner


class ValidationPipeline:
    """Coordinate simulation and feature extraction."""

    def __init__(self, model_path):
        """Initialize the validation pipeline."""

        self.runner = SimulationRunner(model_path)
        self.extractor = FeatureExtractor()

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