"""
Example: Validate a neuron model against experimental features.
"""

import matplotlib.pyplot as plt

from neuroval.validation.pipeline import ValidationPipeline


# Update this path to point to your neuron model.
MODEL_PATH = (
    r"C:\Users\kp\Desktop\KTH\humanspn\models\optimisations"
    r"\hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15"
)


def main():
    """Run a validation experiment."""

    pipeline = ValidationPipeline(MODEL_PATH)

    experimental = {
        "Spikecount": 12,
        "RestingPotential": -90,
        "Mean_AP_amplitude": 71,
        "Mean_AP_width": 1.0,
    }

    results = pipeline.validate(
        experimental,
        amplitude=0.6,
    )

    print("=" * 40)
    print("NeuroVal Validation Report")
    print("=" * 40)

    for feature, values in results["comparison"].items():

        print(f"\n{feature}")

        print(f"  Experimental : {values['experimental']}")
        print(f"  Simulated    : {values['simulated']}")
        print(f"  Error        : {values['error']:.3f}")

    plt.figure(figsize=(10, 5))
    plt.plot(results["time"], results["voltage"])

    plt.xlabel("Time (ms)")
    plt.ylabel("Membrane Potential (mV)")
    plt.title("Validation Simulation")

    plt.grid(True)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()