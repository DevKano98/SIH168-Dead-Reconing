from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from continuum_idr.portable_model import PortableMotionBundle


def test_parity_fixture_execution_in_python():
    fixture_path = Path("tests/fixtures/parity_fixture.json")
    assert fixture_path.exists(), "Parity fixture must exist"

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert data["version"] == "1.0.0"
    assert len(data["evaluations"]) > 0

    bundle = PortableMotionBundle.load_json("models/portable/motion_portable.json")

    for ev in data["evaluations"]:
        features = np.array(ev["features_42"], dtype=float)
        pred = bundle.predict_features(features)

        # Assert strict numerical parity
        assert pred.speed_mps == pytest.approx(ev["expected_speed_mps"], abs=1e-5), (
            f"Step {ev['step_index']}: speed mismatch"
        )
        assert pred.stop_probability == pytest.approx(ev["expected_stop_probability"], abs=1e-5), (
            f"Step {ev['step_index']}: stop probability mismatch"
        )
        assert (pred.stop_probability >= 0.5) == ev["expected_is_stopped"], (
            f"Step {ev['step_index']}: stop classification mismatch"
        )
        assert pred.speed_std_mps == pytest.approx(ev["expected_uncertainty_std_mps"], abs=1e-5), (
            f"Step {ev['step_index']}: uncertainty std mismatch"
        )
