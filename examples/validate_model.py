"""
Example: Validate a neuron model against experimental data.
"""

import matplotlib.pyplot as plt

from neuroval.data import ExperimentalData
from neuroval.validation.pipeline import ValidationPipeline


# Update this path to point to your neuron model.
MODEL_PATH = (
    r"C:\Users\kp\Desktop\KTH\humanspn\models\optimisations"
    r"\hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15"
)


def main():
    """Run a validation experiment."""

    experimental = ExperimentalData.from_json(
        "examples/data/experimental_features.json"
    )

    pipeline = ValidationPipeline(MODEL_PATH)

    results = pipeline.validate(
        experimental.features,
        amplitude=0.6,
    )

    print("=" * 40)
    print("NeuroVal Validation Report")
    print("=" * 40)

    print(
        f"\nOverall Validation Score : "
        f"{results['score']:.2f} / 100"
    )

    for feature, values in results["comparison"].items():

        print(f"\n{feature}")

        print(
            f"  Experimental   : "
            f"{values['experimental']}"
        )

        print(
            f"  Simulated      : "
            f"{values['simulated']}"
        )

        print(
            f"  Absolute Error : "
            f"{values['absolute_error']:.3f}"
        )

        print(
            f"  Relative Error : "
            f"{values['relative_error']:.2f}%"
        )

    plt.figure(figsize=(10, 5))
    plt.plot(
        results["time"],
        results["voltage"],
    )

    plt.xlabel("Time (ms)")
    plt.ylabel("Membrane Potential (mV)")
    plt.title("Validation Simulation")

    plt.grid(True)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()