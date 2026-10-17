"""
Example: Score a neuron model against experimental targets.

Reads a target file (experimental mean and std per eFEL feature) and a
protocol file from the model folder, runs each protocol, and scores
every feature with a z-score.

Default targets are config/features.json, the targets BluePyOpt
optimised the model against (6 protocols). The lab's full extraction for
the same cell, config/<cell>-features.json with <cell>-protocols.json
(59 protocols), also covers protocols that were not used for fitting.

The lab accepts models with validate.py against a different target set:
population features in valdata/. Failing the max z < 3.0 check here does
not mean the model fails the lab's population validation.

Usage:
    python examples/validate_model.py <model_path> [--cell 0] [--output results/]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from neuroval.data import ExperimentalData, load_trace
from neuroval.data.lab_files import find_recording, read_ljp
from neuroval.protocols import load_bluepyopt_protocols
from neuroval.report import save_results
from neuroval.validation import ValidationPipeline
from neuroval.validation.comparison import PASS_THRESHOLD


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="folder of one optimised model")
    parser.add_argument("--cell", type=int, default=0,
                        help="Hall of Fame index (Cell_<index>.hoc)")
    parser.add_argument("--targets", default="config/features.json",
                        help="target file, relative to model_path")
    parser.add_argument("--protocols-file", default="config/protocols.json",
                        help="protocol file, relative to model_path")
    parser.add_argument("--protocols", nargs="+", default=None,
                        help="protocol names (default: all with targets)")
    parser.add_argument("--cvode-minstep", default="1e-3",
                        help="CVode minimum step in ms (optimize.py: 1e-3); "
                             "'none' keeps NEURON's default as in variate.py")
    parser.add_argument("--output", default=None,
                        help="folder for JSON outputs, plots and report.html")
    parser.add_argument("--overlay-recordings", action="store_true",
                        help="draw the recordings in expdata/ under the model traces")
    parser.add_argument("--no-plot", action="store_true",
                        help="skip the interactive voltage plots")
    return parser.parse_args()


def print_report(results: dict, targets_file: str) -> None:
    """Print a console validation report."""

    summary = results["summary"]

    print("=" * 60)
    print("NeuroVal Validation Report")
    print(f"Targets: {targets_file}")
    print("=" * 60)

    for name, protocol in results["protocols"].items():

        print(f"\n{name}")

        if "error" in protocol:
            print(f"  simulation failed: {protocol['error']}")

        for feature, values in protocol["comparison"].items():

            simulated = values["simulated"]
            simulated_text = "None" if simulated is None else f"{simulated:.3f}"

            print(
                f"  {feature:<32} "
                f"exp {values['experimental_mean']:.3f} +- {values['experimental_std']:.3f}  "
                f"sim {simulated_text:<10} "
                f"z {values['z_score']:.2f}  {values['status']}"
            )

    print("\n" + "-" * 60)
    print(f"Mean |z|         : {summary['mean_abs_z']:.2f}")
    print(f"Max z            : {summary['max_z']:.2f}")
    print(f"Passed (max z < {PASS_THRESHOLD}) : {summary['passed']}")
    print(f"Problem features : {summary['problem_features']}")


def plot_traces(results: dict) -> None:
    """Plot the voltage trace of every protocol."""

    protocols = results["protocols"]

    figure, axes = plt.subplots(
        len(protocols), 1, figsize=(10, 2.5 * len(protocols)), squeeze=False
    )

    for axis, (name, protocol) in zip(axes[:, 0], protocols.items()):
        axis.plot(protocol["time"], protocol["voltage"])
        axis.set_title(name)
        axis.set_ylabel("V (mV)")
        axis.grid(True)

    axes[-1, 0].set_xlabel("Time (ms)")
    figure.tight_layout()
    plt.show()


def load_recordings(model: Path, names: list[str]) -> dict:
    """Load the recorded traces available in expdata/ for an overlay."""

    ljp = read_ljp(model / "config")
    traces = {}

    for name in names:
        file_path = find_recording(model / "expdata", name)

        if file_path is not None:
            traces[name] = load_trace(file_path, ljp=ljp)

    return traces


def main() -> None:
    """Run a validation experiment."""

    args = parse_args()

    model = Path(args.model_path)

    experimental = ExperimentalData.from_json(model / args.targets)

    protocols = load_bluepyopt_protocols(
        model / args.protocols_file,
        names=args.protocols or experimental.protocols(),
    )

    minstep = None if args.cvode_minstep.lower() == "none" else float(args.cvode_minstep)

    # Load the overlay first, so a bad recording fails before the simulation.
    recordings = (
        load_recordings(model, list(protocols)) if args.overlay_recordings else None
    )

    pipeline = ValidationPipeline(
        args.model_path, cell_index=args.cell, cvode_minstep=minstep
    )

    results = pipeline.validate(experimental, protocols)

    print_report(results, args.targets)

    if args.output:
        metadata = {
            "model": model.name,
            "cell": f"Cell_{args.cell}",
            "targets": args.targets,
            "protocols": args.protocols_file,
            "integrator": "CVode" if pipeline.runner.cvode_active else "fixed step",
            "cvode_minstep": args.cvode_minstep,
        }
        paths = save_results(results, args.output, metadata, recordings)
        print(f"\nReport written to {paths['report']}")

    if not args.no_plot:
        plot_traces(results)


if __name__ == "__main__":
    main()
