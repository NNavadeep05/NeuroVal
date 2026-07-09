"""
Simulation utilities for NeuroVal.

This module is responsible for loading and running
single-cell NEURON models.
"""

from pathlib import Path
from neuron import h, load_mechanisms
import numpy as np


class SimulationRunner:
    """Run NEURON simulations for a single-cell model."""

    def __init__(self, model_path):
        """Initialize the simulation runner."""

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_path}"
            )

        self.checkpoints_dir = self.model_path / "checkpoints"
        self.morphology_dir = self.model_path / "morphology"
        self.config_dir = self.model_path / "config"

    def validate_model(self):
        """Validate the model directory structure."""

        required_dirs = {
            "checkpoints": self.checkpoints_dir,
            "morphology": self.morphology_dir,
            "config": self.config_dir,
        }

        for name, directory in required_dirs.items():
            if not directory.exists():
                raise FileNotFoundError(
                    f"Required directory '{name}' not found: {directory}"
                )

        hoc_files = list(self.checkpoints_dir.glob("Cell_*.hoc"))

        if not hoc_files:
            raise FileNotFoundError(
                f"No Cell_*.hoc files found in: {self.checkpoints_dir}"
            )

    def load_model(self):
        """Load the NEURON model."""

        self.validate_model()

        load_mechanisms(str(self.model_path.parent / "mechanisms"))

        h.load_file("stdrun.hoc")

        hoc_files = list(self.checkpoints_dir.glob("Cell_*.hoc"))
        self.hoc_file = hoc_files[0]

        h.chdir(str(self.checkpoints_dir))
        h.load_file(str(self.hoc_file.name))

        morphology_files = list(self.morphology_dir.glob("*.swc"))

        if not morphology_files:
            raise FileNotFoundError(
                f"No SWC morphology found in: {self.morphology_dir}"
            )

        self.morphology_file = morphology_files[0]

        self.cell = h.Cell_0(
            str(self.morphology_dir),
            self.morphology_file.name,
        )

    def run_simulation(
        self,
        delay=100,
        duration=500,
        amplitude=0.2,
        tstop=700,
        v_init=-87,
    ):
        """Run a current-clamp simulation."""

        h.finitialize(v_init)

        stim = h.IClamp(self.cell.soma[0](0.5))
        stim.delay = delay
        stim.dur = duration
        stim.amp = amplitude

        self.time = h.Vector()
        self.voltage = h.Vector()

        self.time.record(h._ref_t)
        self.voltage.record(
            self.cell.soma[0](0.5)._ref_v
        )

        h.tstop = tstop
        h.run()

        return (
            np.array(self.time),
            np.array(self.voltage),
        )