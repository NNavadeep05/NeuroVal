"""
Example: Validate every exported Hall of Fame cell of one model.

Runs examples/validate_model.py once per Cell_<n>.hoc in checkpoints/,
each in its own Python process (one hoc model per process), writes the
per-cell outputs to <output>/Cell_<n>/ and a summary.json for all cells.

Usage:
    python examples/validate_all_cells.py <model_path> --output results/ [--jobs 4]
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from neuroval.batch import available_cells, summarise_cells

VALIDATE_SCRIPT = Path(__file__).with_name("validate_model.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="folder of one optimised model")
    parser.add_argument("--output", required=True,
                        help="folder for per-cell results and summary.json")
    parser.add_argument("--targets", default="config/features.json",
                        help="target file, relative to model_path")
    parser.add_argument("--protocols-file", default="config/protocols.json",
                        help="protocol file, relative to model_path")
    parser.add_argument("--cvode-minstep", default="1e-3",
                        help="passed to validate_model.py")
    parser.add_argument("--jobs", type=int, default=1,
                        help="number of cells validated in parallel")
    return parser.parse_args()


def run_cell(args: argparse.Namespace, cell: int) -> int:
    """Validate one cell in a separate Python process; return its exit code."""

    cell_dir = Path(args.output) / f"Cell_{cell}"
    cell_dir.mkdir(parents=True, exist_ok=True)

    # A failed re-run must not leave the previous run's scores behind.
    (cell_dir / "scores.json").unlink(missing_ok=True)

    command = [
        sys.executable, str(VALIDATE_SCRIPT), args.model_path,
        "--cell", str(cell),
        "--targets", args.targets,
        "--protocols-file", args.protocols_file,
        "--cvode-minstep", args.cvode_minstep,
        "--output", str(cell_dir),
        "--no-plot",
    ]

    with (cell_dir / "log.txt").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)

    return completed.returncode


def main() -> None:
    args = parse_args()

    if args.jobs < 1:
        raise SystemExit("--jobs must be at least 1.")

    cells = available_cells(args.model_path)
    print(f"Exported cells: {[f'Cell_{cell}' for cell in cells]}")

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        exit_codes = dict(zip(cells, pool.map(lambda cell: run_cell(args, cell), cells)))

    summary = summarise_cells(args.output, cells)

    for cell, code in exit_codes.items():
        if code != 0:
            summary[f"Cell_{cell}"]["exit_code"] = code

    summary_file = Path(args.output) / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    print(f"\n{'cell':<8} {'mean |z|':>9} {'max z':>8}  passed")

    for name, values in summary.items():
        if "error" in values:
            print(f"{name:<8} {values['error']} (see {name}/log.txt)")
        else:
            print(
                f"{name:<8} {_number(values['mean_abs_z']):>9} "
                f"{_number(values['max_z']):>8}  {values['passed']}"
            )

    print(f"\nSummary written to {summary_file}")

    failed = any(code != 0 for code in exit_codes.values()) or any(
        "error" in values for values in summary.values()
    )

    if failed:
        raise SystemExit(1)


def _number(value) -> str:
    """Format a summary number; null (NaN or inf in scores.json) as n/a."""

    return "n/a" if value is None else f"{value:.2f}"


if __name__ == "__main__":
    main()
