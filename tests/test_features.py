import numpy as np
import pytest

from continuum_idr.features import FEATURE_NAMES, linear_acceleration, summarize_window


def test_gravity_removal_and_feature_shape():
    accel = np.tile([1.0, 2.0, 9.8], (20, 1))
    gravity = np.tile([0.0, 0.0, 9.8], (20, 1))
    linear = linear_acceleration(accel, gravity)
    window = np.concatenate([linear, np.zeros((20, 3))], axis=1)
    features = summarize_window(window)
    assert len(features) == len(FEATURE_NAMES) == 42
    assert features[0] == pytest.approx(1.0)
    assert features[7] == pytest.approx(2.0)


def test_invalid_feature_window_is_rejected():
    with pytest.raises(ValueError):
        summarize_window(np.zeros((20, 5)))
