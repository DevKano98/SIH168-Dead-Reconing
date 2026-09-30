from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .data import PairedRunData, RunPair, audit_pairs, discover_synchronized_pairs, load_paired_run
from .features import FEATURE_NAMES, linear_acceleration, summarize_window


WINDOW_SAMPLES = 20
STRIDE_SAMPLES = 10


def _windows(run: PairedRunData, max_windows: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    imu = np.concatenate([linear_acceleration(run.accel, run.gravity), run.gyro], axis=1)
    indices = np.arange(WINDOW_SAMPLES - 1, len(imu), STRIDE_SAMPLES)
    if max_windows is not None and len(indices) > max_windows:
        selected = np.linspace(0, len(indices) - 1, max_windows, dtype=int)
        indices = indices[selected]
    features = np.stack([summarize_window(imu[i - WINDOW_SAMPLES + 1 : i + 1]) for i in indices])
    # The S/V files can drift in timestamp even when row counts match. Phone
    # GNSS speed is aligned to the phone IMU clock and behaves as m/s despite
    # its Kmh header. It is withheld during held-out outage inference.
    speed = run.phone_speed_raw[indices].astype(np.float32)
    stopped = (speed < 0.35).astype(np.int8)
    return features, speed, stopped


def _load_group(pairs: list[RunPair], max_windows_per_run: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    xs, ys, stops, used = [], [], [], []
    for pair in pairs:
        if not pair.equal_length:
            continue
        try:
            run = load_paired_run(pair)
            x, y, stop = _windows(run, max_windows_per_run)
        except ValueError:
            continue
        xs.append(x)
        ys.append(y)
        stops.append(stop)
        used.append(pair.run_id)
    if not xs:
        raise RuntimeError("no eligible synchronized runs were loaded")
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(stops), used


def train_motion_model(dataset_root: str | Path, output_dir: str | Path) -> dict:
    root = Path(dataset_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pairs = discover_synchronized_pairs(root)
    train_pairs = [p for p in pairs if p.driver_id == "A" or (p.driver_id == "E" and not p.run_id.lower().startswith("vtb"))]
    validation_pairs = [p for p in pairs if p.driver_id == "B"]
    test_pairs = [p for p in pairs if p.driver_id == "E" and p.run_id.lower().startswith("vtb")]
    x_train, y_train, stop_train, train_runs = _load_group(train_pairs, 3000)
    x_validation, y_validation, stop_validation, validation_runs = _load_group(validation_pairs, 12000)
    x_test, y_test, stop_test, test_runs = _load_group(test_pairs, 12000)

    speed_model = HistGradientBoostingRegressor(
        max_iter=180,
        learning_rate=0.07,
        max_leaf_nodes=31,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=2026,
    )
    speed_model.fit(x_train, y_train)
    stop_model = LogisticRegression(max_iter=300, class_weight="balanced", random_state=2026)
    stop_model.fit(x_train, stop_train)

    validation_prediction = np.clip(speed_model.predict(x_validation), 0.0, 55.0)
    test_prediction = np.clip(speed_model.predict(x_test), 0.0, 55.0)
    edges = np.asarray([0.0, 2.0, 5.0, 10.0, 20.0, 60.0], dtype=float)
    uncertainty = []
    absolute_residual = np.abs(validation_prediction - y_validation)
    global_std = max(float(np.sqrt(np.mean((validation_prediction - y_validation) ** 2))), 0.5)
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (validation_prediction >= lower) & (validation_prediction < upper)
        if mask.sum() >= 30:
            uncertainty.append(max(float(np.sqrt(np.mean((validation_prediction[mask] - y_validation[mask]) ** 2))), 0.5))
        else:
            uncertainty.append(global_std)

    model_id = "motion-hgbr-p0-2026-01"
    manifest = {
        "model_id": model_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_type": "HistGradientBoostingRegressor",
        "feature_names": list(FEATURE_NAMES),
        "sample_rate_hz": 10.0,
        "window_samples": WINDOW_SAMPLES,
        "window_seconds": 2.0,
        "stride_samples_training": STRIDE_SAMPLES,
        "max_speed_mps": 55.0,
        "uncertainty_bins_mps": edges.tolist(),
        "uncertainty_std_mps": uncertainty,
        "split_policy": "drivers A and non-Vtb E train, B validation, complete Vtb family held out for test; equal-row synchronized pairs only",
        "train_runs": train_runs,
        "validation_runs": validation_runs,
        "test_runs": test_runs,
        "metrics": {
            "validation_speed_mae_mps": float(mean_absolute_error(y_validation, validation_prediction)),
            "validation_speed_rmse_mps": float(np.sqrt(mean_squared_error(y_validation, validation_prediction))),
            "test_speed_mae_mps": float(mean_absolute_error(y_test, test_prediction)),
            "test_speed_rmse_mps": float(np.sqrt(mean_squared_error(y_test, test_prediction))),
            "train_windows": int(len(y_train)),
            "validation_windows": int(len(y_validation)),
            "test_windows": int(len(y_test)),
        },
        "known_limitations": [
            "10 Hz source data",
            "mounted car assumption",
            "absolute speed is weakly observable during constant motion",
            "vehicle logger speed is a reference measurement, not survey truth",
        ],
    }
    joblib.dump(speed_model, output / "speed_model.joblib")
    joblib.dump(stop_model, output / "stop_model.joblib")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    card = (
        f"# Model card: {model_id}\n\n"
        f"Trained on {len(train_runs)} synchronized, equal-row IO-VNBD runs from Driver A and non-Vtb Driver E families. "
        f"Driver B is validation and the complete Vtb family is held out for test.\n\n"
        f"- Validation speed MAE: {manifest['metrics']['validation_speed_mae_mps']:.3f} m/s\n"
        f"- Held-out test speed MAE: {manifest['metrics']['test_speed_mae_mps']:.3f} m/s\n"
        f"- Input: causal 2 s window at 10 Hz; gravity-subtracted accelerometer and three gyro channels\n"
        f"- Output: forward speed, validation-derived uncertainty bin, stop probability\n\n"
        "This preliminary model is not validated for motorcycles, handheld phones, Indian roads, or external IMUs. "
        "See `manifest.json` for run provenance and limitations.\n"
    )
    (output / "MODEL_CARD.md").write_text(card, encoding="utf-8")
    return manifest
