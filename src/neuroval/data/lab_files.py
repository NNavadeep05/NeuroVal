"""
File conventions of the lab's humanspn model folders.

The voltage recording for protocol IDthresh_587 is expdata/*_ch3_587.dat
(mapping used in the lab's select.ipynb), and the liquid junction
potential is stored in config/<cell>-spec.json.
"""

import json
from pathlib import Path


def read_ljp(config_dir: str | Path) -> float:
    """Read the liquid junction potential (mV) from the cell's spec file."""

    spec_files = sorted(Path(config_dir).glob("*-spec.json"))

    if len(spec_files) != 1:
        raise FileNotFoundError(
            f"Expected one *-spec.json in {config_dir}, found {len(spec_files)}."
        )

    spec = json.loads(spec_files[0].read_text(encoding="utf-8"))
    return float(spec["liquid_junction_potential"])


def find_recording(
    expdata_dir: str | Path,
    protocol: str,
    channel: str = "ch3",
) -> Path | None:
    """Return the voltage recording of a protocol, or None if not recorded."""

    number = protocol.rsplit("_", 1)[-1]
    matches = sorted(Path(expdata_dir).glob(f"*_{channel}_{number}.dat"))

    if len(matches) > 1:
        raise ValueError(f"More than one recording for {protocol}: {matches}")

    return matches[0] if matches else None
