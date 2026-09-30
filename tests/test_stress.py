import pytest

from continuum_idr.geo import LocalFrame
from continuum_idr.stress import CorruptionScenario, CorruptedFixInjector, evaluate_stress_scenario
from continuum_idr.types import GNSSFix
from continuum_idr.model import MotionPrediction


class MockModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 12.0):
        self.speed = speed

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=0.0)


def test_corrupted_fix_injector_mutations():
    frame = LocalFrame(52.4, -1.5)
    injector = CorruptedFixInjector(frame)

    base_fix = GNSSFix(
        timestamp_s=10.0,
        latitude_deg=52.4,
        longitude_deg=-1.5,
        speed_mps=10.0,
        course_deg=90.0,
        horizontal_accuracy_m=3.0,
        fix_id="test_01",
    )

    # 1. Multipath jump test
    jumped = injector.apply_multipath_jump(base_fix, delta_east_m=80.0, delta_north_m=0.0)
    e_jump, n_jump = frame.to_enu(jumped.latitude_deg, jumped.longitude_deg)
    assert e_jump == pytest.approx(80.0, abs=0.5)

    # 2. Stale fix test
    stale = injector.apply_stale_fix(base_fix, current_timestamp_s=15.0)
    assert stale.timestamp_s == 15.0
    assert stale.latitude_deg == base_fix.latitude_deg
    assert stale.longitude_deg == base_fix.longitude_deg

    # 3. Timestamp reversal
    reversed_fix = injector.apply_timestamp_reversal(base_fix, backward_offset_s=3.0)
    assert reversed_fix.timestamp_s == 7.0

    # 4. Degradation
    degraded = injector.apply_degradation(base_fix, degraded_accuracy_m=80.0)
    assert degraded.horizontal_accuracy_m == 80.0


def test_stress_evaluation_multipath_rejection_and_recovery():
    model = MockModel(speed=12.0)
    scenario = CorruptionScenario(
        scenario_id="multipath_spike_80m",
        description="Sudden 80m multipath coordinate jump in urban canyon",
        multipath_jump_m=(80.0, 0.0),
    )

    result = evaluate_stress_scenario(model, scenario, duration_s=45.0, speed_mps=12.0)

    # Gated innovation must have rejected the 80m jump fixes
    assert result.fixes_injected > 0
    assert result.fixes_rejected > 0
    assert result.rejection_rate_pct >= 50.0
    assert "GNSS_REJECTED" in result.health_flags_raised
    # After corruption window ends, clean recovery to GNSS_AIDED must be achieved
    assert result.cleanly_recovered


def test_stress_evaluation_out_of_order_rejection():
    model = MockModel(speed=10.0)
    scenario = CorruptionScenario(
        scenario_id="timestamp_reversal",
        description="Reversed timestamps from packet jitter",
        out_of_order_offset_s=2.0,
    )

    result = evaluate_stress_scenario(model, scenario, duration_s=40.0, speed_mps=10.0)
    assert result.fixes_rejected > 0
    assert result.cleanly_recovered
