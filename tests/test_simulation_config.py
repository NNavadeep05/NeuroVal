"""
Tests for SimulationRunner set-up that do not run NEURON.
"""

import json

import pytest

from neuroval.simulation import SimulationRunner


PARAMETERS = [
    {"param_name": "celsius", "type": "global", "value": 35},
    {"param_name": "v_init", "type": "global", "value": -87.0},
    {"param_name": "g_pas", "type": "range", "bounds": [0, 1]},
]


def _make_model(root, hoc_files=("Cell_0.hoc",), parameters=PARAMETERS,
                morphology="cell.swc"):
    """Create a minimal BluePyOpt model folder."""

    for name in ("checkpoints", "morphology", "config"):
        (root / name).mkdir(parents=True)

    for hoc_file in hoc_files:
        (root / "checkpoints" / hoc_file).write_text("", encoding="utf-8")

    (root / "morphology" / morphology).write_text("", encoding="utf-8")

    if parameters is not None:
        (root / "config" / "parameters.json").write_text(
            json.dumps(parameters), encoding="utf-8"
        )

    return root


def test_settings_read_from_parameters_json(tmp_path):
    """celsius and v_init come from the model's global parameters."""

    runner = SimulationRunner(_make_model(tmp_path / "model"))

    runner.load_simulation_settings()

    assert runner.celsius == 35.0
    assert runner.v_init == -87.0


def test_missing_settings_raise(tmp_path):
    """Without parameters.json or explicit values, NeuroVal refuses to guess."""

    runner = SimulationRunner(_make_model(tmp_path / "model", parameters=None))

    with pytest.raises(ValueError):
        runner.load_simulation_settings()


def test_explicit_settings_used(tmp_path):
    """Explicit values are used when the model has no parameters.json."""

    runner = SimulationRunner(
        _make_model(tmp_path / "model", parameters=None),
        celsius=34,
        v_init=-70,
    )

    runner.load_simulation_settings()

    assert runner.celsius == 34.0
    assert runner.v_init == -70.0


def test_cell_index_selects_hoc_file(tmp_path):
    """The requested Hall of Fame candidate must exist."""

    model = _make_model(tmp_path / "model", hoc_files=("Cell_0.hoc", "Cell_5.hoc"))

    SimulationRunner(model, cell_index=5).validate_model()

    with pytest.raises(FileNotFoundError):
        SimulationRunner(model, cell_index=3).validate_model()


def test_morphology_path_is_relative(tmp_path):
    """The hoc template gets a path relative to checkpoints/, with no spaces."""

    runner = SimulationRunner(_make_model(tmp_path / "folder with spaces" / "model"))

    morphology_dir, morphology_name = runner.morphology_arguments()

    assert morphology_dir == "../morphology"
    assert morphology_name == "cell.swc"


def test_space_in_morphology_name_raises(tmp_path):
    """hoc reads the path with sscanf("%s"), so a space would call quit()."""

    runner = SimulationRunner(
        _make_model(tmp_path / "model", morphology="my cell.swc")
    )

    with pytest.raises(ValueError):
        runner.morphology_arguments()


def test_negative_cell_index_rejected(tmp_path):
    with pytest.raises(ValueError):
        SimulationRunner(_make_model(tmp_path / "model"), cell_index=-1)


def test_more_than_one_swc_rejected(tmp_path):
    model = _make_model(tmp_path / "model")
    (model / "morphology" / "other.swc").write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        SimulationRunner(model).morphology_arguments()


def test_second_hoc_file_in_same_process_refused(tmp_path, monkeypatch):
    """hoc templates are global, so a second model must not load silently."""

    from neuroval.simulation import simulate

    monkeypatch.setattr(simulate, "_loaded_hoc_file", None)

    first = SimulationRunner(_make_model(tmp_path / "a"))
    second = SimulationRunner(_make_model(tmp_path / "b"))

    first._claim_hoc_file()
    first._claim_hoc_file()

    with pytest.raises(RuntimeError, match="one model per Python process"):
        second._claim_hoc_file()


def test_working_directory_restored_when_loading_fails(tmp_path, monkeypatch):
    """A failure inside the hoc template must not leave the cwd changed."""

    import os

    from neuroval.simulation import simulate

    class FakeHoc:
        """Stand-in for neuron.h whose template instantiation fails."""

        chdir = staticmethod(os.chdir)

        def load_file(self, name):
            return 1.0

        def __getattr__(self, name):
            def failing_template(*args):
                raise RuntimeError("hoc template failed")
            return failing_template

    monkeypatch.setattr(simulate, "h", FakeHoc())
    monkeypatch.setattr(simulate, "load_mechanisms", lambda path: True)
    monkeypatch.setattr(simulate, "_loaded_hoc_file", None)

    runner = SimulationRunner(_make_model(tmp_path / "model"))
    original_dir = os.getcwd()

    with pytest.raises(RuntimeError, match="hoc template failed"):
        runner.load_model()

    assert os.getcwd() == original_dir
    assert runner.cell is None


def test_cvode_default_and_option(tmp_path):
    """CVode is the default (lab optimize.py); fixed step is an option."""

    model = _make_model(tmp_path / "model")

    assert SimulationRunner(model).cvode_active is True
    assert SimulationRunner(model, cvode_active=False).cvode_active is False


def test_cvode_minstep_default_and_none(tmp_path):
    """minstep 1e-3 as in optimize.py; None leaves NEURON's default (variate.py)."""

    from neuroval.simulation.simulate import CVODE_MINSTEP

    model = _make_model(tmp_path / "model")

    assert SimulationRunner(model).cvode_minstep == CVODE_MINSTEP == 1e-3
    assert SimulationRunner(model, cvode_minstep=None).cvode_minstep is None


def test_integration_failure_becomes_simulation_error(monkeypatch):
    """A NEURON error inside h.run() is reported as SimulationError."""

    from neuroval.simulation import SimulationError, simulate

    class FailingHoc:
        def run(self):
            raise RuntimeError("variable step integrator error")

    monkeypatch.setattr(simulate, "h", FailingHoc())

    with pytest.raises(SimulationError, match="integrator"):
        SimulationRunner._integrate()


def test_check_simulator_error_is_not_a_simulation_error(monkeypatch):
    """A celsius or v_init mismatch is a configuration error, not masked."""

    from neuroval.simulation import SimulationError, simulate

    class MismatchHoc:
        def check_simulator(self):
            raise RuntimeError("Parameter v_init has different value")

    monkeypatch.setattr(simulate, "h", MismatchHoc())

    with pytest.raises(RuntimeError) as error:
        SimulationRunner._check_simulator()

    assert not isinstance(error.value, SimulationError)
