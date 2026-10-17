"""
Example: Run a single-cell current-clamp simulation.

Usage:
    python examples/run_simulation.py <model_path> [--amplitude 0.6] [--cell 0]
"""

import argparse

import matplotlib.pyplot as plt

from neuroval.protocols import CurrentClamp
from neuroval.validation import ValidationPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="folder of one optimised model")
    parser.add_argument("--amplitude", type=float, default=0.6,
                        help="step current (nA)")
    parser.add_argument("--cell", type=int, default=0,
                        help="Hall of Fame index (Cell_<index>.hoc)")
    parser.add_argument("--no-plot", action="store_true",
                        help="skip the voltage plot")
    return parser.parse_args()


def main() -> None:
    """Run a current-clamp simulation and plot the voltage trace."""

    args = parse_args()

    protocol = CurrentClamp(
        amplitude=args.amplitude,
    )

    pipeline = ValidationPipeline(args.model_path, cell_index=args.cell)

    results = pipeline.run(
        protocol=protocol,
    )

    print(results["features"])

    if args.no_plot:
        return

    plt.figure(figsize=(10, 5))
    plt.plot(
        results["time"],
        results["voltage"],
    )

    plt.xlabel("Time (ms)")
    plt.ylabel("Membrane Potential (mV)")
    plt.title("Current Clamp Simulation")

    plt.grid(True)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
