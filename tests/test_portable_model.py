from pathlib import Path
import numpy as np
import pytest

from continuum_idr.model import MotionModelBundle
from continuum_idr.portable_model import PortableMotionBundle


def test_portable_model_prediction_and_energy_heuristics():
    manifest = {"window_samples": 20, "sample_rate_hz": 10.0, "model_id": "portable-test"}
    bundle = PortableMotionBundle(
        speed_mean=10.0,
        speed_scale=1.0,
        stop_mean=0.0,
        manifest=manifest,
    )

    # 1. Stationary window: pure gravity on Z, zero gyro
    stationary_window = np.zeros((20, 6))
    stationary_window[:, 2] = 0.0  # linear accel is 0 (gravity removed)
    stationary_window[:, 3:] = 0.0  # zero gyro

    pred_stopped = bundle.predict(stationary_window)
    assert pred_stopped.stop_probability > 0.85
    assert pred_stopped.speed_mps < 1.0

    # 2. Moving window: forward accel and angular motion
    moving_window = np.zeros((20, 6))
    moving_window[:, 0] = 1.5  # forward linear accel
    moving_window[:, 4] = 0.1  # yaw rate

    pred_moving = bundle.predict(moving_window)
    assert pred_moving.stop_probability < 0.20
    assert pred_moving.speed_mps > 2.0


def test_portable_model_json_serialization_roundtrip(tmp_path):
    manifest = {"window_samples": 20, "sample_rate_hz": 10.0, "model_id": "test-save-load"}
    weights = np.linspace(0.1, 0.5, 42)
    bundle = PortableMotionBundle(
        speed_mean=8.5,
        speed_scale=1.0,
        stop_mean=-1.2,
        manifest=manifest,
        linear_weights=weights,
        linear_intercept=2.0,
    )

    out_file = tmp_path / "portable_bundle.json"
    bundle.save_json(out_file)
    assert out_file.exists()

    loaded = PortableMotionBundle.load_json(out_file)
    assert loaded.model_id == "test-save-load"
    assert loaded.speed_mean == 8.5
    assert loaded.linear_intercept == 2.0

    # Test numerical parity between original and loaded
    sample_window = np.ones((20, 6)) * 0.5
    pred_orig = bundle.predict(sample_window)
    pred_load = loaded.predict(sample_window)

    assert pred_load.speed_mps == pytest.approx(pred_orig.speed_mps, abs=1e-5)
    assert pred_load.stop_probability == pytest.approx(pred_orig.stop_probability, abs=1e-5)


def test_conversion_from_sklearn_bundle():
    model_dir = Path("models/motion_p0")
    if (model_dir / "manifest.json").exists():
        sklearn_bundle = MotionModelBundle.load(model_dir)
        portable = PortableMotionBundle.from_sklearn_bundle(sklearn_bundle)

        assert len(portable.speed_trees) == len(sklearn_bundle.speed_model._predictors)
        assert portable.stop_linear_weights is not None
        rng = np.random.default_rng(2026)
        for _ in range(5):
            sample_window = rng.normal(size=(20, 6))
            expected = sklearn_bundle.predict(sample_window)
            actual = portable.predict(sample_window)
            assert actual.speed_mps == pytest.approx(expected.speed_mps, abs=1e-9)
            assert actual.stop_probability == pytest.approx(expected.stop_probability, abs=1e-9)


def test_checked_in_portable_model_contains_trained_weights():
    model_dir = Path("models/motion_p0")
    portable_path = Path("models/portable/motion_portable.json")
    if model_dir.joinpath("manifest.json").exists() and portable_path.exists():
        sklearn_bundle = MotionModelBundle.load(model_dir)
        portable = PortableMotionBundle.load_json(portable_path)
        assert len(portable.speed_trees) == len(sklearn_bundle.speed_model._predictors)
        assert portable.stop_linear_weights is not None
        sample_window = np.arange(120, dtype=float).reshape(20, 6) / 100.0
        expected = sklearn_bundle.predict(sample_window)
        actual = portable.predict(sample_window)
        assert actual.speed_mps == pytest.approx(expected.speed_mps, abs=1e-9)
        assert actual.stop_probability == pytest.approx(expected.stop_probability, abs=1e-9)
