import pytest

from continuum_idr.engine import IDREngine
from continuum_idr.scheduling import HighRateScheduler
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample
from continuum_idr.model import MotionPrediction


class MockModel:
    sample_rate_hz = 200.0
    window_samples = 20
    model_id = "test-model"

    def __init__(self, speed: float = 12.0):
        self.speed = speed

    def predict(self, window):
        return MotionPrediction(speed_mps=self.speed, speed_std_mps=0.5, stop_probability=0.0)


def test_high_rate_scheduler_decimation_and_metrics():
    config = EngineConfig(imu_rate_hz=200.0, model_update_hz=10.0)
    model = MockModel(speed=12.0)
    engine = IDREngine(config, model)

    scheduler = HighRateScheduler(
        engine=engine,
        target_imu_rate_hz=200.0,
        model_rate_hz=10.0,
        latency_budget_ms=5.0,
    )

    # Initialize GNSS
    scheduler.step_gnss(GNSSFix(0.0, 52.4, -1.5, 12.0, 90.0, 3.0))

    # Feed 200 samples of 200 Hz IMU (1.0 second of data)
    for i in range(1, 201):
        sample = IMUSample(
            timestamp_s=i * 0.005,
            accel_mps2=(0.0, 0.0, 9.81),
            gyro_radps=(0.0, 0.0, 0.0),
            gravity_mps2=(0.0, 0.0, 9.81),
        )
        state = scheduler.step_imu(sample)

    metrics = scheduler.get_metrics()
    assert metrics.total_imu_samples == 200
    # 200 samples with decimation of 20 should trigger model 10 times
    assert metrics.total_model_triggers == 10
    assert metrics.total_gnss_updates == 1
    # Check that average execution is very fast (well below 5 ms budget)
    assert metrics.avg_propagation_latency_ms < 5.0
