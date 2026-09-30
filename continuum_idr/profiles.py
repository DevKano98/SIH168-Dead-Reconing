"""Continuum IDR — Vehicle Dynamics Profiles & Road Surface Event Detection.

Provides:
1. VehicleProfile configurations (Passenger Car, Two-Wheeler / Motorcycle, Commercial Vehicle).
2. Motorcycle lean-angle roll compensation to prevent tilt-induced yaw cross-coupling errors.
3. RoadSurfaceDetector: Real-time detection of speed breakers, potholes, and unpaved/rough roads
   from vertical acceleration shock signatures.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class VehicleProfile:
    name: str
    max_speed_mps: float
    max_accel_mps2: float
    max_yaw_rate_radps: float
    non_holonomic_lateral_std_mps: float
    lean_angle_compensation: bool = False
    speed_process_noise_std: float = 0.7
    yaw_process_noise_std: float = 0.05

    def calculate_lean_angle_rad(self, speed_mps: float, yaw_rate_radps: float) -> float:
        """Calculate equilibrium lean angle for two-wheelers: theta = atan(v * omega / g)."""
        if not self.lean_angle_compensation or abs(speed_mps) < 1.0:
            return 0.0
        g = 9.80665
        tan_theta = (speed_mps * yaw_rate_radps) / g
        lean_rad = math.atan(tan_theta)
        # Clamp to realistic physical lean limit (+/- 45 degrees)
        return float(np.clip(lean_rad, -math.radians(45.0), math.radians(45.0)))

    def compensate_yaw_rate(
        self,
        raw_gyro_radps: tuple[float, float, float],
        speed_mps: float,
        yaw_index: int = 1,
    ) -> float:
        """Project 3D angular velocities to earth-vertical yaw rate accounting for lean."""
        raw_yaw = float(raw_gyro_radps[yaw_index])
        if not self.lean_angle_compensation:
            return raw_yaw

        lean_rad = self.calculate_lean_angle_rad(speed_mps, raw_yaw)
        # Cosine projection reduces apparent sensor yaw rate back to horizontal plane
        compensated_yaw = raw_yaw * math.cos(lean_rad)
        return float(compensated_yaw)


# Pre-configured domain profiles
CAR_PROFILE = VehicleProfile(
    name="passenger_car",
    max_speed_mps=55.0,  # ~200 km/h
    max_accel_mps2=6.0,
    max_yaw_rate_radps=0.9,
    non_holonomic_lateral_std_mps=0.08,  # strict planar constraint
    lean_angle_compensation=False,
    speed_process_noise_std=0.7,
    yaw_process_noise_std=0.05,
)

MOTORCYCLE_PROFILE = VehicleProfile(
    name="motorcycle",
    max_speed_mps=45.0,
    max_accel_mps2=8.0,
    max_yaw_rate_radps=1.6,
    non_holonomic_lateral_std_mps=0.45,  # relaxed lateral constraint due to counter-steering / lean
    lean_angle_compensation=True,
    speed_process_noise_std=1.2,
    yaw_process_noise_std=0.12,
)

COMMERCIAL_TRUCK_PROFILE = VehicleProfile(
    name="commercial_truck",
    max_speed_mps=30.0,  # ~110 km/h
    max_accel_mps2=3.0,
    max_yaw_rate_radps=0.45,
    non_holonomic_lateral_std_mps=0.04,  # very strict lateral constraint
    lean_angle_compensation=False,
    speed_process_noise_std=0.4,
    yaw_process_noise_std=0.03,
)

PROFILES = {
    "passenger_car": CAR_PROFILE,
    "car": CAR_PROFILE,
    "motorcycle": MOTORCYCLE_PROFILE,
    "two_wheeler": MOTORCYCLE_PROFILE,
    "commercial_truck": COMMERCIAL_TRUCK_PROFILE,
    "truck": COMMERCIAL_TRUCK_PROFILE,
}


@dataclass
class SurfaceEvent:
    timestamp_s: float
    event_type: Literal["SPEED_BREAKER", "POTHOLE", "ROUGH_ROAD", "SMOOTH_ROAD"]
    severity: float  # 0.0 to 1.0
    vertical_shock_mps2: float
    description: str


class RoadSurfaceDetector:
    """Detects speed breakers, potholes, and surface roughness from vertical acceleration."""

    def __init__(self, window_size: int = 20, sample_rate_hz: float = 10.0):
        self.window_size = window_size
        self.sample_rate_hz = sample_rate_hz
        self._vert_accel_history: deque[float] = deque(maxlen=window_size)
        self._timestamps: deque[float] = deque(maxlen=window_size)
        self._last_event_time_s: float = -10.0

    def update(
        self,
        timestamp_s: float,
        accel_mps2: tuple[float, float, float],
        gravity_mps2: tuple[float, float, float] | None = None,
        speed_mps: float = 10.0,
    ) -> SurfaceEvent | None:
        # Determine vertical axis (typically Z in phone body frame or projected along gravity)
        if gravity_mps2 is not None:
            g_vec = np.asarray(gravity_mps2, dtype=float)
            g_norm = float(np.linalg.norm(g_vec))
            if g_norm > 1.0:
                unit_g = g_vec / g_norm
                vert_acc = float(np.dot(np.asarray(accel_mps2, dtype=float), unit_g)) - g_norm
            else:
                vert_acc = float(accel_mps2[2]) - 9.80665
        else:
            vert_acc = float(accel_mps2[2]) - 9.80665

        self._vert_accel_history.append(vert_acc)
        self._timestamps.append(timestamp_s)

        if len(self._vert_accel_history) < 10:
            return None

        # Suppression of duplicate detections within 1.5 seconds
        if timestamp_s - self._last_event_time_s < 1.5:
            return None

        recent = np.asarray(list(self._vert_accel_history)[-8:], dtype=float)
        peak_positive = float(np.max(recent))
        peak_negative = float(np.min(recent))
        variance = float(np.var(recent))
        peak_to_peak = peak_positive - peak_negative

        # 1. Pothole signature: downward drop dominant
        if peak_to_peak > 5.5 and peak_negative < -3.5 and abs(peak_negative) >= peak_positive:
            self._last_event_time_s = timestamp_s
            severity = float(np.clip(peak_to_peak / 14.0, 0.2, 1.0))
            return SurfaceEvent(
                timestamp_s=timestamp_s,
                event_type="POTHOLE",
                severity=severity,
                vertical_shock_mps2=peak_to_peak,
                description=f"Pothole impact detected (peak drop: {peak_negative:.1f} m/s²)",
            )

        # 2. Speed breaker signature: upward shock dominant
        if peak_to_peak > 5.5 and peak_positive > 3.0 and speed_mps <= 18.0:
            self._last_event_time_s = timestamp_s
            severity = float(np.clip(peak_to_peak / 12.0, 0.2, 1.0))
            return SurfaceEvent(
                timestamp_s=timestamp_s,
                event_type="SPEED_BREAKER",
                severity=severity,
                vertical_shock_mps2=peak_to_peak,
                description=f"Speed breaker encountered at {speed_mps*3.6:.1f} km/h (shock: {peak_to_peak:.1f} m/s²)",
            )

        # 3. Sustained rough road / unpaved surface
        if variance > 3.0 and speed_mps > 3.0:
            return SurfaceEvent(
                timestamp_s=timestamp_s,
                event_type="ROUGH_ROAD",
                severity=float(np.clip(variance / 8.0, 0.3, 1.0)),
                vertical_shock_mps2=math.sqrt(variance),
                description="Rough road surface / unpaved terrain detected",
            )

        return None
