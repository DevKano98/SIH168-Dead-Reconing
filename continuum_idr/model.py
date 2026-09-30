from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from .features import FEATURE_NAMES, summarize_window


@dataclass(frozen=True)
class MotionPrediction:
    speed_mps: float
    speed_std_mps: float
    stop_probability: float


class MotionModelBundle:
    """Versioned scikit-learn model pack used by the P0 SDK."""

    def __init__(self, speed_model, stop_model, manifest: dict):
        self.speed_model = speed_model
        self.stop_model = stop_model
        self.manifest = manifest
        expected = list(FEATURE_NAMES)
        if manifest.get("feature_names") != expected:
            raise ValueError("model feature schema does not match this SDK")
        self._prediction_cache: dict[bytes, MotionPrediction] = {}

    @property
    def window_samples(self) -> int:
        return int(self.manifest["window_samples"])

    @property
    def sample_rate_hz(self) -> float:
        return float(self.manifest["sample_rate_hz"])

    @property
    def model_id(self) -> str:
        return str(self.manifest["model_id"])

    @classmethod
    def load(cls, directory: str | Path) -> "MotionModelBundle":
        directory = Path(directory)
        manifest_path = directory / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Model bundle not found at '{directory}'. Run 'python -m continuum_idr.cli train' first to create it, or specify a valid --model path."
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        speed_model_path = directory / "speed_model.joblib"
        stop_model_path = directory / "stop_model.joblib"
        if not speed_model_path.exists() or not stop_model_path.exists():
            raise FileNotFoundError(
                f"Model weights missing in '{directory}'. Run 'python -m continuum_idr.cli train' to train the model."
            )
        speed_model = joblib.load(speed_model_path)
        stop_model = joblib.load(stop_model_path)
        return cls(speed_model, stop_model, manifest)

    def predict(self, imu_window: np.ndarray) -> MotionPrediction:
        # Evaluation replays the same causal drive under several outage masks.
        # The direct P0 model has no hidden state, so identical windows have an
        # identical prediction and can be reused safely.
        key = np.asarray(imu_window, dtype=np.float32).tobytes()
        cached = self._prediction_cache.get(key)
        if cached is not None:
            return cached
        features = summarize_window(imu_window).reshape(1, -1)
        speed = float(self.speed_model.predict(features)[0])
        speed = max(0.0, min(float(self.manifest.get("max_speed_mps", 55.0)), speed))
        if hasattr(self.stop_model, "predict_proba"):
            stop_probability = float(self.stop_model.predict_proba(features)[0, 1])
        else:
            stop_probability = float(self.stop_model.predict(features)[0])
        edges = np.asarray(self.manifest["uncertainty_bins_mps"], dtype=float)
        values = np.asarray(self.manifest["uncertainty_std_mps"], dtype=float)
        bin_index = int(np.clip(np.searchsorted(edges, speed, side="right") - 1, 0, len(values) - 1))
        prediction = MotionPrediction(speed, float(values[bin_index]), stop_probability)
        if len(self._prediction_cache) < 100_000:
            self._prediction_cache[key] = prediction
        return prediction
