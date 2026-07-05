# NeuroVal

NeuroVal is a lightweight framework for electrophysiological validation of single-neuron models.

The framework compares simulated neuronal responses against experimental recordings by:

- Running NEURON HOC models
- Extracting electrophysiological features using eFEL
- Comparing model features with experimental data
- Computing validation scores
- Generating validation reports

The initial implementation focuses on direct pathway spiny projection neurons (dSPNs) using publicly available datasets, with the design intended to support additional basal ganglia cell types in the future.

## Project Status

🚧 Under active development.

## Planned Workflow

```
Experimental Recordings
        │
        ▼
Feature Extraction (eFEL)
        │
        ▼
Experimental Statistics

        +

NEURON Simulation (HOC)

        │
        ▼
Model Features (eFEL)

        │
        ▼
Validation

        │
        ▼
Report Generation
```