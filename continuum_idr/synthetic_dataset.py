"""Continuum IDR — Synthetic Indian-Road Dataset Expansion Pipeline.

Generates randomized, deterministic datasets across 17 distinct operational categories:
 1. smooth_highway
 2. city_roads
 3. stop_go_traffic
 4. dense_intersections
 5. moderate_rough_roads
 6. patched_roads
 7. small_medium_severe_potholes
 8. speed_breakers_multi_speed
 9. idling_engine_vibration
10. sudden_braking
11. tunnels_and_underpasses
12. gnss_multipath
13. parking_ramps
14. reverse_parking_crawl
15. motorcycle_vibration_and_lean
16. phone_mount_shift
17. external_100hz_200hz_imu

All trips contain the source label 'synthetic_indian_road', deterministic seeds,
ground truth trajectories, and realistic phone-like IMU/GNSS observations.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .geo import LocalFrame
from .synthetic import export_scenario_jsonl, generate_scenario


DATASET_CATEGORIES: list[str] = [
    "smooth_highway",
    "city_roads",
    "stop_go_traffic",
    "dense_intersections",
    "moderate_rough_roads",
    "patched_roads",
    "small_medium_severe_potholes",
    "speed_breakers_multi_speed",
    "idling_engine_vibration",
    "sudden_braking",
    "tunnels_and_underpasses",
    "gnss_multipath",
    "parking_ramps",
    "reverse_parking_crawl",
    "motorcycle_vibration_and_lean",
    "phone_mount_shift",
    "external_100hz_200hz_imu",
]


@dataclass
class SyntheticTripMetadata:
    trip_id: str
    category: str
    source: str = "synthetic_indian_road"
    seed: int = 42
    duration_s: float = 30.0
    sample_rate_hz: float = 10.0
    vehicle_profile: str = "car"
    distance_traveled_m: float = 0.0
    outage_count: int = 0
    surface_events_count: int = 0
    file_name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "category": self.category,
            "source": self.source,
            "seed": self.seed,
            "duration_s": round(self.duration_s, 2),
            "sample_rate_hz": self.sample_rate_hz,
            "vehicle_profile": self.vehicle_profile,
            "distance_traveled_m": round(self.distance_traveled_m, 2),
            "outage_count": self.outage_count,
            "surface_events_count": self.surface_events_count,
            "file_name": self.file_name,
            "parameters": self.parameters,
        }


def generate_category_trip(
    category: str,
    trip_idx: int,
    seed: int,
    output_dir: Path,
    base_lat: float = 12.9716,
    base_lon: float = 77.5946,
) -> tuple[SyntheticTripMetadata, Path]:
    """Generate a randomized but deterministic synthetic trip for a given category."""
    rng = np.random.RandomState(seed + trip_idx * 17)

    # Base duration with slight variation
    duration_s = float(rng.uniform(30.0, 50.0))
    rate_hz = 200.0 if category == "external_100hz_200hz_imu" and trip_idx % 2 == 1 else (
        100.0 if category == "external_100hz_200hz_imu" else 10.0
    )

    # Map category to base synthetic profile
    scenario_map = {
        "smooth_highway": "highway_high_speed_90kmh",
        "city_roads": "straight_constant_speed_cruise",
        "stop_go_traffic": "stop_and_go_urban_congestion",
        "dense_intersections": "sharp_90deg_intersection_turn",
        "moderate_rough_roads": "indian_road_speed_breakers_succession",
        "patched_roads": "indian_road_severe_potholes",
        "small_medium_severe_potholes": "indian_road_severe_potholes",
        "speed_breakers_multi_speed": "indian_road_speed_breakers_succession",
        "idling_engine_vibration": "idle_engine_vibration_stationary",
        "sudden_braking": "straight_acceleration_and_braking",
        "tunnels_and_underpasses": "tunnel_total_gnss_blackout_60s",
        "gnss_multipath": "urban_canyon_severe_multipath_jumps",
        "parking_ramps": "parking_garage_spiral_ramp_descent",
        "reverse_parking_crawl": "parking_lot_low_speed_crawl_and_reverse",
        "motorcycle_vibration_and_lean": "motorcycle_high_lean_cornering",
        "phone_mount_shift": "phone_mount_shift_in_pocket",
        "external_100hz_200hz_imu": "external_high_rate_imu_200hz_drive",
    }
    base_scenario = scenario_map.get(category, "straight_constant_speed_cruise")

    # Generate scenario
    res = generate_scenario(
        scenario_id=base_scenario,
        duration_s=duration_s,
        seed=seed + trip_idx * 31,
        origin_lat=base_lat + rng.uniform(-0.01, 0.01),
        origin_lon=base_lon + rng.uniform(-0.01, 0.01),
    )

    # Add extra random surface events for roughness categories
    if category in ("small_medium_severe_potholes", "patched_roads"):
        extra_pots = rng.randint(2, 5)
        for _ in range(extra_pots):
            pt_t = float(rng.uniform(5.0, duration_s - 5.0))
            sev = float(rng.uniform(0.4, 0.95))
            res.surface_events.append({"timestamp_s": round(pt_t, 2), "kind": "POTHOLE", "severity": sev})

    if category in ("speed_breakers_multi_speed", "moderate_rough_roads"):
        extra_bumps = rng.randint(2, 4)
        for _ in range(extra_bumps):
            bm_t = float(rng.uniform(4.0, duration_s - 4.0))
            sev = float(rng.uniform(0.5, 0.9))
            res.surface_events.append({"timestamp_s": round(bm_t, 2), "kind": "SPEED_BREAKER", "severity": sev})

    # Sort surface events by time
    res.surface_events.sort(key=lambda e: e["timestamp_s"])

    trip_id = f"synth_{category}_{trip_idx:03d}"
    file_name = f"{trip_id}.jsonl"
    out_file = output_dir / file_name

    # Set metadata
    res.metadata["source"] = "synthetic_indian_road"
    res.metadata["category"] = category
    res.metadata["seed"] = seed + trip_idx * 31

    export_scenario_jsonl(res, out_file)

    dist_m = float(np.sum(res.ground_truth_speed_mps) / res.sample_rate_hz)
    outages = sum(1 for g in res.gnss_fixes if g.get("is_outage"))

    meta = SyntheticTripMetadata(
        trip_id=trip_id,
        category=category,
        source="synthetic_indian_road",
        seed=seed + trip_idx * 31,
        duration_s=res.duration_s,
        sample_rate_hz=res.sample_rate_hz,
        vehicle_profile=res.metadata.get("vehicle_profile", "car"),
        distance_traveled_m=dist_m,
        outage_count=outages,
        surface_events_count=len(res.surface_events),
        file_name=file_name,
        parameters={
            "base_scenario": base_scenario,
            "origin_lat": res.metadata.get("origin_lat", base_lat),
            "origin_lon": res.metadata.get("origin_lon", base_lon),
        },
    )

    return meta, out_file


def generate_synthetic_dataset_pack(
    output_dir: str | Path = "artifacts/synthetic_dataset",
    trips_per_category: int = 1,
    seed: int = 2026,
) -> dict[str, Any]:
    """Generate a comprehensive multi-category synthetic Indian-road dataset pack."""
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    manifest_trips: list[dict[str, Any]] = []
    total_distance_m = 0.0
    total_duration_s = 0.0

    trip_counter = 1
    for cat in DATASET_CATEGORIES:
        for i in range(trips_per_category):
            meta, _ = generate_category_trip(
                category=cat,
                trip_idx=trip_counter,
                seed=seed,
                output_dir=out_p,
            )
            manifest_trips.append(meta.to_dict())
            total_distance_m += meta.distance_traveled_m
            total_duration_s += meta.duration_s
            trip_counter += 1

    manifest = {
        "dataset_name": "Continuum IDR — Synthetic Indian Road Benchmark Pack",
        "source": "synthetic_indian_road",
        "format_version": "1.0.0",
        "description": "Standardized multi-category synthetic evaluation trips with ground truth dynamics and sensor noise.",
        "notice": "Synthetic results demonstrate simulator behavior only. They do not demonstrate real-road accuracy.",
        "categories_count": len(DATASET_CATEGORIES),
        "total_trips": len(manifest_trips),
        "total_duration_hours": round(total_duration_s / 3600.0, 3),
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "trips": manifest_trips,
    }

    manifest_file = out_p / "dataset_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest
