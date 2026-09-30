import math
import pytest

from continuum_idr.geo import LocalFrame
from continuum_idr.maps import CandidateTracker, RoadGraph
from continuum_idr.engine import IDREngine
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample
from continuum_idr.model import MotionPrediction


class MockModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 12.0):
        self.speed = speed

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=0.0)


def sample_imu(t: float, accel_x: float = 0.0):
    return IMUSample(t, (accel_x, 0.0, 9.80665), (0.0, 0.0, 0.0), (0.0, 0.0, 9.80665))


def test_road_graph_creation_and_spatial_query():
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=2000.0)
    assert len(graph.nodes) > 0
    assert len(graph.segments) > 0

    # Query near origin (East=50m, North=2m)
    candidates = graph.get_candidate_segments(50.0, 2.0, radius_m=40.0)
    assert len(candidates) >= 1
    # Both main road and parallel service road should be found if radius is large
    candidates_wide = graph.get_candidate_segments(50.0, 10.0, radius_m=60.0)
    assert len(candidates_wide) >= 2


def test_candidate_tracker_projection_and_snapping():
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=1000.0)
    tracker = CandidateTracker(graph, search_radius_m=30.0)

    # Point at East=150, North=5 (5 meters North of main road centerline at North=0)
    match = tracker.match(east_m=150.0, north_m=5.0, heading_deg=90.0, speed_mps=15.0)
    assert match.matched
    assert match.snapped_east_m == pytest.approx(150.0, abs=1.0)
    assert match.snapped_north_m == pytest.approx(0.0, abs=0.5)
    assert match.cross_track_error_m == pytest.approx(5.0, abs=0.5)
    assert match.match_confidence > 0.4
    assert match.snapped_latitude_deg is not None
    assert match.snapped_longitude_deg is not None


def test_candidate_tracker_ambiguity_detection():
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=1000.0)
    # Service road is at North=25, main road is at North=0
    # Point at North=12.5 is equidistant between main and service road!
    tracker = CandidateTracker(graph, search_radius_m=35.0, ambiguity_margin=0.25)
    match = tracker.match(east_m=200.0, north_m=12.5, heading_deg=90.0, speed_mps=15.0)

    assert match.matched
    assert match.is_ambiguous
    assert len(match.alternative_segments) > 0


def test_candidate_tracker_unmatched_state():
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=1000.0)
    tracker = CandidateTracker(graph, search_radius_m=30.0)

    # Point 200 meters off-road (North=200)
    match = tracker.match(east_m=100.0, north_m=200.0, heading_deg=90.0, speed_mps=15.0)
    assert not match.matched
    assert match.segment_id is None
    assert match.snapped_east_m is None


def test_engine_map_matching_integration():
    graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=2000.0)
    config = EngineConfig(enable_map_matching=True, gnss_timeout_s=1.0)
    engine = IDREngine(config, MockModel(speed=12.0))
    engine.set_road_graph(graph)

    # Initialize near origin
    engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 12.0, 90.0, 3.0))

    # Dead reckon with slight lateral drift
    for i in range(1, 35):
        t = i * 0.1
        # Feed small lateral accel causing drift
        engine.on_imu(sample_imu(t, accel_x=0.0))

    state = engine.get_state()
    # Snapped coordinates and cross track error should be populated
    assert state.matched_segment_id is not None
    assert state.snapped_latitude_deg is not None
    assert state.cross_track_error_m is not None
