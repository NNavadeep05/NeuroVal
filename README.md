# NeuroVal

> NeuroVal v1 is complete. No further development is planned.

**NeuroVal** is a lightweight Python framework for validating single-neuron models against experimental electrophysiology data.

It takes an optimised model (a BluePyOpt `Cell_<n>.hoc` export with its morphology and mechanisms), runs the same current-clamp protocols as the experiment, and checks how close the model's response is to the recorded cells.

It provides an end-to-end workflow to:

- Run **NEURON** single-cell models with the settings used during optimisation.
- Extract electrophysiological features using **eFEL**.
- Load experimental targets, or build them from raw recordings.
- Score every feature with a z-score and give a pass/fail result.
- Save the results as JSON, CSV, plots and an HTML report.
- Validate every exported Hall of Fame cell in one command.

NeuroVal is built to be **modular** and **reproducible**. It was developed and tested with striatal dSPN models.

## Features

- **NEURON simulations** with the model's own temperature and initial voltage (read from `config/parameters.json`) and CVode integration, as in the lab's optimisation.
- **Lab protocols** loaded from BluePyOpt `protocols.json` files, including the holding current.
- **eFEL feature extraction** with the original eFEL feature names.
- **Experimental targets** from `features.json` files (`[mean, std]` per feature).
- **Recording loading** for two-column text or CSV traces, with liquid junction potential correction.
- **Target building** from recordings (mean, std and number of recordings per feature).
- **Z-score scoring** per feature: `z = |model - mean| / std`.
- **Pass/fail result**: the model passes when the largest z-score is below 3.0. Features the model cannot produce are reported, not skipped.
- **Saved outputs**: `scores.json`, `model_features.json`, `experimental_features.json`, trace CSVs, plots and `report.html`.
- **Batch validation** of every exported Hall of Fame cell, one Python process per cell.
- **Unit and integration tests** with GitHub Actions CI.

## Architecture

NeuroVal follows a modular architecture where each component has a single responsibility.

```
     Recordings / features.json        protocols.json
                 │                            │
                 ▼                            ▼
          ExperimentalData              CurrentClamp
                 │                            │
                 └──────────────┬─────────────┘
                                ▼
                       ValidationPipeline
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
  SimulationRunner       FeatureExtractor     FeatureComparator
          │                     │                     │
          ▼                     ▼                     ▼
       NEURON                 eFEL                z-scores
                                                      │
                                                      ▼
                                                   Report
```

### Components

- **SimulationRunner**: loads a `Cell_<n>.hoc` model, applies the model's settings and runs current-clamp simulations.
- **CurrentClamp**: a current-clamp protocol (test step plus optional holding current). Lab protocols load with `load_bluepyopt_protocols()`.
- **FeatureExtractor**: extracts eFEL features from a voltage trace.
- **ExperimentalData**: loads and checks experimental targets.
- **load_trace / build_targets**: load raw recordings and build targets from them.
- **FeatureComparator**: computes the z-score of each feature and the summary (mean |z|, max z, pass/fail).
- **ValidationPipeline**: runs the whole workflow, from simulation to scores.
- **save_results**: writes the JSON files, trace CSVs, plots and HTML report.

## Installation

### Clone the Repository

```bash
git clone https://github.com/NNavadeep05/NeuroVal.git
cd NeuroVal
```

### Create a Virtual Environment

NeuroVal was developed with Python 3.11.

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

**Linux / macOS**

```bash
pip install -e .
```

**Windows**

NEURON cannot be installed with pip on Windows. Install it with the official NEURON installer (NeuroVal was tested with NEURON 9.0.1), then point Python to it and install the other dependencies:

```bat
set PYTHONPATH=C:\nrn\lib\python
pip install --no-deps -e .
pip install numpy matplotlib pandas efel pytest
```

> **Note:** The following commands assume the virtual environment is active.

### Verify Installation

```bash
python -c "import neuroval; from neuron import h; print('NeuroVal installed successfully!')"
```

## Quick Start

NeuroVal does not include model files or experimental data. The examples take the folder of one optimised model, laid out like the lab's BluePyOpt optimisation folders:

```
<model_path>/
├── checkpoints/Cell_<n>.hoc     exported models
├── morphology/<cell>.swc        one morphology file
├── config/parameters.json       celsius and v_init
├── config/features.json         experimental targets
├── config/protocols.json        stimulation protocols
└── expdata/                     raw recordings (optional)
```

Compiled mechanisms (`nrnmech.dll` on Windows, built with `mknrndll`) are expected in the `mechanisms/` folder next to the model folder.

NEURON keeps hoc templates global, so NeuroVal validates one model per Python process.

### 1. Run a Current-Clamp Simulation

```bash
python examples/run_simulation.py <model_path> --amplitude 0.6 --cell 0
```

This example:

- Loads a NEURON model
- Runs a current-clamp simulation
- Extracts electrophysiological features
- Plots the membrane potential trace

---

### 2. Validate a Neuron Model

```bash
python examples/validate_model.py <model_path> --cell 0 --output results/
```

This example:

- Loads the experimental targets (`config/features.json`) and protocols (`config/protocols.json`)
- Runs every protocol in NEURON
- Extracts the target features using eFEL
- Computes a z-score for each feature
- Prints a validation report (mean |z|, max z, pass/fail, problem features)
- Saves the JSON files, trace CSVs, plots and `report.html` in `results/`

Useful options:

- `--protocols IV_546 IDthresh_587`: run only some protocols
- `--targets` and `--protocols-file`: use other target and protocol files, for example the lab's full extraction with 59 protocols
- `--overlay-recordings`: draw the recorded traces under the model traces
- `--cvode-minstep none`: use NEURON's default CVode step (needed for protocols with very sharp steps)
- `--no-plot`: skip the interactive plots

---

### 3. Build Targets from Recordings

```bash
python examples/build_targets.py <model_path> --out built_features.json
```

Reads the recordings in `expdata/`, applies the liquid junction potential from `config/<cell>-spec.json`, and writes targets in the `features.json` format.

---

### 4. Validate All Hall of Fame Cells

```bash
python examples/validate_all_cells.py <model_path> --output results/ --jobs 4
```

Validates every exported `Cell_<n>.hoc`, each in its own process, and writes a `summary.json` for all cells.

## Working with Protocols

NeuroVal separates the definition of an experiment (the protocol) from its execution (the pipeline).

```python
from neuroval.data import ExperimentalData
from neuroval.protocols import CurrentClamp, load_bluepyopt_protocols
from neuroval.report import save_results
from neuroval.validation import ValidationPipeline

pipeline = ValidationPipeline(model_path, cell_index=0)

# A single protocol defined by hand
results = pipeline.run(protocol=CurrentClamp(amplitude=0.6, holding=0.0009))

# The lab's protocols and targets
experimental = ExperimentalData.from_json(f"{model_path}/config/features.json")
protocols = load_bluepyopt_protocols(f"{model_path}/config/protocols.json")
results = pipeline.validate(experimental, protocols)

print(results["summary"])
save_results(results, "results/")
```

Hand-written protocols and protocols loaded from the lab's files are the same `CurrentClamp` objects, so the pipeline treats them the same way.

## Example Output

Validating the release model (`Cell_0`) of the dSPN model `hPu-dspn-e160118_c7_D1-mAB5_porta80A_cel15` against its targets:

```bash
python examples/validate_model.py <model_path> --no-plot --output results/
```

produces (shortened):

```text
============================================================
NeuroVal Validation Report
Targets: config/features.json
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

and a `results/` folder with:

```
results/
├── report.html                  summary, feature tables and plots
├── scores.json                  z-score and status of every feature
├── model_features.json          feature values of the model
├── experimental_features.json   targets used
├── plots/traces.png             model trace for each protocol
├── plots/z_scores.png           z-score of each feature, with the 3.0 line
└── traces/<protocol>.csv        simulated voltage traces
```

Validating all exported cells of the same model:

| Cell | Mean abs z | Max z | Passed |
|---|---|---|---|
| Cell_0 | 4.16 | 30.42 | No |
| Cell_5 | 4.46 | 31.70 | No |
| Cell_6 | 4.49 | 33.07 | No |
| Cell_9 | 4.72 | 32.68 | No |

Checks done with the lab's model:

- Targets rebuilt from the raw recordings match the lab's target files exactly (37 of 37 features, and 532 of 532 in the full extraction).
- The sum of the 37 z-scores for `Cell_0` (154.0) is close to the fitness BluePyOpt recorded for this model during optimisation (155.6).

The targets above are the ones the model was optimised against. The lab accepts models against a separate set of population targets, so failing max z < 3.0 here does not mean the model is rejected.

## Project Structure

```
NeuroVal/
├── examples/
│   ├── run_simulation.py
│   ├── validate_model.py
│   ├── build_targets.py
│   └── validate_all_cells.py
│
├── src/
│   └── neuroval/
│       ├── data/
│       ├── features/
│       ├── protocols/
│       ├── report/
│       ├── simulation/
│       ├── validation/
│       └── batch.py
│
├── tests/
│
├── .github/workflows/ci.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

- **examples/**: ready-to-run workflows.
- **tests/**: unit tests (run in CI) and integration tests (need a model folder).

Inside `src/neuroval/`:

- **data/**: experimental targets, recording loading and target building.
- **features/**: feature extraction with eFEL.
- **protocols/**: protocol definitions and the loader for lab protocol files.
- **report/**: JSON outputs, plots and the HTML report.
- **simulation/**: NEURON model loading and simulation.
- **validation/**: z-score comparison and the validation pipeline.
- **batch.py**: helpers for validating all Hall of Fame cells.

## Running the Tests

Unit tests do not need any model files:

```bash
python -m pytest tests
```

Integration tests run the real model. Set `NEUROVAL_MODEL_PATH` to a model folder first (they take about 10 minutes):

```bash
export NEUROVAL_MODEL_PATH=<model_path>    # Windows: set NEUROVAL_MODEL_PATH=<model_path>
python -m pytest tests
```

## Project Status

NeuroVal v1 is complete and no further development is planned.

### Implemented

- ✅ Model loading with the optimisation settings (temperature, v_init, CVode)
- ✅ Lab protocols with holding current
- ✅ eFEL feature extraction
- ✅ Z-score validation and pass/fail result
- ✅ Recording loading and target building
- ✅ JSON outputs, plots and HTML report
- ✅ Batch validation of exported Hall of Fame cells
- ✅ Unit and integration tests, CI

### Known Limitations

- Targets come from one recorded cell, not a population of cells.
- Only exported `Cell_<n>.hoc` files can be validated (4 of the 10 Hall of Fame sets in the test model).
- One model per Python process, because NEURON's hoc templates are global.
- Morphology folder and file names must not contain spaces.

## Acknowledgements

NeuroVal builds on:

- NEURON
- eFEL (Electrophys Feature Extraction Library)

Its design borrows ideas from HippoUnit, BasalUnit, BluePyEfe and BluePyOpt.

NeuroVal was developed during a summer research internship at KTH Royal Institute of Technology. The models and experimental data used for testing belong to the lab and are not included in this repository.

## Author

**Navadeep Nandedapu**
