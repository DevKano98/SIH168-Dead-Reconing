"""Continuum IDR — Sensor Calibration & Allan Variance Noise Profiles.

Provides sensor noise specifications and dynamic Kalman process noise (Q) covariance
generation based on physical Allan variance parameters:
1. Consumer Smartphone MEMS (e.g. Bosch BMI160, TDK InvenSense ICM-20600)
2. Automotive-Grade Industrial MEMS (e.g. Analog Devices ADIS16490)
3. Tactical-Grade Fiber Optic Gyroscope (FOG)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np


class SensorGrade(str, Enum):
    CONSUMER_PHONE_MEMS = "CONSUMER_PHONE_MEMS"
    AUTOMOTIVE_MEMS = "AUTOMOTIVE_MEMS"
    TACTICAL_FOG = "TACTICAL_FOG"


@dataclass(frozen=True)
class AllanVarianceParameters:
    grade: SensorGrade
    angle_random_walk_deg_sqrth: float  # ARW: deg / sqrt(hr)
    bias_instability_deg_hr: float  # Flicker noise: deg / hr
    rate_random_walk_deg_hr_sqrth: float  # RRW: deg / hr / sqrt(hr)
    velocity_random_walk_mps_sqrth: float  # VRW: m/s / sqrt(hr)
    accel_bias_instability_mg: float  # mg

    @property
    def gyro_white_noise_psd(self) -> float:
        """Continuous gyro white noise power spectral density (rad/s)^2 / Hz."""
        # Convert ARW from deg/sqrt(hr) to rad/sqrt(s)
        sigma_rad_sqrts = math.radians(self.angle_random_walk_deg_sqrth) / 60.0
        return float(sigma_rad_sqrts**2)

    @property
    def accel_white_noise_psd(self) -> float:
        """Continuous accel white noise power spectral density (m/s^2)^2 / Hz."""
        # Convert VRW from m/s/sqrt(hr) to (m/s^2) / sqrt(Hz)
        sigma_mps2_sqrthz = self.velocity_random_walk_mps_sqrth / 60.0
        return float(sigma_mps2_sqrthz**2)


# Standard Industry Sensor Profiles
SMARTPHONE_MEMS_PROFILE = AllanVarianceParameters(
    grade=SensorGrade.CONSUMER_PHONE_MEMS,
    angle_random_walk_deg_sqrth=0.35,  # Typical consumer MEMS gyro
    bias_instability_deg_hr=18.0,
    rate_random_walk_deg_hr_sqrth=12.0,
    velocity_random_walk_mps_sqrth=0.08,  # Typical consumer MEMS accel
    accel_bias_instability_mg=0.8,
)

AUTOMOTIVE_MEMS_PROFILE = AllanVarianceParameters(
    grade=SensorGrade.AUTOMOTIVE_MEMS,
    angle_random_walk_deg_sqrth=0.05,  # High-grade automotive MEMS
    bias_instability_deg_hr=2.5,
    rate_random_walk_deg_hr_sqrth=1.5,
    velocity_random_walk_mps_sqrth=0.015,
    accel_bias_instability_mg=0.08,
)

TACTICAL_FOG_PROFILE = AllanVarianceParameters(
    grade=SensorGrade.TACTICAL_FOG,
    angle_random_walk_deg_sqrth=0.005,  # Tactical Fiber Optic Gyroscope
    bias_instability_deg_hr=0.08,
    rate_random_walk_deg_hr_sqrth=0.04,
    velocity_random_walk_mps_sqrth=0.003,
    accel_bias_instability_mg=0.01,
)

SENSOR_PROFILES = {
    SensorGrade.CONSUMER_PHONE_MEMS: SMARTPHONE_MEMS_PROFILE,
    SensorGrade.AUTOMOTIVE_MEMS: AUTOMOTIVE_MEMS_PROFILE,
    SensorGrade.TACTICAL_FOG: TACTICAL_FOG_PROFILE,
    "phone": SMARTPHONE_MEMS_PROFILE,
    "automotive": AUTOMOTIVE_MEMS_PROFILE,
    "fog": TACTICAL_FOG_PROFILE,
}


class ProcessNoiseGenerator:
    """Computes rigorous discrete Kalman process noise matrix Q from sensor physics."""

    def __init__(self, profile: AllanVarianceParameters | str = SMARTPHONE_MEMS_PROFILE):
        if isinstance(profile, str):
            profile = SENSOR_PROFILES.get(profile, SMARTPHONE_MEMS_PROFILE)
        self.profile = profile

    def compute_discrete_q(self, dt: float, current_speed_mps: float = 10.0) -> np.ndarray:
        """Compute 4x4 discrete process noise covariance matrix Q_k for planar EKF.
        
        State vector: [east, north, speed, heading_rad]
        """
        dt = max(dt, 1e-4)
        q_accel = self.profile.accel_white_noise_psd
        q_gyro = self.profile.gyro_white_noise_psd

        # Position process noise integrated over dt (1/3 * q * dt^3)
        pos_noise = (1.0 / 3.0) * q_accel * (dt**3) + ((0.05**2) * dt)
        speed_noise = q_accel * dt + (0.15**2 * dt)
        yaw_noise = q_gyro * dt + (0.01**2 * dt)

        q = np.diag([pos_noise, pos_noise, speed_noise, yaw_noise])
        return q
