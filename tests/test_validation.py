from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from neuroval.simulation.simulate import SimulationRunner


MODEL_PATH = r"C:\Users\kp\Desktop\KTH\humanspn\models\optimisations\mCP-dspn-e150917_c6_D1-manimal_1_n24_04102017_cel1"

runner = SimulationRunner(MODEL_PATH)
runner.validate_model()

print("Model validation passed.")