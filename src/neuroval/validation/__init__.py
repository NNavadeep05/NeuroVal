def __init__(self, model_path):
    """Initialize the validation pipeline."""

    self.runner = SimulationRunner(model_path)
    self.extractor = FeatureExtractor()
    self.comparator = FeatureComparator()