import pytest

from continuum_idr.android import AndroidExecutionTracker, AndroidLocation, AndroidSensorAdapter, AndroidSensorEvent


def test_android_sensor_adapter_event_assembly():
    adapter = AndroidSensorAdapter(target_rate_hz=10.0)

    # 1. Send only Accel: no sample yet (missing gyro)
    e_accel = AndroidSensorEvent(
        sensor_type=AndroidSensorAdapter.TYPE_ACCELEROMETER,
        timestamp_ns=1_000_000_000,
        values=(0.1, 0.2, 9.8),
    )
    s1 = adapter.on_sensor_event(e_accel)
    assert s1 is None

    # 2. Send Gyro: now full frame is available, should emit IMUSample
    e_gyro = AndroidSensorEvent(
        sensor_type=AndroidSensorAdapter.TYPE_GYROSCOPE,
        timestamp_ns=1_005_000_000,
        values=(0.01, -0.02, 0.0),
    )
    s2 = adapter.on_sensor_event(e_gyro)
    assert s2 is not None
    assert s2.timestamp_s == pytest.approx(0.005, abs=1e-4)
    assert s2.accel_mps2 == (0.1, 0.2, 9.8)
    assert s2.gyro_radps == (0.01, -0.02, 0.0)
    assert s2.sensor_id == "android_phone"


def test_android_sensor_adapter_location_parsing():
    adapter = AndroidSensorAdapter()
    loc = AndroidLocation(
        time_ms=1600000000000,
        elapsed_realtime_ns=5_000_000_000,
        latitude=52.405,
        longitude=-1.505,
        speed_mps=14.2,
        bearing_deg=88.5,
        accuracy_m=3.5,
    )
    fix = adapter.on_location(loc)
    assert fix.latitude_deg == 52.405
    assert fix.longitude_deg == -1.505
    assert fix.speed_mps == 14.2
    assert fix.course_deg == 88.5
    assert fix.horizontal_accuracy_m == 3.5


def test_android_execution_tracker_budget_and_percentiles():
    tracker = AndroidExecutionTracker(deadline_budget_ms=100.0)

    # Record 90 normal executions between 5ms and 20ms
    for i in range(90):
        tracker.record_execution(duration_seconds=0.010)

    # Record 9 heavy executions at 60ms
    for i in range(9):
        tracker.record_execution(duration_seconds=0.060)

    # Record 1 overrun execution at 120ms (> 100ms budget)
    tracker.record_execution(duration_seconds=0.120)

    stats = tracker.get_stats()
    assert stats.sample_count == 100
    assert stats.missed_deadlines == 1
    assert stats.p50_latency_ms == pytest.approx(10.0, abs=2.0)
    assert stats.max_latency_ms == pytest.approx(120.0, abs=1.0)
    assert stats.p99_latency_ms > 60.0
