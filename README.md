# NeuroVal

**NeuroVal** is an open-source framework for validating computational single-neuron models against experimental electrophysiological data.

It provides an end-to-end validation pipeline that enables researchers to:

- Run **NEURON** single-cell models.
- Extract electrophysiological features using **eFEL**.
- Load experimental feature datasets.
- Compare simulated and experimental responses.
- Compute quantitative validation metrics.
- Generate validation reports.

NeuroVal is designed to be **modular**, **reproducible**, and **extensible**, making it suitable for computational neuroscience research and model evaluation.

## Features

Current capabilities include:

- **Configurable Current-Clamp Simulations** using NEURON.
- **Automatic Electrophysiological Feature Extraction** using eFEL.
- **Experimental Feature Loading** from JSON datasets.
- **Feature-by-Feature Comparison** between simulated and experimental data.
- **Absolute and Relative Error Computation** for each electrophysiological feature.
- **Overall Validation Score** based on feature comparison.
- **End-to-End Validation Pipeline** for automated model evaluation.
- **Example Workflows** demonstrating simulation and validation.

## Architecture

NeuroVal follows a modular architecture where each component has a single responsibility.

```
                 Experimental Data
                        │
                        ▼
               ValidationPipeline
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
SimulationRunner  FeatureExtractor  FeatureComparator
        │                                │
        ▼                                ▼
     NEURON                     Validation Score
```

### Components

- **SimulationRunner** — Loads and runs NEURON single-cell simulations.
- **FeatureExtractor** — Extracts electrophysiological features from voltage traces using eFEL.
- **ExperimentalData** — Loads and validates experimental feature datasets.
- **FeatureComparator** — Compares simulated and experimental features and computes validation metrics.
- **ValidationPipeline** — Coordinates the complete validation workflow from simulation to report generation.

## Installation

### Clone the Repository

```bash
git clone https://github.com/NNavadeep05/NeuroVal.git
cd NeuroVal
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### Install NeuroVal

```bash
pip install -e .
```

### Verify Installation

```bash
python -c "import neuroval; print('NeuroVal installed successfully!')"
```

## Quick Start

NeuroVal provides two example workflows.

### 1. Run a Current-Clamp Simulation

Execute:

```bash
python examples/run_simulation.py
```

This example:

- loads a NEURON model
- runs a configurable current-clamp simulation
- extracts electrophysiological features
- plots the membrane potential trace

---

### 2. Validate a Neuron Model

Execute:

```bash
python examples/validate_model.py
```

This example:

- loads experimental feature data
- runs a NEURON simulation
- extracts electrophysiological features using eFEL
- compares simulated and experimental features
- computes an overall validation score
- generates a validation report
- plots the simulated membrane potential

## Example Output

Running

```bash
python examples/validate_model.py
```

produces a validation report similar to:

```text
========================================
NeuroVal Validation Report
========================================

Overall Validation Score : 96.96 / 100

Spikecount
  Experimental   : 12
  Simulated      : 13
  Absolute Error : 1.000
  Relative Error : 8.33%

RestingPotential
  Experimental   : -90
  Simulated      : -90.828
  Absolute Error : 0.828
  Relative Error : 0.92%

Mean_AP_amplitude
  Experimental   : 71
  Simulated      : 72.001
  Absolute Error : 1.001
  Relative Error : 1.41%

Mean_AP_width
  Experimental   : 1.0
  Simulated      : 0.985
  Absolute Error : 0.015
  Relative Error : 1.50%
```

The example also generates a membrane potential plot for visual inspection of the simulated neuronal response.

## Project Structure

```
NeuroVal/
├── examples/
│   ├── data/
│   ├── run_simulation.py
│   └── validate_model.py
│
├── src/
│   └── neuroval/
│       ├── data/
│       ├── features/
│       ├── simulation/
│       └── validation/
│
├── README.md
├── pyproject.toml
└── LICENSE
```

- **examples/** – Ready-to-run example workflows.

Inside `src/neuroval/`:

- **data/** – Experimental data loading utilities.
- **features/** – Electrophysiological feature extraction using eFEL.
- **simulation/** – NEURON model execution.
- **validation/** – Feature comparison and validation pipeline.

## Roadmap

- [x] Configurable NEURON simulations
- [x] eFEL-based feature extraction
- [x] Experimental data loading (JSON)
- [x] Feature comparison
- [x] Validation scoring
- [x] End-to-end validation pipeline
- [ ] CSV experimental data support
- [ ] HTML/PDF validation reports
- [ ] Unit testing with pytest
- [ ] Continuous Integration (GitHub Actions)
- [ ] NWB support
- [ ] Multiple stimulation protocols
- [ ] PyPI package release

## Project Status

NeuroVal is currently under active development.

### Implemented

- ✅ Configurable NEURON current-clamp simulations
- ✅ eFEL-based electrophysiological feature extraction
- ✅ Experimental data loading from JSON
- ✅ Feature comparison
- ✅ Absolute & relative error computation
- ✅ Validation scoring
- ✅ End-to-end validation pipeline
- ✅ Example workflows

### In Progress

- 🚧 Documentation
- 🚧 Unit testing
- 🚧 HTML validation reports

### Planned

- 📋 CSV experimental data support
- 📋 NWB support
- 📋 Multiple stimulation protocols
- 📋 PyPI package release

## Acknowledgements

NeuroVal builds upon several excellent open-source scientific software projects, including:

- NEURON
- eFEL (Electrophys Feature Extraction Library)

The framework is being developed as an open-source project for computational neuroscience model validation.







