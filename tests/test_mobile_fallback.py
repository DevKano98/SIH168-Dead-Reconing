import pytest

from continuum_idr.maps import RoadGraph
from continuum_idr.mobile_fallback import FallbackState, MobileFallbackEngine
from continuum_idr.model import MotionModelBundle
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample


from continuum_idr.model import MotionPrediction


class ConstantMotionModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 12.0, stop_prob: float = 0.0):
        self.speed = speed
        self.stop_prob = stop_prob

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=self.stop_prob)


@pytest.fixture
def dummy_bundle():
    return ConstantMotionModel()


def test_mobile_fallback_gnss_healthy(dummy_bundle):
    engine = MobileFallbackEngine(model_bundle=dummy_bundle, gnss_timeout_s=1.5)
    fix = GNSSFix(0.0, 52.4, -1.5, 12.0, 90.0, 3.0)
    loc = engine.on_gnss(fix)

    assert loc.provider == "gps"
    assert loc.is_fallback is False
    assert loc.fallback_state == FallbackState.GNSS_HEALTHY
    assert loc.speed_mps == 12.0


def test_mobile_fallback_outage_trigger(dummy_bundle):
    engine = MobileFallbackEngine(model_bundle=dummy_bundle, gnss_timeout_s=1.0)
    # 1. Healthy GPS fix at t=0
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

    # 2. IMU samples before timeout
    loc_sub = engine.on_imu(IMUSample(0.5, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    assert loc_sub is None  # Normal GPS assumed, no synthetic fix needed yet

    # 3. IMU sample after timeout (t = 2.0s > 1.0s timeout)
    loc_fallback = engine.on_imu(IMUSample(2.0, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    assert loc_fallback is not None
    assert loc_fallback.provider == "continuum_idr"
    assert loc_fallback.is_fallback is True
    assert loc_fallback.fallback_state == FallbackState.FALLBACK_ACTIVE
    assert loc_fallback.latitude_deg is not None
    assert loc_fallback.longitude_deg is not None


def test_mobile_fallback_map_matching(dummy_bundle):
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=1000.0)

    engine = MobileFallbackEngine(model_bundle=dummy_bundle, road_graph=graph, gnss_timeout_s=1.0)
    # Seed at (52.4000, -1.5000)
    engine.on_gnss(GNSSFix(0.0, 52.4000, -1.5000, 10.0, 90.0, 3.0))

    # Dead reckon with IMU after outage
    loc = engine.on_imu(IMUSample(2.0, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    assert loc is not None
    assert loc.road_segment_id is not None
    assert loc.road_orthogonal_dist_m is not None
    assert loc.road_orthogonal_dist_m < 15.0  # Snapped closely to road


def test_mobile_fallback_surface_event_and_mount(dummy_bundle):
    engine = MobileFallbackEngine(model_bundle=dummy_bundle, gnss_timeout_s=1.0)

    # 1. Normal state
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

    # 2. Simulate vertical bump sequence (speed breaker)
    engine.on_imu(IMUSample(0.1, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    engine.on_imu(IMUSample(0.2, (0.0, 0.0, 14.5), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    engine.on_imu(IMUSample(0.3, (0.0, 0.0, 6.0), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))

    # 3. Simulate tilt change (gravity vector shifts to X-axis) at t=2.0s
    loc = engine.on_imu(IMUSample(2.0, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (9.81, 0.0, 0.0)))
    assert loc is not None
    assert loc.mount_displaced is True
    assert "MOUNT_TILT_FLAG" in loc.active_flags


def test_mobile_fallback_recovery(dummy_bundle):
    engine = MobileFallbackEngine(model_bundle=dummy_bundle, gnss_timeout_s=1.0)
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

    # Outage
    engine.on_imu(IMUSample(2.0, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))
    assert engine.fallback_state == FallbackState.FALLBACK_ACTIVE

    # GNSS returns
    recovered_fix = GNSSFix(2.5, 52.4001, -1.4998, 10.0, 90.0, 3.0)
    loc = engine.on_gnss(recovered_fix)
    assert loc.fallback_state == FallbackState.RECOVERING

    # Propagate motion between fixes
    for i in range(1, 10):
        engine.on_imu(IMUSample(2.5 + i * 0.1, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))

    # Next GNSS fix
    next_fix = GNSSFix(3.5, 52.4001, -1.4998, 10.0, 90.0, 5.0)
    loc2 = engine.on_gnss(next_fix)
    assert loc2.fallback_state == FallbackState.GNSS_HEALTHY
    assert loc2.provider == "gps"
    assert loc2.is_fallback is False
