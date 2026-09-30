from __future__ import annotations

import json
from pathlib import Path

import pytest

from continuum_idr.experiments import (
    CANDIDATE_REGISTRY,
    format_experiment_comparison_markdown,
    run_experiment_suite,
)


def test_candidate_registry():
    assert len(CANDIDATE_REGISTRY) == 5
    assert "direct_speed_model" in CANDIDATE_REGISTRY
    assert "last_speed_gyro" in CANDIDATE_REGISTRY
    assert "map_matched" in CANDIDATE_REGISTRY
    assert "calibrated_alignment" in CANDIDATE_REGISTRY
    assert "disturbance_filter" in CANDIDATE_REGISTRY


def test_run_experiment_suite():
    suite_res = run_experiment_suite(
        candidate_names=["direct_speed_model", "last_speed_gyro"],
        evaluation_scenarios=["underpass_short_outage_10s"],
        model_path="models/motion_p0",
        seed=123,
    )

    assert suite_res["status"] == "success"
    assert suite_res["provenance"] == "synthetic_validation_suite"
    assert "Demonstrates simulator behavior only" in suite_res["notice"]

    # Historical IO-VNBD benchmark figures MUST be strictly preserved
    hist = suite_res["historical_io_vnbd_baseline"]
    assert hist["median_drift_pct"] == 80.32
    assert hist["pass_rate_10pct"] == 0.0
    assert hist["mean_error_m"] == 354.25

    results = suite_res["results"]
    assert len(results) == 2
    for r in results:
        assert "candidate_name" in r
        assert "median_drift_pct" in r
        assert "pass_rate_10pct" in r
        assert "pass_rate_20pct" in r
        assert "mean_endpoint_error_m" in r


def test_format_experiment_comparison_markdown():
    suite_res = run_experiment_suite(
        candidate_names=["direct_speed_model", "last_speed_gyro"],
        evaluation_scenarios=["underpass_short_outage_10s"],
        model_path="models/motion_p0",
        seed=42,
    )
    md = format_experiment_comparison_markdown(suite_res)
    assert "# Continuum IDR — Estimator Candidate Architecture Comparison" in md
    assert "Candidate Architecture Comparison Table" in md
    assert "IO-VNBD Held-Out Phone Runs" in md
    assert "80.32%" in md
    assert "0.0%" in md
