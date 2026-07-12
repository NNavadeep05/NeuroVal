from pathlib import Path

from neuroval.data import ExperimentalData
from neuroval.validation.pipeline import ValidationPipeline


MODEL_PATH = (
    r"C:\Users\kp\Desktop\KTH\humanspn\models\optimisations"
    r"\hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15"
)

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "data"
    / "experimental_features.json"
)


def test_validation_pipeline():
    """Run the complete NeuroVal validation pipeline."""

    experimental = ExperimentalData.from_json(
        DATA_PATH
    )

    pipeline = ValidationPipeline(MODEL_PATH)

    results = pipeline.validate(
        experimental.features,
        amplitude=0.6,
    )

    assert "features" in results
    assert "comparison" in results
    assert "score" in results

    assert results["score"] > 90

    assert "Spikecount" in results["comparison"]