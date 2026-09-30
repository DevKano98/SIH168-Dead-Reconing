import pytest

from continuum_idr.engine import IDREngine
from continuum_idr.odometry import CANOdometryAdapter, WheelSpeedSample
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample
from continuum_idr.model import MotionPrediction


class MockModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 10.0):
        self.speed = speed

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=0.0)


def sample_imu(t: float):
    return IMUSample(t, (0.0, 0.0, 9.80665), (0.0, 0.0, 0.0), (0.0, 0.0, 9.80665))


def test_can_odometry_speed_and_differential_yaw_calculation():
    adapter = CANOdometryAdapter(default_track_width_m=1.55)

    # 1. Straight driving at 12 m/s
    sample_straight = WheelSpeedSample(
        timestamp_s=1.0,
        rear_left_mps=12.0,
        rear_right_mps=12.0,
        track_width_m=1.55,
    )
    update_straight = adapter.process(sample_straight, imu_longitudinal_accel_mps2=0.0)
    assert update_straight.vehicle_speed_mps == pytest.approx(12.0)
    assert update_straight.differential_yaw_rate_radps == pytest.approx(0.0)
    assert not update_straight.is_slipping

    # 2. Right-hand turn: outer (left) wheel is faster or inner (right) is faster
    # Right wheel faster: counter-clockwise positive yaw rate
    sample_turn = WheelSpeedSample(
        timestamp_s=1.1,
        rear_left_mps=10.0,
        rear_right_mps=11.55,
        track_width_m=1.55,
    )
    update_turn = adapter.process(sample_turn, imu_longitudinal_accel_mps2=0.0)
    assert update_turn.vehicle_speed_mps == pytest.approx(10.775)
    # (11.55 - 10.0) / 1.55 = 1.0 rad/s
    assert update_turn.differential_yaw_rate_radps == pytest.approx(1.0, abs=1e-3)


def test_can_odometry_slip_detection():
    adapter = CANOdometryAdapter(slip_acceleration_threshold_mps2=2.5)

    # Normal step
    s1 = WheelSpeedSample(timestamp_s=1.0, rear_left_mps=10.0, rear_right_mps=10.0)
    adapter.process(s1, imu_longitudinal_accel_mps2=0.0)

    # Sudden wheel spin: wheel speed jumps from 10 to 18 m/s in 0.1s (wheel accel = 80 m/s^2),
    # but vehicle IMU accel is only 1.5 m/s^2 -> SLIP!
    s2 = WheelSpeedSample(timestamp_s=1.1, rear_left_mps=18.0, rear_right_mps=18.0)
    up2 = adapter.process(s2, imu_longitudinal_accel_mps2=1.5)

    assert up2.is_slipping
    # Covariance should be inflated during slip
    assert up2.speed_std_mps > 1.0


def test_engine_on_wheel_speed_fusion():
    config = EngineConfig(enable_can_odometry=True)
    engine = IDREngine(config, MockModel(speed=10.0))
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

    # Feed IMU
    engine.on_imu(sample_imu(0.1))

    # Feed CAN wheel speed at 14.5 m/s
    wheel_sample = WheelSpeedSample(timestamp_s=0.15, rear_left_mps=14.5, rear_right_mps=14.5)
    state = engine.on_wheel_speed(wheel_sample)

    assert state.speed_mps == pytest.approx(14.5, abs=0.5)
