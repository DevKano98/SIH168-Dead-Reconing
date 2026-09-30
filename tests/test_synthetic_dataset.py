from __future__ import annotations

import json
from pathlib import Path

import pytest

from continuum_idr.synthetic_dataset import (
    DATASET_CATEGORIES,
    generate_category_trip,
    generate_synthetic_dataset_pack,
)


def test_dataset_categories_count():
    assert len(DATASET_CATEGORIES) == 17
    assert "smooth_highway" in DATASET_CATEGORIES
    assert "small_medium_severe_potholes" in DATASET_CATEGORIES
    assert "motorcycle_vibration_and_lean" in DATASET_CATEGORIES
    assert "external_100hz_200hz_imu" in DATASET_CATEGORIES


def test_generate_category_trip(tmp_path: Path):
    meta, file_path = generate_category_trip(
        category="small_medium_severe_potholes",
        trip_idx=1,
        seed=100,
        output_dir=tmp_path,
    )
    assert file_path.exists()
    assert meta.trip_id == "synth_small_medium_severe_potholes_001"
    assert meta.source == "synthetic_indian_road"
    assert meta.category == "small_medium_severe_potholes"
    assert meta.duration_s > 0
    assert meta.distance_traveled_m > 0
    assert meta.surface_events_count >= 2

    lines = file_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) > 10
    first_line = json.loads(lines[0])
    assert first_line["type"] == "metadata"
    assert first_line["source"] == "synthetic_indian_road"


def test_generate_synthetic_dataset_pack(tmp_path: Path):
    pack_dir = tmp_path / "pack"
    manifest = generate_synthetic_dataset_pack(
        output_dir=pack_dir,
        trips_per_category=1,
        seed=42,
    )

    manifest_file = pack_dir / "dataset_manifest.json"
    assert manifest_file.exists()

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["source"] == "synthetic_indian_road"
    assert data["categories_count"] == 17
    assert data["total_trips"] == 17
    assert "notice" in data
    assert "simulator behavior only" in data["notice"]
    assert len(data["trips"]) == 17

    # Check that all 17 files exist
    for trip_meta in data["trips"]:
        trip_file = pack_dir / trip_meta["file_name"]
        assert trip_file.exists()


def test_dataset_generation_determinism(tmp_path: Path):
    dir1 = tmp_path / "d1"
    dir2 = tmp_path / "d2"

    m1 = generate_synthetic_dataset_pack(output_dir=dir1, trips_per_category=1, seed=777)
    m2 = generate_synthetic_dataset_pack(output_dir=dir2, trips_per_category=1, seed=777)

    assert m1["total_distance_km"] == m2["total_distance_km"]
    assert m1["total_duration_hours"] == m2["total_duration_hours"]
    assert len(m1["trips"]) == len(m2["trips"])
    for t1, t2 in zip(m1["trips"], m2["trips"]):
        assert t1["trip_id"] == t2["trip_id"]
        assert t1["distance_traveled_m"] == t2["distance_traveled_m"]
