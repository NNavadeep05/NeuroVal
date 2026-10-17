import json

import pytest

from neuroval.protocols import CurrentClamp, load_bluepyopt_protocols


PROTOCOLS = {
    "IDthresh_587": {
        "stimuli": [
            {
                "amp": 0.4465,
                "delay": 700,
                "duration": 2000,
                "totduration": 3000.0,
            },
            {
                "amp": 0.0009,
                "delay": 0.0,
                "duration": 3000.0,
                "totduration": 3000.0,
            },
        ]
    },
    "IV_546": {
        "stimuli": [
            {
                "amp": -0.65,
                "delay": 100,
                "duration": 1000,
                "totduration": 1400.0,
            },
        ]
    },
}


@pytest.fixture
def protocols_file(tmp_path):
    file_path = tmp_path / "protocols.json"
    file_path.write_text(json.dumps(PROTOCOLS), encoding="utf-8")
    return file_path


def test_load_step_and_holding(protocols_file):
    """The whole-sweep second stimulus becomes the holding current."""

    protocol = CurrentClamp.from_bluepyopt(protocols_file, "IDthresh_587")

    assert protocol.name == "IDthresh_587"
    assert protocol.amplitude == 0.4465
    assert protocol.delay == 700
    assert protocol.duration == 2000
    assert protocol.tstop == 3000.0
    assert protocol.holding == 0.0009
    assert protocol.stim_start == 700
    assert protocol.stim_end == 2700


def test_load_without_holding(protocols_file):
    """A protocol with a single stimulus has no holding current."""

    protocol = CurrentClamp.from_bluepyopt(protocols_file, "IV_546")

    assert protocol.holding == 0.0


def test_load_all(protocols_file):
    """All protocols in the file load in file order."""

    protocols = load_bluepyopt_protocols(protocols_file)

    assert list(protocols) == ["IDthresh_587", "IV_546"]


def test_unknown_protocol(protocols_file):
    with pytest.raises(KeyError):
        CurrentClamp.from_bluepyopt(protocols_file, "IV_999")


def test_unsupported_second_stimulus(tmp_path):
    """Only a whole-sweep second stimulus is accepted as holding current."""

    data = {
        "P": {
            "stimuli": [
                {"amp": 0.1, "delay": 100, "duration": 500, "totduration": 700},
                {"amp": 0.2, "delay": 200, "duration": 100, "totduration": 700},
            ]
        }
    }
    file_path = tmp_path / "protocols.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError):
        CurrentClamp.from_bluepyopt(file_path, "P")


def test_to_dict_has_no_v_init():
    """v_init is a model setting (parameters.json), not a protocol setting."""

    protocol = CurrentClamp(amplitude=0.6, holding=0.001)

    assert protocol.to_dict() == {
        "amplitude": 0.6,
        "delay": 100,
        "duration": 500,
        "tstop": 700,
        "holding": 0.001,
    }


def test_stimulus_must_end_before_tstop():
    with pytest.raises(ValueError):
        CurrentClamp(delay=100, duration=500, tstop=500)


def _write(tmp_path, data):
    file_path = tmp_path / "protocols.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_empty_stimuli(tmp_path):
    file_path = _write(tmp_path, {"P": {"stimuli": []}})

    with pytest.raises(ValueError):
        CurrentClamp.from_bluepyopt(file_path, "P")


def test_holding_must_span_the_step_sweep(tmp_path):
    """The holding stimulus must last as long as the step's sweep."""

    file_path = _write(tmp_path, {
        "P": {
            "stimuli": [
                {"amp": 0.1, "delay": 100, "duration": 500, "totduration": 1400},
                {"amp": 0.001, "delay": 0, "duration": 1000, "totduration": 1000},
            ]
        }
    })

    with pytest.raises(ValueError):
        CurrentClamp.from_bluepyopt(file_path, "P")
