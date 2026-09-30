import numpy as np
import pytest

from continuum_idr.calibration import (
    AUTOMOTIVE_MEMS_PROFILE,
    ProcessNoiseGenerator,
    SMARTPHONE_MEMS_PROFILE,
    TACTICAL_FOG_PROFILE,
)


def test_sensor_profiles_noise_ordering():
    phone = SMARTPHONE_MEMS_PROFILE
    auto = AUTOMOTIVE_MEMS_PROFILE
    fog = TACTICAL_FOG_PROFILE

    # Gyro noise: Phone > Automotive > FOG
    assert phone.gyro_white_noise_psd > auto.gyro_white_noise_psd > fog.gyro_white_noise_psd
    # Accel noise: Phone > Automotive > FOG
    assert phone.accel_white_noise_psd > auto.accel_white_noise_psd > fog.accel_white_noise_psd


def test_process_noise_generator_matrix_properties():
    generator = ProcessNoiseGenerator(SMARTPHONE_MEMS_PROFILE)
    dt = 0.1
    q = generator.compute_discrete_q(dt=dt, current_speed_mps=15.0)

    # Must be 4x4 matrix
    assert q.shape == (4, 4)

    # Must be symmetric
    assert np.allclose(q, q.T)

    # Must be positive definite (all eigenvalues > 0)
    eigenvalues = np.linalg.eigvals(q)
    assert np.all(eigenvalues > 0.0)

    # Automotive generator produces smaller process noise than phone
    auto_generator = ProcessNoiseGenerator(AUTOMOTIVE_MEMS_PROFILE)
    q_auto = auto_generator.compute_discrete_q(dt=dt, current_speed_mps=15.0)

    # Diagonal elements of auto should be strictly smaller than phone
    assert np.all(np.diag(q_auto) < np.diag(q))
