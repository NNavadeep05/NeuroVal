"""
Loading of experimental voltage recordings.

Reads two-column text files (time in ms, voltage in mV), such as the
lab's expdata/*.dat files or CSV exports. Same reading as the lab's
utils.py plot_responses(): np.loadtxt, then the liquid junction
potential is subtracted (BluePyEfe Recording does the same).
"""

from pathlib import Path

import numpy as np


def load_trace(
    file_path: str | Path,
    ljp: float = 0.0,
    delimiter: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Load one recording and return (time, voltage).

    ljp is the liquid junction potential in mV, given as a positive
    number and subtracted from the voltage (the lab's spec.json gives
    11.5 mV for cell 160118_c7_D1). delimiter=None splits on whitespace;
    use ',' for CSV. Lines starting with '#' are skipped.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Recording not found: {file_path}")

    data = np.loadtxt(file_path, comments="#", delimiter=delimiter, ndmin=2)

    if data.shape[1] < 2:
        raise ValueError(f"{file_path} must have time and voltage columns.")

    if data.shape[0] < 2:
        raise ValueError(f"{file_path} has fewer than two samples.")

    time = data[:, 0]
    voltage = data[:, 1] - ljp

    if not (np.all(np.isfinite(time)) and np.all(np.isfinite(voltage))):
        raise ValueError(f"{file_path} contains non-finite values.")

    if np.any(np.diff(time) <= 0):
        raise ValueError(f"Time in {file_path} must be strictly increasing.")

    return time, voltage
