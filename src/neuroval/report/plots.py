"""
Validation plots, modelled on the lab's utils.py.

plot_traces follows plot_responses (recorded trace in light grey under the
simulated one); plot_z_scores follows plot_objectives (horizontal bars
with a line at the acceptance threshold).
"""

import math
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from neuroval.validation.comparison import PASS_THRESHOLD


def plot_traces(
    protocols: dict,
    file_path: Path,
    experimental_traces: dict | None = None,
) -> None:
    """Plot the simulated voltage of every protocol, one panel each."""

    experimental_traces = experimental_traces or {}

    figure = Figure(figsize=(8, 2.2 * len(protocols)))
    axes = figure.subplots(len(protocols), 1, squeeze=False)[:, 0]

    for axis, (name, result) in zip(axes, protocols.items()):

        if name in experimental_traces:
            time, voltage = experimental_traces[name]
            axis.plot(time, voltage, color="lightgrey", label="recorded")

        axis.plot(result["time"], result["voltage"], label="model")
        axis.set_title(name, size="small")
        axis.set_ylabel("V (mV)")

    axes[-1].set_xlabel("Time (ms)")

    if experimental_traces:
        axes[0].legend(loc="upper right", fontsize="small")

    figure.tight_layout()
    figure.savefig(file_path, dpi=100)


def plot_z_scores(features: dict, file_path: Path) -> None:
    """Horizontal bar chart of z-scores with the pass threshold marked.

    Infinite z-scores (zero std) are drawn at the right edge in red.
    """

    names = sorted(features)[::-1]
    values = [features[name]["z_score"] for name in names]

    finite = [value for value in values if math.isfinite(value)]
    edge = max(finite + [PASS_THRESHOLD]) * 1.1

    shown = [value if math.isfinite(value) else edge for value in values]
    colors = [
        "tab:blue" if values[i] < PASS_THRESHOLD else "tab:red"
        for i in range(len(values))
    ]

    figure = Figure(figsize=(8, max(3.0, 0.25 * len(names))))
    axis = figure.subplots()

    positions = np.arange(len(names))
    axis.barh(positions, shown, height=0.75, color=colors)
    axis.axvline(PASS_THRESHOLD, color="lightgray", linewidth=3, alpha=0.7)
    axis.set_yticks(positions)
    axis.set_yticklabels(names, size="small")
    axis.set_xlabel("z-score")

    figure.tight_layout()
    figure.savefig(file_path, dpi=100)
