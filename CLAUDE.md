# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyHFO is a PyQt5 desktop application for deep learning-based High-Frequency Oscillation (HFO) analysis in EEG/iEEG data. It supports multiple detection algorithms (STE, MNI, HIL), AI-powered classification (artifact, spike, eHFO), and interactive annotation. It reads EDF and BrainVision formats.

## Running the Application
Note: the current version is limitted to use python 3.9 - 3.11 because PyQt5 is
not supported beyond version python 3.11.

```bash
# Setup (Python 3.9; 3.10 or 3.11 are also acceptable)
conda create -n pyhfo python=3.9
pip install -e .          # recommended (uses pyproject.toml)
# OR: pip install -r requirements.txt

# Run
python main.py
# OR: pyhfo              # uses the installed entry point
```

### Tool install (pyhfo command)

Python in range of 3.9 - 3.11 is required — other versions produce segfaults due
to incompatible PyQt5 binary wheels.

```bash
uv tool install --python 3.9 .          # recommended
# OR: this might work:  pipx install --python python3.9 .
pyhfo
```

### Testing

```bash
pytest tests/               # run locally
tox                          # run across Python 3.9–3.11 (requires tox-uv)
tox -e py39                  # single version
```

## Architecture

**MVC pattern** with four parallel component groups (main window, waveform plot, mini plot, annotation), each in `pyhfo2app/models/`, `pyhfo2app/views/`, `pyhfo2app/controllers/`.

**Key data flow:**
1. `main.py` → `pyhfo2app.app.py`
2  `pyhfo2app.app.py` -> `pyhfo2app/ui/main_window.py` (MainWindow) → creates MVC components
3. `MainWindowController` orchestrates biomarker-specific windows (HFO, Spindle, Spike)
4. `MainWindowModel` (`pyhfo2app/models/main_window_model.py`, ~77KB) holds most application state and delegates to backends

**Backend processing (`pyhfo2app/`):**
- `hfo_app.py` / `spindle_app.py` — Core detection backends. Load EDF, filter, detect, extract features, classify, export NPZ
- `classifer.py` — DL classification (artifact/spike/eHFO) using ResNet18 models from `pyhfo2app/dl_models/`
- `hfo_feature.py` / `spindle_feature.py` — Feature containers tracking events, predictions, annotations

**Parameters (`pyhfo2app/param/`):**
- `param_detector.py` — ParamSTE, ParamMNI, ParamHIL, ParamYASA (detector configs)
- `param_filter.py` — ParamFilter (80-500Hz default), ParamFilterSpindle (1-30Hz)
- `param_classifier.py` — ParamClassifier, ParamModel, ParamPreprocessing

**Utilities (`pyhfo2app/utils/`):**
- `utils_io.py` — EDF reading, NPZ export, channel sorting
- `utils_filter.py` — Chebyshev type-II bandpass filter design
- `utils_detector.py` — Wraps HFODetector library detectors
- `utils_inference.py` — Model checkpoint loading, batch GPU/CPU inference
- `utils_feature.py` — Spectrogram computation, waveform extraction, parallel processing
- `utils_gui.py` — Thread workers, stdout/stderr capture, custom widgets

**DL Models (`pyhfo2app/dl_models/`):**
- `modeling_neuralcnn.py` — NeuralCNNModel/NeuralCNNForImageClassification (HuggingFace PreTrainedModel)
- `configuration_neuralcnn.py` — ResnetConfig (HuggingFace PretrainedConfig)
- Pretrained checkpoints in `ckpt/` (model_a, model_s, model_e)

**UI (`pyhfo2app/ui/`):**
- `main_window.py` — Main application window
- `quick_detection.py` — Quick detection dialog
- `channels_selection.py` / `bipolar_channel_selection.py` — Channel selection dialogs
- `plot_waveform.py` — pyqtgraph-based waveform plotting

## Key Dependencies

- **PyQt5** (5.15.9) + **pyqtgraph** (0.13.3) — GUI
- **mne** — EEG file I/O
- **HFODetector** — Detection algorithms (STE, MNI, HIL)
- **torch** / **torchvision** / **transformers** — DL classification
- **yasa** — Spindle detection
- **numpy** (1.26.4), **scipy**, **pandas** — Scientific computing

## macOS Packaging

`setup_macos.py` uses py2applet to build a standalone .app bundle. `macos_package.py` is a secondary packaging script.
