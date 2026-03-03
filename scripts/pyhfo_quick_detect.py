#!/usr/bin/env python
"""
Command-line equivalent of the PyHFO Quick Detection dialog.

Replicates the same operations and default parameters as the GUI's
HFOQuickDetector, without requiring a display or Qt event loop.

Usage:
    python pyhfo_quick_detect.py recording.edf
    python pyhfo_quick_detect.py recording.edf --detector MNI --classify
    python pyhfo_quick_detect.py recording.edf --classify --device cuda:0 --xlsx
"""
# From the Quick Detection UI dialog
# Filters:
# Pass Band: 80
# Pass Band ripple: 0.5
# Stop Band: 500
# Stop Band Ripple 93

# STE Detector default settings:
# Min Oscillations: 6 secs
# RMS Threshold: 5
# RMS Window: 0.003 ms
# Epoch Length: 600
# Min Window: 0.006 ms
# Peak Threshold: 3
# Min Gap 0.01 ms

# Defaults for use default GPU Model: use spkHFO use eHFO
# Artifact Model: pyHFO/ckpt/model_a.tar
# spkHFO Model:   pyHFO/ckpt/model_s.tar
# eHFO Model :    pyHFO/ckpt/mode_e.tar
# ignore 1 sec before 1 sec after
# device: cuda:0
# Batch Size: 323
# my settings
# save as .npz and .xlsx saved to same directory as the edf file

import argparse
import os
import sys
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(
        description="PyHFO Quick Detection CLI - runs the same pipeline as the Quick Detection dialog.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        help="Path to recording file (.edf, .eeg, .vhdr, .vmrk)",
    )

    # --- Detector ---
    parser.add_argument(
        "--detector",
        choices=["HIL", "STE", "MNI"],
        default="STE",
        help="Detection algorithm",
    )

    # --- Filter (ParamFilter defaults) ---
    filt = parser.add_argument_group("filter parameters")
    filt.add_argument("--fp", type=float, default=80, help="Passband frequency (Hz)")
    filt.add_argument("--fs", type=float, default=500, help="Stopband frequency (Hz)")
    filt.add_argument("--rp", type=float, default=0.5, help="Passband ripple (dB)")
    filt.add_argument("--rs", type=float, default=93, help="Stopband attenuation (dB)")

    # --- HIL (ParamHIL(2000) defaults) ---
    hil = parser.add_argument_group("HIL detector parameters")
    hil.add_argument(
        "--hil-epoch-time", type=float, default=3600, help="Epoch time (s)"
    )
    hil.add_argument("--hil-sd-threshold", type=float, default=5, help="SD threshold")
    hil.add_argument(
        "--hil-min-window", type=float, default=0.01, help="Minimum window (s)"
    )

    # --- STE (ParamSTE(2000) defaults) ---
    ste = parser.add_argument_group("STE detector parameters")
    ste.add_argument(
        "--ste-rms-window", type=float, default=3e-3, help="RMS window (s)"
    )
    ste.add_argument(
        "--ste-min-window", type=float, default=6e-3, help="Minimum window (s)"
    )
    ste.add_argument("--ste-min-gap", type=float, default=10e-3, help="Minimum gap (s)")
    ste.add_argument(
        "--ste-epoch-len", type=float, default=600, help="Epoch length (s)"
    )
    ste.add_argument(
        "--ste-min-osc", type=float, default=6, help="Minimum oscillations"
    )
    ste.add_argument("--ste-rms-thres", type=float, default=5, help="RMS threshold")
    ste.add_argument("--ste-peak-thres", type=float, default=3, help="Peak threshold")

    # --- MNI (ParamMNI(200) defaults, percentages as in GUI) ---
    mni = parser.add_argument_group("MNI detector parameters")
    mni.add_argument("--mni-epoch-time", type=float, default=10, help="Epoch time (s)")
    mni.add_argument("--mni-epo-chf", type=float, default=60, help="Epoch CHF")
    mni.add_argument(
        "--mni-per-chf", type=float, default=95, help="CHF percentage (%%)"
    )
    mni.add_argument(
        "--mni-min-win", type=float, default=10e-3, help="Minimum window (s)"
    )
    mni.add_argument("--mni-min-gap", type=float, default=10e-3, help="Minimum gap (s)")
    mni.add_argument(
        "--mni-thrd-perc", type=float, default=99.9999, help="Threshold percentage (%%)"
    )
    mni.add_argument(
        "--mni-base-seg", type=float, default=125e-3, help="Baseline segment (s)"
    )
    mni.add_argument("--mni-base-shift", type=float, default=0.5, help="Baseline shift")
    mni.add_argument(
        "--mni-base-thrd", type=float, default=0.67, help="Baseline threshold"
    )
    mni.add_argument(
        "--mni-base-min", type=float, default=5, help="Baseline minimum time (s)"
    )

    # --- Classifier ---
    cls = parser.add_argument_group("classifier parameters")
    cls.add_argument(
        "--classify", action="store_true", help="Run AI classifier after detection"
    )
    cls.add_argument(
        "--device",
        default=None,
        help="Classifier device, e.g. 'cpu' or 'cuda:0' (default: auto)",
    )
    cls.add_argument("--batch-size", type=int, default=32, help="Classifier batch size")
    cls.add_argument(
        "--no-spikes", action="store_true", help="Skip spike (spkHFO) classification"
    )
    cls.add_argument(
        "--ignore-seconds-before",
        type=float,
        default=1.0,
        help="Seconds to ignore at start of recording for classification",
    )
    cls.add_argument(
        "--ignore-seconds-after",
        type=float,
        default=1.0,
        help="Seconds to ignore at end of recording for classification",
    )

    # --- Output ---
    out = parser.add_argument_group("output")
    out.add_argument("--xlsx", action="store_true", help="Save results as .xlsx")
    out.add_argument("--npz", action="store_true", help="Save results as .npz")
    out.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: same as input file)",
    )

    # --- Processing ---
    parser.add_argument("--n-jobs", type=int, default=4, help="Number of parallel jobs")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Default to both output formats when neither is specified
    if not args.xlsx and not args.npz:
        args.xlsx = True
        args.npz = True

    input_file = os.path.abspath(args.input_file)
    if not os.path.exists(input_file):
        print(f"Error: file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Build output base path
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.join(output_dir, Path(input_file).stem)
    else:
        base = str(Path(input_file).with_suffix(""))

    # ---- Heavy imports after arg parsing so --help stays fast ----
    from pyhfo2app.hfo_app import HFO_App
    from pyhfo2app.param.param_filter import ParamFilter
    from pyhfo2app.param.param_detector import ParamDetector

    # 1. Create backend and load recording
    backend = HFO_App()
    backend.n_jobs = args.n_jobs

    print(f"Loading {input_file} ...")
    backend.load_edf(input_file)
    print(f"  Sample freq : {backend.sample_freq} Hz")
    print(f"  Channels    : {len(backend.channel_names)}")
    print(f"  Samples     : {backend.eeg_data.shape[1]}")

    # 2. Filter
    filter_param = ParamFilter(fp=args.fp, fs=args.fs, rp=args.rp, rs=args.rs)
    print(f"Filtering (passband={args.fp} Hz, stopband={args.fs} Hz) ...")
    backend.filter_eeg_data(filter_param)
    print("  Filtering complete.")

    # 3. Build detector parameters
    #    sample_freq / pass_band / stop_band are overridden inside
    #    backend.set_detector() to match the actual recording, so the
    #    placeholder values used here are consistent with the GUI code.
    if args.detector == "HIL":
        param_dict = {
            "sample_freq": backend.sample_freq,
            "pass_band": int(filter_param.fp),
            "stop_band": int(filter_param.fs),
            "epoch_time": args.hil_epoch_time,
            "sd_threshold": args.hil_sd_threshold,
            "min_window": args.hil_min_window,
            "n_jobs": args.n_jobs,
        }
        detector_params = {"detector_type": "HIL", "detector_param": param_dict}
    elif args.detector == "STE":
        param_dict = {
            "sample_freq": backend.sample_freq,
            "pass_band": int(filter_param.fp),
            "stop_band": int(filter_param.fs),
            "rms_window": args.ste_rms_window,
            "min_window": args.ste_min_window,
            "min_gap": args.ste_min_gap,
            "epoch_len": args.ste_epoch_len,
            "min_osc": args.ste_min_osc,
            "rms_thres": args.ste_rms_thres,
            "peak_thres": args.ste_peak_thres,
            "n_jobs": args.n_jobs,
        }
        detector_params = {"detector_type": "STE", "detector_param": param_dict}
    elif args.detector == "MNI":
        param_dict = {
            "sample_freq": backend.sample_freq,
            "pass_band": int(filter_param.fp),
            "stop_band": int(filter_param.fs),
            "epoch_time": args.mni_epoch_time,
            "epo_CHF": args.mni_epo_chf,
            "per_CHF": args.mni_per_chf / 100,
            "min_win": args.mni_min_win,
            "min_gap": args.mni_min_gap,
            "thrd_perc": args.mni_thrd_perc / 100,
            "base_seg": args.mni_base_seg,
            "base_shift": args.mni_base_shift,
            "base_thrd": args.mni_base_thrd,
            "base_min": args.mni_base_min,
            "n_jobs": args.n_jobs,
        }
        detector_params = {"detector_type": "MNI", "detector_param": param_dict}

    detector_param = ParamDetector.from_dict(detector_params)

    # 4. Detect
    print(f"Detecting HFOs with {args.detector} ...")
    backend.set_detector(detector_param)
    backend.detect_biomarker()
    n_events = len(backend.event_features.starts) if backend.event_features else 0
    print(f"  Detection complete — {n_events} events found.")

    # 5. Classify (mirrors quick_detection.py _classify behaviour)
    if args.classify:
        if n_events == 0:
            print("Skipping classification — no events to classify.")
        else:
            import torch

            if args.device is None:
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            else:
                device = args.device

            print(f"Setting up classifier (device={device}) ...")

            # set_default_*_classifier creates ParamClassifier + Classifier instance
            if "cuda" in device and torch.cuda.is_available():
                backend.set_default_gpu_classifier()
            else:
                backend.set_default_cpu_classifier()

            if args.batch_size != 32:
                backend.param_classifier.batch_size = args.batch_size
                backend.classifier.batch_size = args.batch_size

            # Load model weights (HuggingFace cards set by the default above)
            backend.set_classifier(backend.param_classifier)

            print(
                f"  Classifying artifacts "
                f"(ignore {args.ignore_seconds_before}s before, "
                f"{args.ignore_seconds_after}s after) ..."
            )
            backend.classify_artifacts(
                [args.ignore_seconds_before, args.ignore_seconds_after]
            )

            if not args.no_spikes:
                print("  Classifying spikes ...")
                backend.classify_spikes()

            print("  Classification complete.")

    # 6. Export
    if args.xlsx:
        xlsx_path = base + ".xlsx"
        print(f"Saving {xlsx_path} ...")
        backend.export_excel(xlsx_path)

    if args.npz:
        npz_path = base + ".npz"
        print(f"Saving {npz_path} ...")
        backend.export_app(npz_path)

    print("Done.")


if __name__ == "__main__":
    main()
