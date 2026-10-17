"""
Current-clamp stimulation protocol for NeuroVal.
"""

import json
from pathlib import Path


class CurrentClamp:
    """Represent a current-clamp stimulation protocol.

    Stores the stimulation parameters required to execute a
    current-clamp experiment: a test step plus an optional
    whole-sweep holding current.
    """

    def __init__(
        self,
        amplitude: float = 0.2,
        delay: float = 100,
        duration: float = 500,
        tstop: float = 700,
        holding: float = 0.0,
        name: str = "CurrentClamp",
    ) -> None:
        """Initialize a current-clamp protocol."""

        if delay < 0:
            raise ValueError("delay cannot be negative.")

        if duration <= 0:
            raise ValueError("duration must be positive.")

        if delay + duration > tstop:
            raise ValueError("The stimulus must end before tstop.")

        self.amplitude = amplitude
        self.delay = delay
        self.duration = duration
        self.tstop = tstop
        self.holding = holding
        self.name = name

    @property
    def stim_start(self) -> float:
        """Start of the test step (ms)."""

        return self.delay

    @property
    def stim_end(self) -> float:
        """End of the test step (ms)."""

        return self.delay + self.duration

    def to_dict(self) -> dict:
        """Return protocol parameters as a dictionary."""

        return {
            "amplitude": self.amplitude,
            "delay": self.delay,
            "duration": self.duration,
            "tstop": self.tstop,
            "holding": self.holding,
        }

    @classmethod
    def from_bluepyopt(cls, file_path: str | Path, name: str) -> "CurrentClamp":
        """Load one protocol from a BluePyOpt protocols.json file.

        As in the lab's cell_evaluator.py and BasalUnit, stimuli[0] is the
        test step. A second stimulus that spans the whole sweep is the
        holding current.
        """

        protocols = _read_protocols(file_path)

        if name not in protocols:
            raise KeyError(
                f"Protocol '{name}' not found in {file_path}. "
                f"Available: {list(protocols)}"
            )

        stimuli = protocols[name].get("stimuli", [])

        if len(stimuli) == 0:
            raise ValueError(f"Protocol '{name}' has no stimuli.")

        step = stimuli[0]

        if len(stimuli) > 2:
            raise ValueError(
                f"Protocol '{name}' has {len(stimuli)} stimuli; "
                "only a step plus a holding current is supported."
            )

        holding = 0.0

        if len(stimuli) == 2:
            extra = stimuli[1]

            if (
                extra["delay"] != 0
                or extra["duration"] != extra["totduration"]
                or extra["totduration"] != step["totduration"]
            ):
                raise ValueError(
                    f"The second stimulus of '{name}' is not a whole-sweep "
                    "holding current."
                )

            holding = extra["amp"]

        return cls(
            amplitude=step["amp"],
            delay=step["delay"],
            duration=step["duration"],
            tstop=step["totduration"],
            holding=holding,
            name=name,
        )


def load_bluepyopt_protocols(
    file_path: str | Path,
    names: list[str] | None = None,
) -> dict[str, CurrentClamp]:
    """Load protocols from a BluePyOpt protocols.json file.

    Returns {name: CurrentClamp}, in file order unless names are given.
    """

    if names is None:
        names = list(_read_protocols(file_path))

    return {
        name: CurrentClamp.from_bluepyopt(file_path, name)
        for name in names
    }


def _read_protocols(file_path: str | Path) -> dict:
    """Read a protocols.json file."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Protocol file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
