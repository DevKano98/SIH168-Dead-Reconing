from __future__ import annotations

import numpy as np


FEATURE_NAMES = tuple(
    f"{channel}_{stat}"
    for channel in ("ax", "ay", "az", "gx", "gy", "gz")
    for stat in ("mean", "std", "min", "max", "last", "delta", "rms")
)


def linear_acceleration(
    accel: np.ndarray, gravity: np.ndarray | None
) -> np.ndarray:
    accel = np.asarray(accel, dtype=np.float64)
    if gravity is None:
        result = accel.copy()
        result[..., 2] -= 9.80665
        return result
    return accel - np.asarray(gravity, dtype=np.float64)


def summarize_window(window: np.ndarray) -> np.ndarray:
    """Summarize a causal [time, 6] IMU window into stable scalar features."""
    window = np.asarray(window, dtype=np.float64)
    if window.ndim != 2 or window.shape[1] != 6:
        raise ValueError(f"expected [time, 6] window, got {window.shape}")
    if not np.isfinite(window).all():
        raise ValueError("window contains a non-finite value")
    chunks: list[float] = []
    for index in range(6):
        values = window[:, index]
        chunks.extend(
            [
                float(values.mean()),
                float(values.std()),
                float(values.min()),
                float(values.max()),
                float(values[-1]),
                float(values[-1] - values[0]),
                float(np.sqrt(np.mean(values * values))),
            ]
        )
    return np.asarray(chunks, dtype=np.float32)
