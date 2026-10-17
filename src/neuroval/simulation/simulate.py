"""
Simulation utilities for NeuroVal.

This module is responsible for loading and running
single-cell NEURON models exported by BluePyOpt.
"""

import json
import os
from pathlib import Path

import numpy as np
from neuron import h, load_mechanisms


# The lab's optimize.py ran BluePyOpt's NrnSimulator with CVode
# (cvode_active=True is its default) and cvode_minstep=1e-3.
CVODE_MINSTEP = 1e-3

# Fixed time step (ms) used when cvode_active=False, as in HippoUnit.
DT = 0.025

# NEURON keeps hoc templates and procs (e.g. check_simulator) global and
# h.load_file() skips names it has already loaded. A second Cell_N.hoc in
# the same process would silently run the first model's biophysics, so only
# one hoc file is allowed per Python process.
_loaded_hoc_file = None


class SimulationError(RuntimeError):
    """NEURON failed while integrating a protocol (for example a CVode error)."""


class SimulationRunner:
    """Run NEURON simulations for a single-cell model."""

    def __init__(
        self,
        model_path: str | Path,
        cell_index: int = 0,
        celsius: float | None = None,
        v_init: float | None = None,
        cvode_active: bool = True,
        cvode_minstep: float | None = CVODE_MINSTEP,
    ) -> None:
        """Initialize the simulation runner.

        cell_index selects the Hall of Fame candidate (Cell_<index>.hoc),
        like BasalUnit's hof_index. The optimisations README names #0 as
        the release model, but not every folder exports Cell_0.hoc.
        celsius and v_init are read from config/parameters.json unless
        given here. cvode_active=True integrates with CVode as the lab's
        optimisation did; False uses a fixed 0.025 ms step. cvode_minstep
        is 1e-3 ms as in optimize.py; None keeps NEURON's default, as the
        lab's variate.py does (NrnSimulator() without a minstep).
        """

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_path}"
            )

        if not isinstance(cell_index, int) or isinstance(cell_index, bool) or cell_index < 0:
            raise ValueError("cell_index must be a non-negative integer.")

        self.cell_index = cell_index
        self.cvode_active = cvode_active
        self.cvode_minstep = cvode_minstep
        self.celsius = celsius
        self.v_init = v_init
        self.cell = None

        self.checkpoints_dir = self.model_path / "checkpoints"
        self.morphology_dir = self.model_path / "morphology"
        self.config_dir = self.model_path / "config"
        self.hoc_file = self.checkpoints_dir / f"Cell_{cell_index}.hoc"

    def validate_model(self) -> None:
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

        if not self.hoc_file.exists():
            available = sorted(
                path.name for path in self.checkpoints_dir.glob("Cell_*.hoc")
            )
            raise FileNotFoundError(
                f"{self.hoc_file.name} not found in {self.checkpoints_dir}. "
                f"Available: {available}"
            )

    def load_simulation_settings(self) -> None:
        """Read celsius and v_init from the model's global parameters.

        Same approach as HippoUnit's ModelLoader_BPO: the temperature and
        initial voltage used during optimisation are stored as global
        parameters in config/parameters.json.
        """

        global_values = self._read_global_parameters()

        if self.celsius is None:
            self.celsius = global_values.get("celsius")

        if self.v_init is None:
            self.v_init = global_values.get("v_init")

        missing = [
            name
            for name, value in (("celsius", self.celsius), ("v_init", self.v_init))
            if value is None
        ]

        if missing:
            raise ValueError(
                f"{missing} not found in {self.config_dir / 'parameters.json'}. "
                "Pass them to SimulationRunner explicitly."
            )

        self.celsius = float(self.celsius)
        self.v_init = float(self.v_init)

    def _read_global_parameters(self) -> dict:
        """Return {name: value} for global parameters in parameters.json."""

        params_file = self.config_dir / "parameters.json"

        if not params_file.exists():
            return {}

        with params_file.open("r", encoding="utf-8") as file:
            parameters = json.load(file)

        if not isinstance(parameters, list):
            raise ValueError(
                f"Unsupported parameters.json format in {params_file}: "
                "expected a list of parameter definitions."
            )

        return {
            parameter["param_name"]: parameter["value"]
            for parameter in parameters
            if parameter.get("type") == "global" and "value" in parameter
        }

    def morphology_arguments(self) -> tuple[str, str]:
        """Return (morphology_dir, morphology_name) for the hoc template.

        The BluePyOpt template reads the path with sscanf("%s"), which stops
        at the first whitespace and then calls quit(). The directory is
        therefore given relative to checkpoints/, and whitespace is rejected
        up front.
        """

        morphology_files = sorted(self.morphology_dir.glob("*.swc"))

        if not morphology_files:
            raise FileNotFoundError(
                f"No SWC morphology found in: {self.morphology_dir}"
            )

        if len(morphology_files) > 1:
            raise ValueError(
                f"More than one SWC file in {self.morphology_dir}: "
                f"{[path.name for path in morphology_files]}"
            )

        morphology_dir = Path(
            os.path.relpath(self.morphology_dir, self.checkpoints_dir)
        ).as_posix()
        morphology_name = morphology_files[0].name

        if any(char.isspace() for char in morphology_dir + morphology_name):
            raise ValueError(
                "The hoc template cannot read morphology paths with whitespace: "
                f"{morphology_dir}/{morphology_name}"
            )

        return morphology_dir, morphology_name

    def load_model(self) -> None:
        """Load the NEURON model. Does nothing if it is already loaded."""

        if self.cell is not None:
            return

        self.validate_model()
        self.load_simulation_settings()
        morphology_dir, morphology_name = self.morphology_arguments()
        self._claim_hoc_file()

        load_mechanisms(str(self.model_path.parent / "mechanisms"))

        h.load_file("stdrun.hoc")

        # The hoc template resolves the morphology path from checkpoints/.
        # Restore the original directory afterwards, as BasalUnit does.
        original_dir = os.getcwd()

        try:
            h.chdir(str(self.checkpoints_dir))
            h.load_file(self.hoc_file.name)
            template = getattr(h, f"Cell_{self.cell_index}")
            self.cell = template(morphology_dir, morphology_name)
        finally:
            h.chdir(original_dir)

    def _claim_hoc_file(self) -> None:
        """Refuse to load a second, different hoc file in this process."""

        global _loaded_hoc_file

        hoc_file = self.hoc_file.resolve()

        if _loaded_hoc_file is not None and _loaded_hoc_file != hoc_file:
            raise RuntimeError(
                f"{_loaded_hoc_file} is already loaded in this process. "
                "NEURON keeps hoc templates global, so validate one model "
                "per Python process."
            )

        _loaded_hoc_file = hoc_file

    def run_simulation(
        self,
        delay: float = 100,
        duration: float = 500,
        amplitude: float = 0.2,
        tstop: float = 700,
        holding: float = 0.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run a current-clamp simulation and return the recorded voltage trace.

        holding is a whole-sweep current, the second stimulus in the lab's
        protocols.json files.
        """

        if self.cell is None:
            raise RuntimeError("Call load_model() before run_simulation().")

        if delay + duration > tstop:
            raise ValueError("The stimulus must end before tstop.")

        soma = self.cell.soma[0](0.5)

        stimuli = [self._square_pulse(soma, amplitude, delay, duration)]

        if holding != 0.0:
            stimuli.append(self._square_pulse(soma, holding, 0.0, tstop))

        self.time = h.Vector()
        self.voltage = h.Vector()

        self.time.record(h._ref_t)
        self.voltage.record(soma._ref_v)

        # h.run() initialises with the hoc globals, so set them here
        # (HippoUnit sets h.v_init and h.celsius the same way).
        h.celsius = self.celsius
        h.v_init = self.v_init
        self._check_simulator()

        h.tstop = tstop

        if self.cvode_active:
            # Same as BluePyOpt's NrnSimulator.run(): set the minstep for
            # this run and restore the previous value afterwards.
            cvode = h.CVode()
            h.cvode_active(1)
            previous_minstep = cvode.minstep()

            if self.cvode_minstep is not None:
                cvode.minstep(self.cvode_minstep)

            try:
                self._integrate()
            finally:
                cvode.minstep(previous_minstep)
        else:
            h.cvode_active(0)
            h.dt = DT
            h.steps_per_ms = 1.0 / DT
            self._integrate()

        return (
            np.array(self.time),
            np.array(self.voltage),
        )

    @staticmethod
    def _integrate() -> None:
        """Run NEURON; report integration failures as SimulationError."""

        try:
            h.run()
        except RuntimeError as error:
            raise SimulationError(str(error)) from error

    @staticmethod
    def _square_pulse(segment, amplitude: float, delay: float, duration: float):
        """Create an IClamp square pulse on a segment."""

        stim = h.IClamp(segment)
        stim.delay = delay
        stim.dur = duration
        stim.amp = amplitude
        return stim

    @staticmethod
    def _check_simulator() -> None:
        """Run the BluePyOpt check that celsius and v_init match the optimisation."""

        try:
            check = h.check_simulator
        except AttributeError:
            return

        check()
