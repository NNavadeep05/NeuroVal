"""
Example: Run a single-cell current-clamp simulation.
"""

import matplotlib.pyplot as plt

from neuroval.simulation.simulate import SimulationRunner


# Update this path to point to your neuron model.
MODEL_PATH = (
    r"C:\Users\kp\Desktop\KTH\humanspn\models\optimisations"
    r"\hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15"
)


def main():
    """Run a current-clamp simulation and plot the voltage trace."""

    runner = SimulationRunner(MODEL_PATH)

    runner.load_model()

    time, voltage = runner.run_simulation(
        amplitude=0.6,
    )

    plt.figure(figsize=(10, 5))
    plt.plot(time, voltage)

    plt.xlabel("Time (ms)")
    plt.ylabel("Membrane Potential (mV)")
    plt.title("Current Clamp Simulation")

    plt.grid(True)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()