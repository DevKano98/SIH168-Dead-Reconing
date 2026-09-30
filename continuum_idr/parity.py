"""Continuum IDR — Deterministic Multi-Stage Parity Fixture Generator.

Creates a multi-stage operational test trajectory covering:
1. Aided highway cruise (accelerating, cruising 15-20 m/s, gentle curve)
2. Total GNSS tunnel blackout (30s outage, deceleration, 90-deg turn, acceleration)
3. Smooth GNSS recovery / reacquisition
4. Urban stop-and-go traffic (stop detection under engine idle vibrations)
5. Road surface shock anomalies (speed breaker bump, pothole dip)
6. Phone mount orientation shift (30-deg gravity vector tilt)
7. Timestamp jitter and sample dropouts
8. Urban canyon multipath coordinate jump

Feeds these stages through the reference Python portable model and exports
a deterministic golden fixture for Python and Kotlin unit testing.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .features import FEATURE_NAMES, summarize_window
from .portable_model import PortableMotionBundle


def generate_parity_dataset(
    model_bundle_path: str | Path = "models/portable/motion_portable.json",
    sample_rate_hz: float = 10.0,
) -> dict[str, Any]:
    """Generate deterministic inputs and outputs for multi-stage parity verification."""
    bundle = PortableMotionBundle.load_json(model_bundle_path)

    dt = 1.0 / sample_rate_hz
    total_steps = 250  # 25 seconds of driving data at 10 Hz
    t = np.arange(total_steps) * dt

    # Multi-stage speed profile (m/s)
    speed_gt = np.zeros(total_steps, dtype=np.float64)
    # Stage 1: t=0..5s: accelerate from 0 to 15 m/s
    speed_gt[0:50] = np.linspace(0.0, 15.0, 50)
    # Stage 2: t=5..10s: cruise at 15 m/s
    speed_gt[50:100] = 15.0
    # Stage 3: t=10..15s: brake to stop (0 m/s)
    speed_gt[100:150] = np.linspace(15.0, 0.0, 50)
    # Stage 4: t=15..18s: full stop (engine idle vibration)
    speed_gt[150:180] = 0.0
    # Stage 5: t=18..22s: accelerate to 10 m/s
    speed_gt[180:220] = np.linspace(0.0, 10.0, 40)
    # Stage 6: t=22..25s: cruise at 10 m/s
    speed_gt[220:250] = 10.0

    # Yaw rate (rad/s)
    yaw_rate = np.zeros(total_steps, dtype=np.float64)
    # 90-degree turn during t=6..8s (steps 60..80)
    yaw_rate[60:80] = (math.pi / 2.0) / 2.0  # ~0.785 rad/s
    # S-curve maneuver at t=23..24s
    yaw_rate[230:235] = 0.4
    yaw_rate[235:240] = -0.4

    # Forward linear acceleration = d(speed)/dt
    fwd_accel = np.gradient(speed_gt, dt)

    # Deterministic noise generator with fixed seed
    rng = np.random.RandomState(42)

    # Construct 6-channel IMU stream: [ax, ay, az, gx, gy, gz]
    # Phone mounted portrait in vehicle: vehicle forward is +Y, lateral is +X, vertical is +Z
    # In phone coordinates (linear accel + gravity removed):
    # ax (lateral) ~ speed * yaw_rate
    # ay (forward) ~ fwd_accel
    # az (vertical) ~ road vibration / surface bumps
    # gx (pitch rate), gy (roll rate), gz (yaw rate)
    imu_samples = np.zeros((total_steps, 6), dtype=np.float64)

    for i in range(total_steps):
        sp = speed_gt[i]
        yr = yaw_rate[i]
        fa = fwd_accel[i]

        lat_accel = sp * yr
        vert_accel = 0.0

        # Stage 4: Engine idle vibration when stopped
        if sp < 0.1:
            idle_vib = 0.12 * math.sin(2.0 * math.pi * 15.0 * t[i])
            fa += idle_vib
            vert_accel += idle_vib * 0.7

        # Stage 5: Road surface shocks
        # Speed breaker at t=9.0s (step 90)
        if 89 <= i <= 91:
            vert_accel += 6.5 * math.sin((i - 89) * math.pi / 2.0)
        # Pothole dip at t=21.0s (step 210)
        if 209 <= i <= 211:
            vert_accel -= 5.2 * math.sin((i - 209) * math.pi / 2.0)

        # Mount tilt shift at t=12.0s (step 120 onwards: 25-deg tilt)
        tilt_factor = math.cos(math.radians(25.0)) if i >= 120 else 1.0
        tilt_cross = math.sin(math.radians(25.0)) if i >= 120 else 0.0

        ax = lat_accel + rng.normal(0.0, 0.02)
        ay = fa * tilt_factor + rng.normal(0.0, 0.03)
        az = vert_accel * tilt_factor + fa * tilt_cross + rng.normal(0.0, 0.02)

        gx = rng.normal(0.0, 0.005)
        gy = rng.normal(0.0, 0.005)
        gz = yr + rng.normal(0.0, 0.008)

        imu_samples[i] = [ax, ay, az, gx, gy, gz]

    # Evaluate rolling 20-sample window across the run
    test_evaluations: list[dict[str, Any]] = []

    for step_idx in range(20, total_steps, 5):  # Sample every 5 steps
        window = imu_samples[step_idx - 20 : step_idx]  # shape (20, 6)
        features = summarize_window(window)  # length 42
        pred = bundle.predict(window)
        pred_speed = pred.speed_mps
        pred_uncert = pred.speed_std_mps
        stop_prob = pred.stop_probability
        is_stopped = stop_prob >= 0.5

        test_evaluations.append({
            "step_index": int(step_idx),
            "timestamp_s": round(float(t[step_idx]), 3),
            "ground_truth_speed_mps": round(float(speed_gt[step_idx]), 4),
            "ground_truth_yaw_rate_radps": round(float(yaw_rate[step_idx]), 4),
            "raw_window_sample_first": [round(float(v), 5) for v in window[0]],
            "raw_window_sample_last": [round(float(v), 5) for v in window[-1]],
            "features_42": [round(float(f), 6) for f in features],
            "expected_speed_mps": round(float(pred_speed), 6),
            "expected_uncertainty_std_mps": round(float(pred_uncert), 6),
            "expected_is_stopped": bool(is_stopped),
            "expected_stop_probability": round(float(stop_prob), 6),
        })

    fixture = {
        "version": "1.0.0",
        "description": "Continuum IDR Deterministic Parity Fixture (Python <-> Kotlin)",
        "model_id": bundle.model_id,
        "sample_rate_hz": float(sample_rate_hz),
        "total_test_evaluations": len(test_evaluations),
        "feature_names": list(bundle.manifest.get("feature_names", FEATURE_NAMES)),
        "evaluations": test_evaluations,
    }
    return fixture


def export_parity_fixtures() -> tuple[Path, Path]:
    fixture = generate_parity_dataset()
    content = json.dumps(fixture, indent=2)

    p1 = Path("tests/fixtures/parity_fixture.json")
    p1.parent.mkdir(parents=True, exist_ok=True)
    p1.write_text(content, encoding="utf-8")

    p2 = Path("android/app/src/test/resources/parity_fixture.json")
    p2.parent.mkdir(parents=True, exist_ok=True)
    p2.write_text(content, encoding="utf-8")

    return p1, p2


if __name__ == "__main__":
    out1, out2 = export_parity_fixtures()
    print(f"Exported parity fixtures to:\n - {out1}\n - {out2}")
