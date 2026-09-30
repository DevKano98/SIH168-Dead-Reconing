import math
import numpy as np
import pytest

from continuum_idr.profiles import CAR_PROFILE, COMMERCIAL_TRUCK_PROFILE, MOTORCYCLE_PROFILE, PROFILES, RoadSurfaceDetector


def test_vehicle_profiles_and_motorcycle_lean_compensation():
    assert "car" in PROFILES
    assert "motorcycle" in PROFILES
    assert "truck" in PROFILES

    car = CAR_PROFILE
    moto = MOTORCYCLE_PROFILE

    # Car has lean_angle_compensation disabled
    assert not car.lean_angle_compensation
    assert car.calculate_lean_angle_rad(speed_mps=15.0, yaw_rate_radps=0.3) == 0.0

    # Motorcycle calculates equilibrium lean angle: theta = atan(v * omega / g)
    assert moto.lean_angle_compensation
    speed = 15.0
    yaw = 0.3
    expected_lean = math.atan((speed * yaw) / 9.80665)  # ~0.430 rad (~24.6 deg)
    lean = moto.calculate_lean_angle_rad(speed_mps=speed, yaw_rate_radps=yaw)
    assert lean == pytest.approx(expected_lean, abs=1e-3)

    # Compensated yaw rate: raw * cos(lean)
    raw_gyro = (0.0, yaw, 0.0)
    comp_yaw = moto.compensate_yaw_rate(raw_gyro, speed_mps=speed, yaw_index=1)
    assert comp_yaw == pytest.approx(yaw * math.cos(expected_lean), abs=1e-3)


def test_road_surface_detector_classifies_events():
    detector = RoadSurfaceDetector(window_size=20)

    # 1. Smooth road: 10 samples of normal gravity
    for i in range(12):
        t = i * 0.1
        event = detector.update(t, accel_mps2=(0.0, 0.0, 9.81), speed_mps=12.0)
        assert event is None

    # 2. Speed breaker: upward shock (+4.0 m/s^2 above 9.8) then drop
    t_sb = 1.3
    # Az spikes to 14.5 (+4.7 m/s^2)
    detector.update(t_sb, accel_mps2=(0.0, 0.0, 14.5), speed_mps=10.0)
    # Then dips to 7.0 (-2.8 m/s^2) -> peak-to-peak > 7.0
    ev_sb = detector.update(t_sb + 0.1, accel_mps2=(0.0, 0.0, 7.0), speed_mps=10.0)
    assert ev_sb is not None
    assert ev_sb.event_type == "SPEED_BREAKER"
    assert ev_sb.severity > 0.3

    # Wait 2.0s to clear suppression window
    for i in range(20):
        detector.update(3.0 + i * 0.1, accel_mps2=(0.0, 0.0, 9.81), speed_mps=12.0)

    # 3. Pothole: sharp downward drop (Az dips to 4.5 -> -5.3 m/s^2) followed by rim impact
    t_ph = 5.2
    detector.update(t_ph, accel_mps2=(0.0, 0.0, 4.5), speed_mps=12.0)
    ev_ph = detector.update(t_ph + 0.1, accel_mps2=(0.0, 0.0, 13.0), speed_mps=12.0)
    assert ev_ph is not None
    assert ev_ph.event_type == "POTHOLE"
