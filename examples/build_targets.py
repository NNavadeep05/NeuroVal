"""
Example: Build experimental targets from the lab's raw recordings.

Reads the voltage recordings in <model_path>/expdata, extracts eFEL
features for each protocol in the protocol file, and writes targets in
the features.json format (mean, std per feature) with BluePyEfe's rules.

File mapping follows the lab's select.ipynb: protocol IDthresh_587 is
recorded in expdata/*_ch3_587.dat (ch3 = voltage in mV, time in ms).
The liquid junction potential is read from config/*-spec.json.

With one recording per protocol, BluePyEfe sets every std to 1e-3, so
the means are meaningful but z-scores against these targets are not.
Use several recordings (cells or repetitions) per protocol for real stds.

Usage:
    python examples/build_targets.py <model_path> --out built_features.json
"""

import argparse
from pathlib import Path

from neuroval.data import ExperimentalData, load_trace
from neuroval.data.lab_files import find_recording, read_ljp
from neuroval.data.statistics import build_targets
from neuroval.protocols import load_bluepyopt_protocols


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="folder of one optimised model")
    parser.add_argument("--protocols-file", default="config/protocols.json",
                        help="protocol file, relative to model_path")
    parser.add_argument("--features-file", default="config/features.json",
                        help="feature names to extract (and lab means to compare)")
    parser.add_argument("--voltage-channel", default="ch3",
                        help="channel tag of the voltage files")
    parser.add_argument("--out", default="built_features.json",
                        help="output targets file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    model = Path(args.model_path)
    ljp = read_ljp(model / "config")
    lab = ExperimentalData.from_json(model / args.features_file)
    protocols = load_bluepyopt_protocols(model / args.protocols_file)

    recordings = {}

    for name in lab.protocols():
        file_path = find_recording(model / "expdata", name, args.voltage_channel)

        if file_path is not None:
            recordings[name] = [load_trace(file_path, ljp=ljp)]

    feature_names = {name: list(lab.features(name)) for name in recordings}

    targets, sizes = build_targets(recordings, protocols, feature_names)
    targets.to_json(args.out)

    print(f"Liquid junction potential: {ljp} mV")
    print(f"Protocols with recordings: {len(recordings)} of {len(lab.protocols())}")

    for name in targets.protocols():
        for feature, (mean, std) in targets.features(name).items():
            lab_mean = lab.features(name)[feature][0]
            print(
                f"  {name:<18} {feature:<32} built {mean:10.4f} "
                f"(n={sizes[name][feature]})  lab {lab_mean:10.4f}"
            )

    print(f"Targets written to {args.out}")


if __name__ == "__main__":
    main()
