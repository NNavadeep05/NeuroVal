"""
Current-clamp stimulation protocol for NeuroVal.
"""


class CurrentClamp:
    """Represent a current-clamp stimulation protocol."""

    def __init__(
        self,
        amplitude=0.2,
        delay=100,
        duration=500,
        tstop=700,
        v_init=-87,
    ):
        """Initialize a current-clamp protocol."""

        self.amplitude = amplitude
        self.delay = delay
        self.duration = duration
        self.tstop = tstop
        self.v_init = v_init

    def to_dict(self):
        """Return protocol parameters as a dictionary."""

        return {
            "amplitude": self.amplitude,
            "delay": self.delay,
            "duration": self.duration,
            "tstop": self.tstop,
            "v_init": self.v_init,
        }