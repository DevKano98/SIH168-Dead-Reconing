"""Continuum IDR — Robustness, Alignment, Stop Hysteresis, and Gyro Bias Adaptation.

Implements:
1. StopHysteresisFilter: Schmitt trigger preventing false stops during low-speed crawl.
2. MountChangeDetector: Detects phone holder slip or orientation shift via gravity vector deviation.
3. OnlineGyroBiasEstimator: Learns residual gyro zero-rate bias during ZUPT/straight driving to prevent yaw drift.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class AlignmentStatus:
    is_aligned: bool
    gravity_vector: tuple[float, float, float]
    tilt_pitch_deg: float
    tilt_roll_deg: float
    mount_disturbance_detected: bool
    consecutive_stable_samples: int


class StopHysteresisFilter:
    """Schmitt-trigger stop detection filter with acceleration energy gating.
    
    Prevents false zero-velocity triggers during low-speed crawl (e.g. in traffic queues).
    """

    def __init__(
        self,
        high_threshold: float = 0.88,
        low_threshold: float = 0.35,
        min_stop_duration_samples: int = 5,
        max_crawl_speed_mps: float = 1.2,
    ):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.min_stop_duration_samples = min_stop_duration_samples
        self.max_crawl_speed_mps = max_crawl_speed_mps

        self._is_stopped = False
        self._high_count = 0
        self._low_count = 0

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    def update(
        self,
        stop_probability: float,
        current_speed_mps: float | None = None,
        accel_variance: float = 0.0,
    ) -> bool:
        """Update stop state with hysteresis.
        
        Returns:
            True if vehicle is confirmed stationary, False if moving or crawling.
        """
        speed = current_speed_mps if current_speed_mps is not None else 0.0

        if not self._is_stopped:
            # Candidate for stopping: high probability, low speed, low accel variance
            if stop_probability >= self.high_threshold and speed <= self.max_crawl_speed_mps:
                self._high_count += 1
                if self._high_count >= self.min_stop_duration_samples:
                    self._is_stopped = True
                    self._high_count = 0
            else:
                self._high_count = max(0, self._high_count - 1)
        else:
            # Currently stopped; exit only if low stop probability or motion is detected
            if stop_probability <= self.low_threshold or speed > self.max_crawl_speed_mps or accel_variance > 0.4:
                self._low_count += 1
                if self._low_count >= 2:
                    self._is_stopped = False
                    self._low_count = 0
            else:
                self._low_count = 0

        return self._is_stopped


class MountChangeDetector:
    """Monitors phone gravity vector orientation and flags disturbances or slips."""

    def __init__(
        self,
        angle_threshold_deg: float = 12.0,
        filter_alpha: float = 0.05,
        min_stable_seconds: float = 2.0,
        sample_rate_hz: float = 10.0,
    ):
        self.angle_threshold_rad = math.radians(angle_threshold_deg)
        self.filter_alpha = filter_alpha
        self.min_stable_samples = int(min_stable_seconds * sample_rate_hz)

        self._ref_gravity: np.ndarray | None = None
        self._filtered_gravity: np.ndarray | None = None
        self._stable_count = 0
        self._disturbance_flag = False

    def reset(self) -> None:
        self._ref_gravity = None
        self._filtered_gravity = None
        self._stable_count = 0
        self._disturbance_flag = False

    def update(
        self,
        gravity_mps2: tuple[float, float, float] | np.ndarray,
        is_stationary: bool = False,
    ) -> AlignmentStatus:
        g = np.asarray(gravity_mps2, dtype=float)
        norm = float(np.linalg.norm(g))
        if norm < 1e-3:
            return AlignmentStatus(False, (0.0, 0.0, 9.8), 0.0, 0.0, False, 0)

        unit_g = g / norm

        if self._filtered_gravity is None:
            self._filtered_gravity = unit_g.copy()
            self._ref_gravity = unit_g.copy()
            self._stable_count = 1
            pitch = math.degrees(math.atan2(unit_g[1], unit_g[2]))
            roll = math.degrees(math.atan2(-unit_g[0], math.hypot(unit_g[1], unit_g[2])))
            return AlignmentStatus(True, tuple(g), pitch, roll, False, 1)

        # Update filtered gravity vector
        self._filtered_gravity = (
            (1.0 - self.filter_alpha) * self._filtered_gravity + self.filter_alpha * unit_g
        )
        self._filtered_gravity /= float(np.linalg.norm(self._filtered_gravity))

        # Check instantaneous angular divergence from reference gravity
        inst_dot = float(np.clip(np.dot(unit_g, self._ref_gravity), -1.0, 1.0))
        angle_diff = math.acos(inst_dot)

        self._disturbance_flag = False
        if angle_diff > self.angle_threshold_rad:
            # Mount disturbance detected!
            self._disturbance_flag = True
            # Re-align reference to current gravity
            self._ref_gravity = unit_g.copy()
            self._filtered_gravity = unit_g.copy()
            self._stable_count = 0
        else:
            self._stable_count += 1
            if is_stationary and self._stable_count > self.min_stable_samples:
                # Slowly adapt reference when stationary
                self._ref_gravity = (
                    0.99 * self._ref_gravity + 0.01 * self._filtered_gravity
                )
                self._ref_gravity /= float(np.linalg.norm(self._ref_gravity))

        pitch = math.degrees(math.atan2(self._filtered_gravity[1], self._filtered_gravity[2]))
        roll = math.degrees(
            math.atan2(-self._filtered_gravity[0], math.hypot(self._filtered_gravity[1], self._filtered_gravity[2]))
        )

        return AlignmentStatus(
            is_aligned=self._stable_count >= self.min_stable_samples,
            gravity_vector=(float(g[0]), float(g[1]), float(g[2])),
            tilt_pitch_deg=pitch,
            tilt_roll_deg=roll,
            mount_disturbance_detected=self._disturbance_flag,
            consecutive_stable_samples=self._stable_count,
        )


class OnlineGyroBiasEstimator:
    """Estimates and subtracts residual gyroscope zero-rate bias during stops and straight runs."""

    def __init__(
        self,
        learning_rate_zupt: float = 0.08,
        learning_rate_straight: float = 0.01,
        max_bias_radps: float = 0.08,  # ~4.5 deg/sec maximum expected sensor bias
    ):
        self.learning_rate_zupt = learning_rate_zupt
        self.learning_rate_straight = learning_rate_straight
        self.max_bias_radps = max_bias_radps
        self._bias_radps = 0.0
        self._sample_count = 0

    @property
    def estimated_bias_radps(self) -> float:
        return self._bias_radps

    @property
    def estimated_bias_degps(self) -> float:
        return math.degrees(self._bias_radps)

    def update_from_zupt(self, measured_yaw_rate_radps: float) -> float:
        """Update bias when vehicle is confirmed stationary (ZUPT)."""
        self._sample_count += 1
        # Target stationary rate is 0.0
        error = measured_yaw_rate_radps - self._bias_radps
        self._bias_radps += self.learning_rate_zupt * error
        self._bias_radps = float(np.clip(self._bias_radps, -self.max_bias_radps, self.max_bias_radps))
        return self._bias_radps

    def update_from_gnss_straight_track(
        self,
        measured_yaw_rate_radps: float,
        gnss_heading_rate_radps: float,
        speed_mps: float,
    ) -> float:
        """Update bias during straight driving when GNSS course is highly reliable."""
        if speed_mps >= 8.0 and abs(gnss_heading_rate_radps) < 0.02:
            self._sample_count += 1
            error = (measured_yaw_rate_radps - gnss_heading_rate_radps) - self._bias_radps
            self._bias_radps += self.learning_rate_straight * error
            self._bias_radps = float(np.clip(self._bias_radps, -self.max_bias_radps, self.max_bias_radps))
        return self._bias_radps

    def correct(self, raw_yaw_rate_radps: float) -> float:
        """Return bias-corrected yaw rate in rad/s."""
        return raw_yaw_rate_radps - self._bias_radps
