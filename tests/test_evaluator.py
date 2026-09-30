import numpy as np
import pytest

from continuum_idr.data import PairedRunData, RunPair
from continuum_idr.evaluation import _distance_axis, _smooth_reference_enu, build_outages, replay_outage, Outage
from continuum_idr.geo import LocalFrame
from continuum_idr.model import MotionPrediction
from continuum_idr.types import EngineConfig


class MockMotionModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "eval-mock-model"

    def predict(self, window):
        return MotionPrediction(speed_mps=12.0, speed_std_mps=0.5, stop_probability=0.0)


def make_synthetic_run(
    num_samples: int = 1500,
    speed_mps: float = 12.0,
    time_gap_at: int | None = None,
    gap_duration_s: float = 5.0,
    fix_interval: int = 10,
) -> PairedRunData:
    time_s = np.arange(num_samples, dtype=float) * 0.1
    if time_gap_at is not None and time_gap_at < num_samples:
        time_s[time_gap_at:] += gap_duration_s

    # Generate coordinates moving eastward at speed_mps
    # 1 deg lon ~ 67800 m at lat 52.4
    start_lat, start_lon = 52.4, -1.5
    dist = np.arange(num_samples, dtype=float) * 0.1 * speed_mps
    lons = start_lon + dist / 67800.0
    lats = np.full(num_samples, start_lat)

    # Subsample fixes according to fix_interval
    phone_lat = lats.copy()
    phone_lon = lons.copy()
    for i in range(num_samples):
        ref_idx = (i // fix_interval) * fix_interval
        phone_lat[i] = lats[ref_idx]
        phone_lon[i] = lons[ref_idx]

    phone_speed = np.full(num_samples, speed_mps)
    phone_course = np.full(num_samples, 90.0)
    phone_accuracy = np.full(num_samples, 4.0)

    accel = np.zeros((num_samples, 3))
    accel[:, 2] = 9.80665
    gravity = accel.copy()
    gyro = np.zeros((num_samples, 3))

    pair = RunPair(
        run_id="Synthetic_01",
        driver_id="T",
        phone_csv=None,
        vehicle_csv=None,
        rows_phone=num_samples,
        rows_vehicle=num_samples,
    )
    return PairedRunData(
        pair=pair,
        time_s=time_s,
        accel=accel,
        gravity=gravity,
        gyro=gyro,
        phone_lat=phone_lat,
        phone_lon=phone_lon,
        phone_speed_raw=phone_speed,
        phone_course_deg=phone_course,
        phone_accuracy_m=phone_accuracy,
        vehicle_lat=lats,
        vehicle_lon=lons,
        vehicle_speed_mps=phone_speed,
        vehicle_heading_deg=phone_course,
    )


def test_distance_axis_monotonic():
    run = make_synthetic_run(num_samples=500, speed_mps=10.0)
    dist = _distance_axis(run)
    assert len(dist) == 500
    assert dist[0] == 0.0
    assert np.all(np.diff(dist) >= 0.0)
    # 500 samples at 10 Hz = 50 s * 10 m/s ~ 500 m
    assert dist[-1] == pytest.approx(499.0, abs=2.0)


def test_smooth_reference_enu_interpolation():
    run = make_synthetic_run(num_samples=100, speed_mps=10.0, fix_interval=10)
    enu = _smooth_reference_enu(run)
    assert enu.shape == (100, 2)
    # Check that East coordinates are strictly monotonically increasing between valid fix endpoints
    assert np.all(np.diff(enu[:90, 0]) > 0.0)
    # Check North coordinates stay near zero (pure Eastward heading)
    assert np.all(np.abs(enu[:, 1]) < 0.01)


def test_build_outages_rejects_insufficient_warmup():
    # Only 320 samples total, fraction=0.2 gives start_dist index < 300
    run = make_synthetic_run(num_samples=320, speed_mps=10.0)
    outages, skipped = build_outages(run, include_skipped=True)
    assert len(outages) == 0
    reasons = [item["reason"] for item in skipped]
    assert any("insufficient_warmup" in r or "run_too_short" in r for r in reasons)


def test_build_outages_rejects_time_gaps():
    # Insert a 4.0s gap at sample 500
    run = make_synthetic_run(num_samples=1500, speed_mps=10.0, time_gap_at=500, gap_duration_s=4.0)
    outages, skipped = build_outages(run, include_skipped=True)
    time_gap_reasons = [item["reason"] for item in skipped if "time_gap" in item["reason"]]
    assert len(time_gap_reasons) > 0


def test_build_outages_rejects_low_speed():
    # Vehicle moving at only 0.5 m/s (below the 2.0 m/s quality gate)
    run = make_synthetic_run(num_samples=4000, speed_mps=0.5)
    outages, skipped = build_outages(run, include_skipped=True)
    assert len(outages) == 0
    reasons = [item["reason"] for item in skipped]
    assert any("duration_too_long" in r or "insufficient_speed" in r for r in reasons)


def test_build_outages_rejects_sparse_reference_fixes():
    # Fixes only update once every 2000 samples (extremely sparse)
    run = make_synthetic_run(num_samples=2500, speed_mps=15.0, fix_interval=2000)
    outages, skipped = build_outages(run, include_skipped=True)
    fix_reasons = [item["reason"] for item in skipped if "insufficient_reference_fixes" in item["reason"]]
    assert len(fix_reasons) > 0


def test_build_outages_creates_valid_outages():
    # 2500 samples at 12 m/s = 3000 m total, fixes every 10 samples (1 Hz)
    run = make_synthetic_run(num_samples=2500, speed_mps=12.0, fix_interval=10)
    outages = build_outages(run, include_skipped=False)
    assert len(outages) > 0
    for out in outages:
        assert out.target_distance_m in (50.0, 500.0, 1000.0)
        assert out.duration_s > 0.0
        assert out.mean_speed_mps >= 2.0


def test_replay_outage_no_leakage_and_baselines():
    run = make_synthetic_run(num_samples=1200, speed_mps=12.0, fix_interval=10)
    outages = build_outages(run, include_skipped=False)
    assert len(outages) > 0
    outage = outages[0]

    model = MockMotionModel()
    config = EngineConfig(gnss_timeout_s=1.0)
    metrics, samples = replay_outage(run, model, outage, config=config, capture=True)

    # Verify metrics structure
    assert "endpoint_error_m" in metrics
    assert "frozen_endpoint_error_m" in metrics
    assert "last_speed_gyro_endpoint_error_m" in metrics
    assert "drift_percent" in metrics

    # Baseline B0 (Frozen) must have substantial endpoint error equal to outage distance
    assert metrics["frozen_endpoint_error_m"] == pytest.approx(outage.target_distance_m, rel=0.10)

    # Verify that during outage samples, gnss is never delivered (leakage prevention)
    outage_samples = [s for s in samples if s["in_outage"]]
    assert len(outage_samples) > 0
    assert all(not s["gnss_delivered"] for s in outage_samples)
    # After warmup/timeout, tracking mode should be DEAD_RECKONING
    modes = set(s["mode"] for s in outage_samples[20:])
    assert "DEAD_RECKONING" in modes
