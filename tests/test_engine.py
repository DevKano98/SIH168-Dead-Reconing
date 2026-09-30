import math
import numpy as np
import pytest

from continuum_idr.engine import IDREngine
from continuum_idr.model import MotionPrediction
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample, TrackingMode


class ConstantMotionModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 10.0, stop_prob: float = 0.0):
        self.speed = speed
        self.stop_prob = stop_prob

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=self.stop_prob)


def imu(t: float, yaw_rate: float = 0.0, accel_x: float = 0.0):
    # yaw_index is 1 in default EngineConfig
    return IMUSample(
        timestamp_s=t,
        accel_mps2=(accel_x, 0.0, 9.80665),
        gyro_radps=(0.0, yaw_rate, 0.0),
        gravity_mps2=(0.0, 0.0, 9.80665),
    )


def test_engine_uninitialized_state_is_explicit():
    engine = IDREngine(ConstantMotionModel())
    assert not engine.initialized
    state = engine.get_state()
    assert state.tracking_mode == TrackingMode.UNINITIALIZED
    assert state.east_m is None
    assert state.north_m is None
    assert state.latitude_deg is None
    assert state.longitude_deg is None


def test_engine_flexible_constructor_argument_order():
    config = EngineConfig(gnss_timeout_s=5.0)
    model = ConstantMotionModel()

    # (model, config)
    e1 = IDREngine(model, config)
    assert e1.config.gnss_timeout_s == 5.0

    # (config, model)
    e2 = IDREngine(config, model)
    assert e2.config.gnss_timeout_s == 5.0


def test_engine_continues_during_gnss_outage():
    engine = IDREngine(ConstantMotionModel(), EngineConfig(gnss_timeout_s=1.0))
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))
    for index in range(1, 51):
        state = engine.on_imu(imu(index / 10))
    assert state.tracking_mode == TrackingMode.DEAD_RECKONING
    assert state.east_m is not None and state.east_m > 40.0
    assert abs(state.north_m) < 1.0
    assert state.horizontal_uncertainty_m > 0


def test_engine_rejects_large_gnss_jump():
    engine = IDREngine(ConstantMotionModel(), EngineConfig())
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 0.0, 0.0, 3.0))
    state = engine.on_gnss(GNSSFix(1.0, 53.4, -1.5, 0.0, 0.0, 3.0))
    assert state.last_gnss_decision.startswith("REJECT_INNOVATION")
    assert "GNSS_REJECTED" in state.health_flags


def test_engine_rejects_out_of_order_timestamps():
    engine = IDREngine(ConstantMotionModel(), EngineConfig())
    engine.on_gnss(GNSSFix(10.0, 52.4, -1.5, 10.0, 90.0, 3.0))
    engine.on_imu(imu(10.0))

    # Out of order IMU
    state_imu = engine.on_imu(imu(9.5))
    assert "OUT_OF_ORDER_IMU" in state_imu.health_flags

    # Out of order GNSS
    state_gnss = engine.on_gnss(GNSSFix(9.0, 52.4, -1.5, 10.0, 90.0, 3.0))
    assert state_gnss.last_gnss_decision == "REJECT_OUT_OF_ORDER"
    assert "GNSS_REJECTED" in state_gnss.health_flags


def test_engine_rejects_invalid_coordinates():
    engine = IDREngine(ConstantMotionModel(), EngineConfig())
    # Latitude out of bounds
    s1 = engine.on_gnss(GNSSFix(1.0, 95.0, -1.5, 5.0, 0.0, 3.0))
    assert s1.last_gnss_decision == "REJECT_RANGE"

    # Non-finite coordinates
    s2 = engine.on_gnss(GNSSFix(2.0, float("nan"), -1.5, 5.0, 0.0, 3.0))
    assert s2.last_gnss_decision == "REJECT_INVALID"


def test_engine_kinematic_heading_alignment():
    # If initial GNSS fix has no heading and speed is 0, mode is ALIGNING
    engine = IDREngine(ConstantMotionModel(speed=5.0), EngineConfig(gnss_timeout_s=5.0))
    s1 = engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 0.0, None, 3.0))
    assert s1.tracking_mode == TrackingMode.ALIGNING

    # After moving and receiving a fix with motion, heading aligns and mode becomes GNSS_AIDED
    # 52.4001 is ~11.1m North of 52.4
    s2 = engine.on_gnss(GNSSFix(1.0, 52.4001, -1.5, 5.0, 0.0, 3.0))
    assert s2.tracking_mode == TrackingMode.GNSS_AIDED
    assert s2.heading_deg == pytest.approx(0.0, abs=10.0)


def test_engine_gnss_recovery_convergence():
    config = EngineConfig(gnss_timeout_s=1.0, recovery_fixes=2)
    engine = IDREngine(ConstantMotionModel(speed=10.0), config)

    # 1. Initialize
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

    # 2. Simulate 30s outage (moves East at 10 m/s -> ~300m East)
    for i in range(1, 301):
        state = engine.on_imu(imu(i * 0.1))
    assert state.tracking_mode == TrackingMode.DEAD_RECKONING
    dr_uncertainty = state.horizontal_uncertainty_m
    assert dr_uncertainty > 10.0

    # 3. First GNSS fix arrives after outage (recovering)
    # At lat 52.4, 300m East is ~0.0044 degrees longitude
    rec_fix_1 = GNSSFix(30.1, 52.4, -1.5 + (300.0 / 67800.0), 10.0, 90.0, 4.0)
    s_rec1 = engine.on_gnss(rec_fix_1)
    assert s_rec1.tracking_mode == TrackingMode.RECOVERING
    assert s_rec1.last_gnss_decision == "ACCEPT"

    # 4. Second GNSS fix confirms recovery
    rec_fix_2 = GNSSFix(31.1, 52.4, -1.5 + (310.0 / 67800.0), 10.0, 90.0, 4.0)
    s_rec2 = engine.on_gnss(rec_fix_2)
    assert s_rec2.tracking_mode == TrackingMode.GNSS_AIDED

    # Uncertainty should decrease significantly after re-acquisition
    assert s_rec2.horizontal_uncertainty_m < dr_uncertainty


def test_engine_zupt_on_stop_detection():
    # Test zero-velocity update when stop_probability is high
    stop_model = ConstantMotionModel(speed=0.0, stop_prob=0.98)
    engine = IDREngine(stop_model, EngineConfig(model_update_hz=10.0))
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 0.0, 0.0, 2.0))

    # Feed 25 samples so window fills and model triggers
    for i in range(1, 26):
        state = engine.on_imu(imu(i * 0.1))
    assert state.speed_mps == pytest.approx(0.0, abs=0.01)
