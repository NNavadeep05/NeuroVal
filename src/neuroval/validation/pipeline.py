"""
Validation pipeline for NeuroVal.
"""

from pathlib import Path

import numpy as np

from neuroval.data import ExperimentalData
from neuroval.features import FeatureExtractor
from neuroval.protocols import CurrentClamp
from neuroval.simulation import SimulationError, SimulationRunner
from neuroval.simulation.simulate import CVODE_MINSTEP
from neuroval.validation.comparison import FeatureComparator


# Features reported by run() when none are requested.
DEFAULT_FEATURES = [
    "Spikecount",
    "voltage_base",
    "AP_amplitude",
    "AP_width",
]


class ValidationPipeline:
    """Coordinate simulation, feature extraction and comparison."""

    def __init__(
        self,
        model_path: str | Path,
        cell_index: int = 0,
        celsius: float | None = None,
        v_init: float | None = None,
        cvode_active: bool = True,
        cvode_minstep: float | None = CVODE_MINSTEP,
    ) -> None:
        """Initialize the validation pipeline."""

        self.runner = SimulationRunner(
            model_path,
            cell_index=cell_index,
            celsius=celsius,
            v_init=v_init,
            cvode_active=cvode_active,
            cvode_minstep=cvode_minstep,
        )
        self.extractor = FeatureExtractor()
        self.comparator = FeatureComparator()

    def run(
        self,
        protocol: CurrentClamp | None = None,
        feature_names: list[str] | None = None,
    ) -> dict:
        """Run a simulation and extract electrophysiological features."""

        if protocol is None:
            protocol = CurrentClamp()

        if feature_names is None:
            feature_names = DEFAULT_FEATURES

        if self.runner.cell is None:
            self.runner.load_model()

        time, voltage = self.runner.run_simulation(
            **protocol.to_dict()
        )

        features = self.extractor.extract(
            time,
            voltage,
            stimulus_start=protocol.stim_start,
            stimulus_end=protocol.stim_end,
            feature_names=feature_names,
        )

        return {
            "protocol": protocol.name,
            "time": time,
            "voltage": voltage,
            "features": features,
        }

    def validate(
        self,
        experimental: ExperimentalData,
        protocols: dict[str, CurrentClamp],
    ) -> dict:
        """Validate the model on each protocol against experimental targets.

        Every protocol must have targets, as BasalUnit's eFELFeaturesTest
        requires. Comparison keys follow BluePyOpt objective names:
        protocol.soma.feature.
        """

        if not protocols:
            raise ValueError("No protocols to validate.")

        missing = [name for name in protocols if name not in experimental.protocols()]

        if missing:
            raise ValueError(
                f"No experimental targets for protocols: {missing}"
            )

        # NeuroVal records the soma only. The lab's cell_evaluator.py also
        # supports dendritic targets; refuse them rather than drop them.
        for name in protocols:
            locations = set(experimental.targets[name])

            if locations != {"soma"}:
                raise ValueError(
                    f"Protocol '{name}' has targets at {sorted(locations)}; "
                    "only 'soma' is supported."
                )

        results = {}
        combined = {}

        for name, protocol in protocols.items():

            targets = experimental.features(name)

            try:
                result = self.run(
                    protocol=protocol,
                    feature_names=list(targets),
                )
            except SimulationError as error:
                result = _failed_result(name, targets, error)

            result["comparison"] = self.comparator.compare(
                targets,
                result["features"],
            )

            if "error" in result:
                for values in result["comparison"].values():
                    values["status"] = "simulation_failed"

            for feature, values in result["comparison"].items():
                combined[f"{name}.soma.{feature}"] = values

            results[name] = result

        return {
            "protocols": results,
            "summary": self.comparator.summarise(combined),
        }


def _failed_result(name: str, targets: dict, error: Exception) -> dict:
    """Result of a protocol whose simulation failed.

    BluePyOpt's SweepProtocol sets the responses of a failed run to None,
    so every feature of the protocol is scored as missing.
    """

    return {
        "protocol": name,
        "time": np.array([]),
        "voltage": np.array([]),
        "features": {feature: None for feature in targets},
        "error": str(error),
    }
