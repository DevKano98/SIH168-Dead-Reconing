"""Continuum IDR — Vehicle CAN Bus Wheel Speed Odometry Adapter & Slip Detector.

Ingests individual wheel tick / speed measurements, calculates differential rear-wheel
yaw rates, detects wheel slip/spin during aggressive maneuvers, and generates velocity
updates for the Kalman filter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class WheelSpeedSample:
    timestamp_s: float
    rear_left_mps: float
    rear_right_mps: float
    front_left_mps: Optional[float] = None
    front_right_mps: Optional[float] = None
    track_width_m: float = 1.55  # Standard rear track width in meters


@dataclass
class OdometryUpdate:
    timestamp_s: float
    vehicle_speed_mps: float
    differential_yaw_rate_radps: float
    is_slipping: bool
    speed_std_mps: float
    yaw_rate_std_radps: float


class CANOdometryAdapter:
    """Fuses vehicle CAN bus wheel speeds and detects tire slip."""

    def __init__(
        self,
        default_track_width_m: float = 1.55,
        slip_acceleration_threshold_mps2: float = 2.5,
    ):
        self.default_track_width_m = default_track_width_m
        self.slip_acceleration_threshold = slip_acceleration_threshold_mps2

        self._last_sample: WheelSpeedSample | None = None
        self._last_speed_mps: float | None = None
        self._last_timestamp_s: float | None = None

    def process(
        self,
        sample: WheelSpeedSample,
        imu_longitudinal_accel_mps2: float | None = None,
    ) -> OdometryUpdate:
        track = sample.track_width_m or self.default_track_width_m

        # 1. Vehicle longitudinal speed from average of un-driven or driven rear wheels
        v_speed = 0.5 * (sample.rear_left_mps + sample.rear_right_mps)
        v_speed = max(0.0, float(v_speed))

        # 2. Differential steering yaw rate from rear wheels: omega = (v_right - v_left) / track
        diff_yaw_rate = (sample.rear_right_mps - sample.rear_left_mps) / max(track, 0.5)

        # 3. Slip detection
        is_slipping = False
        if self._last_speed_mps is not None and self._last_timestamp_s is not None:
            dt = sample.timestamp_s - self._last_timestamp_s
            if dt > 1e-4:
                wheel_accel = (v_speed - self._last_speed_mps) / dt
                if imu_longitudinal_accel_mps2 is not None:
                    slip_diff = abs(wheel_accel - imu_longitudinal_accel_mps2)
                    if slip_diff > self.slip_acceleration_threshold:
                        is_slipping = True

        self._last_sample = sample
        self._last_speed_mps = v_speed
        self._last_timestamp_s = sample.timestamp_s

        # 4. Adaptive measurement uncertainty
        if is_slipping:
            speed_std = 2.5  # de-weight during slip
            yaw_std = 0.15
        else:
            speed_std = 0.10  # high precision from direct wheel encoders
            yaw_std = 0.02

        return OdometryUpdate(
            timestamp_s=sample.timestamp_s,
            vehicle_speed_mps=v_speed,
            differential_yaw_rate_radps=float(diff_yaw_rate),
            is_slipping=is_slipping,
            speed_std_mps=speed_std,
            yaw_rate_std_radps=yaw_std,
        )
