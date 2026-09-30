import math
import numpy as np
import pytest

from continuum_idr.alignment import MountChangeDetector, OnlineGyroBiasEstimator, StopHysteresisFilter
from continuum_idr.engine import IDREngine
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample
from continuum_idr.model import MotionPrediction


class MockModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 5.0):
        self.speed = speed

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=0.0)


def test_stop_hysteresis_filter_prevents_false_stop():
    filter_ = StopHysteresisFilter(high_threshold=0.88, low_threshold=0.35, min_stop_duration_samples=5)

    # 1. Slow crawl: stop prob is moderately high (0.80) but speed is 1.5 m/s -> should NOT stop
    for _ in range(10):
        is_stopped = filter_.update(stop_probability=0.80, current_speed_mps=1.5, accel_variance=0.5)
        assert not is_stopped

    # 2. Confirmed stop: stop prob is 0.95, speed is 0.0, low variance -> after 5 samples, should STOP
    for _ in range(4):
        filter_.update(stop_probability=0.95, current_speed_mps=0.0, accel_variance=0.05)
    # 5th sample triggers stop
    assert filter_.update(stop_probability=0.95, current_speed_mps=0.0, accel_variance=0.05)
    assert filter_.is_stopped

    # 3. Acceleration / takeoff: speed increases to 2.5 m/s -> should exit stop state
    filter_.update(stop_probability=0.20, current_speed_mps=2.5, accel_variance=0.8)
    filter_.update(stop_probability=0.10, current_speed_mps=3.5, accel_variance=0.8)
    assert not filter_.is_stopped


def test_mount_change_detector_identifies_orientation_shift():
    detector = MountChangeDetector(angle_threshold_deg=12.0)

    # Initialize with level phone (gravity pure Z)
    g_level = (0.0, 0.0, 9.80665)
    status_1 = detector.update(g_level, is_stationary=True)
    assert not status_1.mount_disturbance_detected

    # Small road bump vibrations (e.g. 2 deg tilt) -> no disturbance
    g_bump = (0.3, 0.2, 9.80)
    for _ in range(10):
        status_bump = detector.update(g_bump, is_stationary=False)
        assert not status_bump.mount_disturbance_detected

    # Sudden mount shift / phone knocked 30 degrees in holder
    # 30 deg rotation around X axis: y = 9.8 * sin(30) = 4.9, z = 9.8 * cos(30) = 8.49
    g_tilted = (0.0, 4.9, 8.49)
    status_tilted = detector.update(g_tilted, is_stationary=False)
    assert status_tilted.mount_disturbance_detected


def test_online_gyro_bias_estimator_converges():
    estimator = OnlineGyroBiasEstimator(learning_rate_zupt=0.10, max_bias_radps=0.08)

    # Constant sensor zero-rate bias of 0.025 rad/s (~1.4 deg/s)
    true_bias = 0.025

    # Simulate 30 stationary ZUPT updates
    for _ in range(30):
        estimator.update_from_zupt(measured_yaw_rate_radps=true_bias)

    # Estimated bias should converge close to true_bias
    assert estimator.estimated_bias_radps == pytest.approx(true_bias, abs=0.005)

    # Correction test: raw yaw rate of true_bias should be corrected to near zero
    corrected = estimator.correct(true_bias)
    assert abs(corrected) < 0.005


def test_engine_mount_disturbance_health_flag():
    config = EngineConfig(enable_mount_detector=True)
    engine = IDREngine(config, MockModel(speed=5.0))
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 5.0, 90.0, 3.0))

    # Feed level samples
    for i in range(1, 25):
        s = engine.on_imu(IMUSample(i * 0.1, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
        assert "SUSPECT_ALIGNMENT" not in s.health_flags

    # Feed sudden tilted gravity
    tilted_sample = IMUSample(2.6, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 5.5, 8.1))
    s_tilted = engine.on_imu(tilted_sample)
    assert "SUSPECT_ALIGNMENT" in s_tilted.health_flags
