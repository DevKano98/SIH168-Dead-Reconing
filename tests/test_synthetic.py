from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from continuum_idr.synthetic import (
    SCENARIO_CATALOG,
    export_scenario_jsonl,
    generate_scenario,
    list_scenarios,
)


def test_list_scenarios_contains_all_20():
    scenarios = list_scenarios()
    assert len(scenarios) == 20
    assert len(SCENARIO_CATALOG) == 20


@pytest.mark.parametrize("scenario_id", list(SCENARIO_CATALOG.keys()))
def test_generate_all_20_scenarios(scenario_id: str):
    res = generate_scenario(scenario_id, duration_s=10.0, seed=42)
    assert res.scenario_id == scenario_id
    assert res.duration_s == 10.0
    assert len(res.timestamps) > 0
    assert res.ground_truth_pos.shape == (len(res.timestamps), 3)
    assert res.ground_truth_vel.shape == (len(res.timestamps), 3)
    assert res.imu_accel.shape == (len(res.timestamps), 3)
    assert res.imu_gyro.shape == (len(res.timestamps), 3)
    assert len(res.gnss_fixes) > 0

    summary = res.to_summary()
    assert summary["scenario_id"] == scenario_id
    assert summary["total_samples"] == len(res.timestamps)


def test_specific_scenario_behaviors():
    # 1. Tunnel blackout has outage fixes
    tunnel = generate_scenario("tunnel_total_gnss_blackout_60s", duration_s=50.0)
    outages = [g for g in tunnel.gnss_fixes if g.get("is_outage")]
    assert len(outages) > 0

    # 2. Indian speed breakers have surface events
    bumps = generate_scenario("indian_road_speed_breakers_succession", duration_s=25.0)
    assert len(bumps.surface_events) >= 3
    assert any(e["kind"] == "SPEED_BREAKER" for e in bumps.surface_events)

    # 3. Potholes have surface events
    potholes = generate_scenario("indian_road_severe_potholes", duration_s=25.0)
    assert len(potholes.surface_events) >= 2
    assert any(e["kind"] == "POTHOLE" for e in potholes.surface_events)

    # 4. External IMU runs at 200 Hz
    imu200 = generate_scenario("external_high_rate_imu_200hz_drive", duration_s=5.0)
    assert imu200.sample_rate_hz == 200.0
    assert len(imu200.timestamps) == 1000

    # 5. Reverse gear in parking lot has negative speed
    parking = generate_scenario("parking_lot_low_speed_crawl_and_reverse", duration_s=25.0)
    assert np.any(parking.ground_truth_speed_mps < -0.5)


def test_export_scenario_jsonl(tmp_path: Path):
    scenario = generate_scenario("underpass_short_outage_10s", duration_s=15.0)
    out_file = tmp_path / "test_underpass.jsonl"
    export_scenario_jsonl(scenario, out_file)

    assert out_file.exists()
    lines = out_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) > 20

    # Line 1 must be metadata
    meta = json.loads(lines[0])
    assert meta["type"] == "metadata"
    assert meta["version"] == "1.0.0"
    assert meta["scenario_id"] == "underpass_short_outage_10s"

    # Subsequent lines are events
    event_types = {json.loads(line)["type"] for line in lines[1:50]}
    assert "imu" in event_types
    assert "gnss" in event_types
