# NeuroVal

> ⚠️ NeuroVal is currently under active development. The API may evolve as additional electrophysiology protocols and validation metrics are introduced.

**NeuroVal** is an open-source framework for validating computational single-neuron models against experimental electrophysiological data.

It provides an end-to-end workflow that enables researchers to:

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
- **Model settings from the optimisation**: temperature (`celsius`) and `v_init` are read from the model's `config/parameters.json`, and runs use CVode as the lab's `optimize.py` did.
- **Lab protocols**: step and holding currents are loaded from the model's BluePyOpt `config/protocols.json`.
- **Experimental targets** loaded from BluePyEfe/BluePyOpt `features.json` files (`[mean, std]` per eFEL feature).
- **Z-score scoring** per feature: `z = |simulated - mean| / std` (HippoUnit, BasalUnit and the lab's `validate.py`).
- **Pass/fail** using the lab's criterion: the largest z-score must be below 3.0. Missing features are reported, not skipped.
- **Experimental recordings**: two-column text or CSV traces (such as the lab's `expdata/*.dat`) with liquid junction potential correction.
- **Target building** from recordings with BluePyEfe's rules (mean, std and n per feature across recordings).
- **Saved outputs**: `scores.json`, `model_features.json`, `experimental_features.json`, trace CSVs, plots and an HTML report.
- **All lab protocols**: the full extraction file (`config/<cell>-features.json`, 59 protocols) can be used instead of the 6 optimisation protocols.
- **Hall of Fame batch**: every exported `Cell_<n>.hoc` validated, one Python process per cell.
- **End-to-End Validation Pipeline** for automated model evaluation.
- **Example Workflows** demonstrating simulation and validation.
- **Protocol-based experiment configuration**

## Architecture

NeuroVal follows a modular architecture where each component has a single responsibility.

```
                 Experimental Data
                        │
                        ▼
                 CurrentClamp
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
- **FeatureComparator** — Computes per-feature z-scores and the validation summary.
- **CurrentClamp** — Defines a current-clamp protocol (step plus optional holding current); loads lab protocols with `CurrentClamp.from_bluepyopt()`.
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

> **Note:** The following commands assume the NeuroVal virtual environment has been activated.

### Verify Installation

```bash
python -c "import neuroval; print('NeuroVal installed successfully!')"
```

## Quick Start

> 
NeuroVal provides two example workflows to help you get started.

**Note:** NeuroVal does not include NEURON model files. Pass the folder of one optimised model (for example `.../optimisations/hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15`) to the examples. The folder must contain `checkpoints/`, `morphology/` and `config/`, with compiled mechanisms in the sibling `mechanisms/` folder.

NEURON's hoc templates are global, so validate one model per Python process.


### 1. Run a Current-Clamp Simulation

Execute:

```bash
python examples/run_simulation.py <model_path> --amplitude 0.6 --cell 0
```

This example:

- Loads a NEURON model
- Runs a configurable current-clamp simulation
- Extracts electrophysiological features
- Plots the membrane potential trace

---

### 2. Validate a Neuron Model

Execute:

```bash
python examples/validate_model.py <model_path> --cell 0
```

This example:

- Loads the model's experimental targets (`config/features.json`)
- Loads the model's protocols (`config/protocols.json`), including holding currents
- Runs every protocol in NEURON
- Extracts the target features using eFEL
- Computes a z-score for each feature
- Prints a validation report (mean |z|, max z, pass/fail, problem features)
- Plots the simulated membrane potential of each protocol

Use `--protocols IV_546 IDthresh_587` to run a subset and `--no-plot` to skip the plots. Add `--output results/` to save the JSON files, trace CSVs, plots and `report.html`, and `--overlay-recordings` to draw the lab's recordings under the model traces.

To use all 59 protocols of the lab's extraction for this cell:

```bash
python examples/validate_model.py <model_path> --targets config/160118_c7_D1-features.json --protocols-file config/160118_c7_D1-protocols.json --cvode-minstep none --output results/
```

`--cvode-minstep none` uses NEURON's default CVode step, as the lab's `variate.py` does. With the 1e-3 ms minimum step of `optimize.py`, CVode fails on two protocols (APWaveform_568 and Delta_610); their features are then reported as `simulation_failed`, as BluePyOpt scores a failed run.

---

### 3. Build Targets from Recordings

```bash
python examples/build_targets.py <model_path> --out built_features.json
```

Reads the lab's recordings in `expdata/` (voltage files `*_ch3_<n>.dat`, junction potential from `config/<cell>-spec.json`) and writes targets in the `features.json` format. For this cell the means match the lab's files exactly. With one recording per protocol, BluePyEfe's rule sets every std to 1e-3, so use several recordings per protocol for real standard deviations.

---

### 4. Validate All Hall of Fame Cells

```bash
python examples/validate_all_cells.py <model_path> --output results/ --jobs 4
```

Runs `validate_model.py` for every exported `Cell_<n>.hoc`, each in its own process, and writes `summary.json`.

## Working with Protocols

NeuroVal separates the definition of an electrophysiological experiment from its execution through protocol objects.

For example, a current-clamp experiment can be configured as:

```python
from neuroval.data import ExperimentalData
from neuroval.protocols import CurrentClamp, load_bluepyopt_protocols
from neuroval.validation import ValidationPipeline

pipeline = ValidationPipeline(model_path, cell_index=0)

# A single protocol defined by hand
results = pipeline.run(protocol=CurrentClamp(amplitude=0.6))

# The lab's protocols and targets
experimental = ExperimentalData.from_json(f"{model_path}/config/features.json")
protocols = load_bluepyopt_protocols(f"{model_path}/config/protocols.json")
results = pipeline.validate(experimental, protocols)
print(results["summary"])
```

This design keeps experiment configuration independent from the validation pipeline and provides a scalable foundation for supporting additional electrophysiological protocols in the future.


## Example Output

Running the release model (`Cell_0`) of `hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15` against its own targets:

```bash
python examples/validate_model.py <model_path> --no-plot
```

produces (shortened):

```text
============================================================
NeuroVal Validation Report
Targets: config/features.json (optimisation targets)
============================================================

IV_546
  Spikecount                       exp 0.000 +- 0.001  sim 0.000      z 0.00  ok
  decay_time_constant_after_stim   exp 2.837 +- 0.626  sim 10.417     z 12.12  ok
  voltage_base                     exp -90.575 +- 0.098  sim -91.084    z 5.21  ok
  ...

IDthresh_587
  AHP_depth_abs                    exp -63.279 +- 0.621  sim -64.749    z 2.37  ok
  mean_frequency                   exp 4.061 +- 0.406  sim 1.930      z 5.25  ok
  spike_half_width                 exp 0.922 +- 0.008  sim 0.931      z 1.23  ok
  ...

------------------------------------------------------------
Mean |z|         : 4.16
Max z            : 30.42
Passed (max z < 3.0) : False
Problem features : []
```

These are the model's optimisation targets (`config/features.json`), not the lab's population-validation targets (`valdata/`, used by `validate.py`), so failing max z < 3.0 here does not mean the model fails the lab's validation.

NeuroVal integrates with CVode (minimum step 1e-3 ms), the setting of the lab's `optimize.py`. The 37 z-scores sum to 154.0, close to the best fitness BluePyOpt recorded for this run (155.6 in `log.json`). A fixed 0.025 ms step is available with `cvode_active=False`; it gives 159.9 and changes spike-shape features most.

A feature the model cannot produce gets z = 13.13, the penalty used by the lab's `validate.py` (BluePyOpt itself uses 250).

The example also generates a membrane potential plot for visual inspection of the simulated neuronal response.

## Project Structure

```
NeuroVal/
├── examples/
│   ├── build_targets.py
│   ├── validate_all_cells.py
│   ├── run_simulation.py
│   └── validate_model.py
│
├── src/
│   └── neuroval/
│       ├── data/
│       ├── features/
│       ├── protocols/
│       ├── simulation/
│       └── validation/
│
├── tests/
│   ├── test_*.py                         (unit tests, run in CI)
│   ├── test_validation.py                (integration, needs NEUROVAL_MODEL_PATH)
│   ├── test_batch_integration.py         (integration)
│   └── test_experimental_recordings.py   (integration, needs expdata/)
│
├── README.md
└── pyproject.toml
```

- **examples/** – Ready-to-run example workflows.

Inside `src/neuroval/`:

- **data/** – Experimental targets, recording loading and BluePyEfe-style target building.
- **report/** – JSON outputs, plots and the HTML report.
- **batch.py** – Helpers for validating all Hall of Fame cells.
- **features/** – Electrophysiological feature extraction using eFEL.
- **protocols/** – Electrophysiology protocol definitions.
- **simulation/** – NEURON model execution.
- **validation/** – Feature comparison and validation pipeline.

## Roadmap

- [x] Configurable NEURON simulations
- [x] eFEL-based feature extraction
- [x] Experimental data loading (BluePyOpt features.json)
- [x] Z-score validation with the lab's max-z criterion
- [x] Lab protocols with holding current
- [x] End-to-end validation pipeline
- [x] Text/CSV recording loading and target building
- [x] Saved JSON outputs, plots and HTML report
- [x] All protocols of the lab's extraction
- [x] Validation of every exported Hall of Fame cell
- [x] Unit testing with pytest
- [x] Continuous Integration (GitHub Actions)
- [ ] NWB support
- [ ] Ramp protocols (no ramp recordings in the lab data yet)
- [ ] Population targets across cells (needs amplitude matching between cells)
- [ ] PyPI package release

## Project Status

NeuroVal is currently under active development.

### Implemented

- ✅ Configurable NEURON current-clamp simulations
- ✅ eFEL-based electrophysiological feature extraction
- ✅ Experimental targets from BluePyOpt features.json
- ✅ Z-score validation (mean |z|, max z < 3.0)
- ✅ Temperature and v_init from the model's parameters.json
- ✅ Lab protocols with holding current
- ✅ End-to-end validation pipeline
- ✅ Example workflows
- ✅ Protocol-based experiment configuration
- ✅ Recording loading and target building from the lab's expdata
- ✅ JSON outputs, plots and HTML report
- ✅ All 59 protocols of the lab's extraction
- ✅ Batch validation of exported Hall of Fame cells

### Planned

- 📋 Population targets across cells
- 📋 NWB support
- 📋 PyPI package release

## Acknowledgements

NeuroVal builds upon several excellent open-source scientific software projects, including:

- NEURON
- eFEL (Electrophys Feature Extraction Library)

The framework is being developed as an open-source project for computational neuroscience model validation.







