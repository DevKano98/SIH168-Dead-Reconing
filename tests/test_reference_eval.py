from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from continuum_idr.reference_eval import (
    evaluate_trajectory_against_reference,
    load_estimate_trajectory,
    load_reference_trajectory,
)
from continuum_idr.synthetic import export_scenario_jsonl, generate_scenario


@pytest.fixture
def synthetic_trip_and_ref(tmp_path: Path) -> tuple[Path, Path]:
    scen = generate_scenario("underpass_short_outage_10s", duration_s=25.0, seed=123)
    trip_path = tmp_path / "trip.jsonl"
    export_scenario_jsonl(scen, trip_path)

    # Also write reference CSV
    ref_csv = tmp_path / "reference.csv"
    with open(ref_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_s", "lat", "lon", "speed_mps", "heading_deg"])
        # Use initial origin lat/lon and positions
        from continuum_idr.geo import LocalFrame
        frame = LocalFrame(12.9716, 77.5946)
        for i, t in enumerate(scen.timestamps):
            e = scen.ground_truth_pos[i, 0]
            n = scen.ground_truth_pos[i, 1]
            lat, lon = frame.to_wgs84(e, n)
            spd = scen.ground_truth_speed_mps[i]
            hdg = scen.ground_truth_yaw_deg[i]
            writer.writerow([round(t, 2), lat, lon, spd, hdg])

    return trip_path, ref_csv


def test_load_reference_trajectory_csv(synthetic_trip_and_ref: tuple[Path, Path]):
    _, ref_csv = synthetic_trip_and_ref
    prov, points = load_reference_trajectory(ref_csv)
    assert prov == "external_reference"
    assert len(points) > 50
    assert points[0].timestamp_s == 0.0
    assert points[0].lat != 0.0
    assert points[0].speed_mps is not None


def test_load_estimate_trajectory(synthetic_trip_and_ref: tuple[Path, Path]):
    trip_path, _ = synthetic_trip_and_ref
    trip_id, prov, points = load_estimate_trajectory(trip_path)
    assert trip_id == "underpass_short_outage_10s"
    assert len(points) >= 10
    assert points[0].lat != 0.0


def test_evaluate_trajectory_against_reference(synthetic_trip_and_ref: tuple[Path, Path], tmp_path: Path):
    trip_path, ref_csv = synthetic_trip_and_ref
    out_csv = tmp_path / "errors.csv"
    out_md = tmp_path / "eval_report.md"

    report = evaluate_trajectory_against_reference(
        trip_path=trip_path,
        reference_path=ref_csv,
        out_csv_path=out_csv,
        out_report_path=out_md,
    )

    assert report.trip_id == "underpass_short_outage_10s"
    assert report.total_samples >= 10
    assert report.distance_traveled_m > 0
    assert report.endpoint_error_m >= 0.0
    assert report.drift_pct >= 0.0
    assert report.rmse_horizontal_error_m >= 0.0
    assert report.mean_cross_track_error_m >= 0.0

    # CSV output exists and has required columns
    assert out_csv.exists()
    lines = out_csv.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 10
    assert "horizontal_error_m" in lines[0]
    assert "cross_track_m" in lines[0]

    # Markdown report exists
    assert out_md.exists()
    md_content = out_md.read_text(encoding="utf-8")
    assert "# Continuum IDR — Reference Trajectory Evaluation Report" in md_content
    assert "Primary Accuracy & Drift Benchmarks" in md_content


def test_telemetry_only_provenance(synthetic_trip_and_ref: tuple[Path, Path]):
    trip_path, _ = synthetic_trip_and_ref
    report = evaluate_trajectory_against_reference(trip_path=trip_path, reference_path=None)
    assert report.provenance == "telemetry_only"
    assert "Telemetry only, not accuracy validated" in report.notice
