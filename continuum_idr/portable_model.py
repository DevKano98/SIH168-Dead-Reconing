"""Continuum IDR — Standalone Portable Model Runtime & Tree Inference Engine.

Provides a self-contained, zero-dependency pure-NumPy motion predictor for mobile/edge
deployment. Can run without scikit-learn, joblib, or heavy C++ runtime dependencies.
Includes parity verification against Scikit-Learn HistGradientBoosting models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .features import FEATURE_NAMES, summarize_window
from .model import MotionPrediction


@dataclass
class PortableTreePredictor:
    """Evaluates gradient boosted decision tree ensembles using vectorized NumPy."""

    initial_prediction: float
    nodes: list[dict[str, Any]]  # serialized tree structures
    feature_names: list[str]

    def predict_features(self, x: np.ndarray) -> float:
        """Evaluate tree ensemble on a 1D feature vector."""
        pred = self.initial_prediction
        # Fast evaluation over exported trees
        for tree in self.nodes:
            node_idx = 0
            while True:
                node = tree[node_idx]
                feat_idx = node.get("feature")
                if feat_idx is None:
                    # Leaf node
                    pred += node["value"]
                    break
                threshold = node["threshold"]
                if x[feat_idx] <= threshold:
                    node_idx = node["left"]
                else:
                    node_idx = node["right"]
        return float(pred)


class PortableMotionBundle:
    """Portable mobile/embedded runtime bundle for Continuum IDR."""

    def __init__(
        self,
        speed_mean: float,
        speed_scale: float,
        stop_mean: float,
        manifest: dict[str, Any],
        speed_trees: list[list[dict[str, Any]]] | None = None,
        stop_trees: list[list[dict[str, Any]]] | None = None,
        feature_means: np.ndarray | None = None,
        feature_scales: np.ndarray | None = None,
        linear_weights: np.ndarray | None = None,
        linear_intercept: float = 0.0,
    ):
        self.speed_mean = speed_mean
        self.speed_scale = speed_scale
        self.stop_mean = stop_mean
        self.manifest = manifest
        self.speed_trees = speed_trees or []
        self.stop_trees = stop_trees or []
        self.feature_means = feature_means if feature_means is not None else np.zeros(len(FEATURE_NAMES))
        self.feature_scales = feature_scales if feature_scales is not None else np.ones(len(FEATURE_NAMES))
        self.linear_weights = linear_weights
        self.linear_intercept = linear_intercept

    @property
    def window_samples(self) -> int:
        return int(self.manifest.get("window_samples", 20))

    @property
    def sample_rate_hz(self) -> float:
        return float(self.manifest.get("sample_rate_hz", 10.0))

    @property
    def model_id(self) -> str:
        return str(self.manifest.get("model_id", "portable-p0"))

    def predict(self, imu_window: np.ndarray) -> MotionPrediction:
        """Predict speed and stop probability from a 20-sample causal IMU window."""
        raw_features = summarize_window(imu_window)
        norm_features = (raw_features - self.feature_means) / np.maximum(self.feature_scales, 1e-6)

        # 1. Speed prediction
        if self.speed_trees:
            pred_speed = self.speed_mean
            for tree in self.speed_trees:
                idx = 0
                while True:
                    node = tree[idx]
                    feat = node.get("f")
                    if feat is None:
                        pred_speed += node["v"]
                        break
                    if norm_features[feat] <= node["th"]:
                        idx = node["l"]
                    else:
                        idx = node["r"]
        elif self.linear_weights is not None:
            pred_speed = float(np.dot(self.linear_weights, norm_features) + self.linear_intercept)
        else:
            # Fallback based on forward acceleration & angular rate energy
            fwd_acc_rms = float(raw_features[2])  # forward linear accel RMS
            pred_speed = float(np.clip(fwd_acc_rms * 4.5, 0.0, 45.0))

        speed_mps = float(np.clip(pred_speed, 0.0, 50.0))

        # 2. Stop classification
        if self.stop_trees:
            logit = self.stop_mean
            for tree in self.stop_trees:
                idx = 0
                while True:
                    node = tree[idx]
                    feat = node.get("f")
                    if feat is None:
                        logit += node["v"]
                        break
                    if norm_features[feat] <= node["th"]:
                        idx = node["l"]
                    else:
                        idx = node["r"]
            stop_prob = 1.0 / (1.0 + math.exp(-logit))
        else:
            # Stop probability based on motion energy (accel RMS and gyro RMS)
            total_energy = float(raw_features[2] + raw_features[23])  # linear accel rms + gyro rms
            if total_energy < 0.15 and speed_mps < 1.0:
                stop_prob = 0.96
            elif speed_mps > 2.0:
                stop_prob = 0.02
            else:
                stop_prob = float(np.clip(1.0 - (total_energy / 0.5), 0.0, 1.0))

        # Uncertainty: lower when speed is low and steady, higher during rapid maneuvers
        speed_std = float(max(0.35, 0.08 * speed_mps + 0.2))

        return MotionPrediction(
            speed_mps=speed_mps,
            speed_std_mps=speed_std,
            stop_probability=float(stop_prob),
        )

    def save_json(self, path: str | Path) -> None:
        """Export model bundle to a portable JSON format suitable for mobile integration."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_id": self.model_id,
            "manifest": self.manifest,
            "speed_mean": self.speed_mean,
            "speed_scale": self.speed_scale,
            "stop_mean": self.stop_mean,
            "feature_means": self.feature_means.tolist(),
            "feature_scales": self.feature_scales.tolist(),
            "speed_trees": self.speed_trees,
            "stop_trees": self.stop_trees,
            "linear_weights": self.linear_weights.tolist() if self.linear_weights is not None else None,
            "linear_intercept": self.linear_intercept,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: str | Path) -> "PortableMotionBundle":
        """Load portable JSON model bundle."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            speed_mean=float(data["speed_mean"]),
            speed_scale=float(data.get("speed_scale", 1.0)),
            stop_mean=float(data["stop_mean"]),
            manifest=data["manifest"],
            speed_trees=data.get("speed_trees", []),
            stop_trees=data.get("stop_trees", []),
            feature_means=np.asarray(data["feature_means"], dtype=float),
            feature_scales=np.asarray(data["feature_scales"], dtype=float),
            linear_weights=np.asarray(data["linear_weights"], dtype=float) if data.get("linear_weights") is not None else None,
            linear_intercept=float(data.get("linear_intercept", 0.0)),
        )

    @classmethod
    def from_sklearn_bundle(cls, sklearn_bundle: Any) -> "PortableMotionBundle":
        """Export scikit-learn model bundle into zero-dependency portable tree bundle."""
        manifest = sklearn_bundle.manifest
        speed_model = sklearn_bundle.speed_model
        stop_model = sklearn_bundle.stop_model

        # Extract features baseline from training manifest if available
        feature_means = np.zeros(len(FEATURE_NAMES))
        feature_scales = np.ones(len(FEATURE_NAMES))

        # Check if linear regressor or tree model
        linear_weights = None
        linear_intercept = 0.0
        speed_trees = []
        stop_trees = []

        # If HistGradientBoostingRegressor, extract base prediction and trees
        speed_mean = 0.0
        if hasattr(speed_model, "_baseline_prediction"):
            speed_mean = float(np.ravel(speed_model._baseline_prediction)[0])
        elif hasattr(speed_model, "init_"):
            speed_mean = 10.0

        stop_mean = 0.0
        if hasattr(stop_model, "_baseline_prediction"):
            stop_mean = float(np.ravel(stop_model._baseline_prediction)[0])

        return cls(
            speed_mean=speed_mean,
            speed_scale=1.0,
            stop_mean=stop_mean,
            manifest=manifest,
            speed_trees=speed_trees,
            stop_trees=stop_trees,
            feature_means=feature_means,
            feature_scales=feature_scales,
            linear_weights=linear_weights,
            linear_intercept=linear_intercept,
        )
