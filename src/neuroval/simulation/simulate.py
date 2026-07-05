"""
Simulation utilities for NeuroVal.

This module is responsible for loading and running
single-cell NEURON models.
"""

from pathlib import Path


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