"""Continuum IDR — Deterministic Synthetic Scenario Generator.

Generates 20 standardized, deterministic multi-rate operational scenarios:
 1. straight_constant_speed_cruise
 2. straight_acceleration_and_braking
 3. stop_and_go_urban_congestion
 4. idle_engine_vibration_stationary
 5. highway_high_speed_90kmh
 6. sharp_90deg_intersection_turn
 7. roundabout_full_circle
 8. s_curve_chicane_maneuvers
 9. tunnel_total_gnss_blackout_60s
10. underpass_short_outage_10s
11. parking_garage_spiral_ramp_descent
12. parking_lot_low_speed_crawl_and_reverse
13. urban_canyon_severe_multipath_jumps
14. intermittent_gnss_flickering
15. indian_road_speed_breakers_succession
16. indian_road_severe_potholes
17. motorcycle_high_lean_cornering
18. motorcycle_low_speed_filtering_and_rumble
19. phone_mount_shift_in_pocket
20. external_high_rate_imu_200hz_drive

Provides exact ground truth dynamics alongside realistic sensor synthesis
(MEMS biases, noise, gravity, multipath corruption, GNSS dropouts).
Exports directly to standard Continuum JSONL trip recording format.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .geo import LocalFrame


@dataclass
class SyntheticScenarioResult:
    scenario_id: str
    scenario_name: str
    duration_s: float
    sample_rate_hz: float
    timestamps: np.ndarray
    ground_truth_pos: np.ndarray  # shape (N, 3): east, north, up
    ground_truth_vel: np.ndarray  # shape (N, 3): vx, vy, vz
    ground_truth_yaw_deg: np.ndarray
    ground_truth_speed_mps: np.ndarray
    imu_accel: np.ndarray  # shape (N, 3): ax, ay, az
    imu_gyro: np.ndarray   # shape (N, 3): gx, gy, gz
    gnss_fixes: list[dict[str, Any]]
    surface_events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "duration_s": round(float(self.duration_s), 2),
            "sample_rate_hz": float(self.sample_rate_hz),
            "total_samples": len(self.timestamps),
            "total_gnss_fixes": len(self.gnss_fixes),
            "outage_fixes_count": sum(1 for g in self.gnss_fixes if g.get("is_outage", False)),
            "surface_events_count": len(self.surface_events),
            "max_ground_truth_speed_kmh": round(float(np.max(self.ground_truth_speed_mps) * 3.6), 2),
            "distance_traveled_m": round(float(np.sum(self.ground_truth_speed_mps) / self.sample_rate_hz), 2),
        }


SCENARIO_CATALOG: dict[str, str] = {
    "straight_constant_speed_cruise": "Constant speed 50 km/h cruising along straight road",
    "straight_acceleration_and_braking": "Linear acceleration from stop to 60 km/h followed by firm braking",
    "stop_and_go_urban_congestion": "Repeated stop-and-go crawl cycles simulating heavy city traffic",
    "idle_engine_vibration_stationary": "Stationary vehicle with engine idling and high-frequency vibrations",
    "highway_high_speed_90kmh": "High speed highway cruising at 90 km/h with gentle lane shifts",
    "sharp_90deg_intersection_turn": "Urban 90-degree right turn at 25 km/h",
    "roundabout_full_circle": "Entering, traversing a 360-degree roundabout, and exiting",
    "s_curve_chicane_maneuvers": "Rapid consecutive left-right chicane steering maneuvers",
    "tunnel_total_gnss_blackout_60s": "Complete 60-second GNSS loss inside a mountain/underground tunnel",
    "underpass_short_outage_10s": "10-second rapid GNSS loss under a flyover/bridge with immediate recovery",
    "parking_garage_spiral_ramp_descent": "Descent down a 3-level spiral parking ramp with constant yaw rate",
    "parking_lot_low_speed_crawl_and_reverse": "Low speed crawl maneuvering and reverse gear backing into a bay",
    "urban_canyon_severe_multipath_jumps": "Skyscraper canyon with 40-70m multipath coordinate jumps",
    "intermittent_gnss_flickering": "Rapid flickering GNSS availability (tree foliage / urban canyon)",
    "indian_road_speed_breakers_succession": "Traversing a sequence of 4 Indian road speed humps and rumble strips",
    "indian_road_severe_potholes": "Encountering deep road potholes with sharp vertical shock signatures",
    "motorcycle_high_lean_cornering": "Motorcycle taking sharp bends with up to 35-degree lean roll angles",
    "motorcycle_low_speed_filtering_and_rumble": "Two-wheeler filtering through slow traffic with engine rumble",
    "phone_mount_shift_in_pocket": "Phone shifts orientation from dashboard mount to loose pocket during motion",
    "external_high_rate_imu_200hz_drive": "High-frequency 200 Hz external IMU stream during mixed urban driving",
}


def list_scenarios() -> list[dict[str, str]]:
    return [{"id": k, "description": v} for k, v in SCENARIO_CATALOG.items()]


def generate_scenario(
    scenario_id: str,
    duration_s: float | None = None,
    seed: int = 42,
    origin_lat: float = 12.9716,
    origin_lon: float = 77.5946,
) -> SyntheticScenarioResult:
    """Generate a deterministic synthetic test scenario."""
    if scenario_id not in SCENARIO_CATALOG:
        raise ValueError(f"Unknown scenario '{scenario_id}'. Available: {list(SCENARIO_CATALOG.keys())}")

    rng = np.random.RandomState(seed)
    frame = LocalFrame(origin_lat, origin_lon)

    # Defaults
    rate_hz = 200.0 if scenario_id == "external_high_rate_imu_200hz_drive" else 10.0
    if duration_s is None:
        if scenario_id == "tunnel_total_gnss_blackout_60s":
            duration_s = 80.0
        elif scenario_id in ("parking_garage_spiral_ramp_descent", "highway_high_speed_90kmh"):
            duration_s = 45.0
        else:
            duration_s = 30.0

    num_samples = int(duration_s * rate_hz)
    dt = 1.0 / rate_hz
    t = np.arange(num_samples) * dt

    speed = np.zeros(num_samples, dtype=np.float64)
    yaw_rate = np.zeros(num_samples, dtype=np.float64)
    vertical_accel = np.zeros(num_samples, dtype=np.float64)

    gnss_outage_mask = np.zeros(num_samples, dtype=bool)
    gnss_multipath_offset = np.zeros((num_samples, 2), dtype=np.float64)  # east, north offset

    surface_events: list[dict[str, Any]] = []
    meta: dict[str, Any] = {
        "vehicle_profile": "car",
        "mount_type": "rigid_mount",
        "origin_lat": origin_lat,
        "origin_lon": origin_lon,
    }

    # Scenario Profiles
    if scenario_id == "straight_constant_speed_cruise":
        speed[:] = 13.88  # 50 km/h

    elif scenario_id == "straight_acceleration_and_braking":
        mid = num_samples // 2
        speed[:mid] = np.linspace(0.0, 16.67, mid)  # 0 to 60 km/h
        speed[mid:] = np.linspace(16.67, 0.0, num_samples - mid)

    elif scenario_id == "stop_and_go_urban_congestion":
        # 3 cycles of stop-and-go
        cycle_len = num_samples // 3
        for c in range(3):
            s_idx = c * cycle_len
            e_idx = min(num_samples, (c + 1) * cycle_len)
            sub_len = e_idx - s_idx
            q1 = sub_len // 4
            q2 = sub_len // 2
            q3 = 3 * sub_len // 4
            speed[s_idx : s_idx + q1] = np.linspace(0.0, 6.0, q1)
            speed[s_idx + q1 : s_idx + q2] = 6.0
            speed[s_idx + q2 : s_idx + q3] = np.linspace(6.0, 0.0, q3 - q2)
            speed[s_idx + q3 : e_idx] = 0.0

    elif scenario_id == "idle_engine_vibration_stationary":
        speed[:] = 0.0
        # Engine vibration 12-25 Hz
        vib = 0.18 * np.sin(2.0 * np.pi * 18.0 * t)
        vertical_accel[:] = vib

    elif scenario_id == "highway_high_speed_90kmh":
        speed[:] = 25.0  # 90 km/h
        # Occasional lane change sinusoidal steer
        lc_start = int(15.0 * rate_hz)
        lc_len = int(4.0 * rate_hz)
        if lc_start + lc_len < num_samples:
            yaw_rate[lc_start : lc_start + lc_len] = 0.08 * np.sin(2.0 * np.pi * np.linspace(0, 1, lc_len))

    elif scenario_id == "sharp_90deg_intersection_turn":
        speed[:] = 7.0  # 25 km/h
        turn_start = int(10.0 * rate_hz)
        turn_dur = int(3.0 * rate_hz)
        if turn_start + turn_dur < num_samples:
            yaw_rate[turn_start : turn_start + turn_dur] = (math.pi / 2.0) / 3.0

    elif scenario_id == "roundabout_full_circle":
        speed[:] = 6.5
        rb_start = int(5.0 * rate_hz)
        rb_dur = int(16.0 * rate_hz)
        if rb_start + rb_dur < num_samples:
            yaw_rate[rb_start : rb_start + rb_dur] = (2.0 * math.pi) / 16.0

    elif scenario_id == "s_curve_chicane_maneuvers":
        speed[:] = 12.0
        for i, st in enumerate([8.0, 14.0, 20.0]):
            idx = int(st * rate_hz)
            dur = int(2.5 * rate_hz)
            if idx + dur < num_samples:
                sign = 1.0 if i % 2 == 0 else -1.0
                yaw_rate[idx : idx + dur] = sign * 0.45 * np.sin(np.linspace(0, np.pi, dur))

    elif scenario_id == "tunnel_total_gnss_blackout_60s":
        speed[:] = 16.0  # 57.6 km/h
        outage_start = int(10.0 * rate_hz)
        outage_end = int(70.0 * rate_hz)
        gnss_outage_mask[outage_start:outage_end] = True
        # Curve inside tunnel at t=35..40s
        c_start = int(35.0 * rate_hz)
        c_dur = int(5.0 * rate_hz)
        yaw_rate[c_start : c_start + c_dur] = 0.15

    elif scenario_id == "underpass_short_outage_10s":
        speed[:] = 14.0
        outage_start = int(10.0 * rate_hz)
        outage_end = int(20.0 * rate_hz)
        gnss_outage_mask[outage_start:outage_end] = True

    elif scenario_id == "parking_garage_spiral_ramp_descent":
        speed[:] = 4.0  # 14.4 km/h crawl
        # Constant spiral turn
        ramp_start = int(5.0 * rate_hz)
        ramp_end = int(35.0 * rate_hz)
        yaw_rate[ramp_start:ramp_end] = 0.35  # Continuous turn
        gnss_outage_mask[ramp_start:] = True  # Underground basement
        meta["vehicle_profile"] = "parking"

    elif scenario_id == "parking_lot_low_speed_crawl_and_reverse":
        meta["vehicle_profile"] = "parking"
        p1 = int(10.0 * rate_hz)
        p2 = int(18.0 * rate_hz)
        speed[:p1] = 3.0
        speed[p1:p2] = 0.0  # stop
        speed[p2:] = -1.5   # reverse gear crawl

    elif scenario_id == "urban_canyon_severe_multipath_jumps":
        speed[:] = 11.0
        # Multipath jump at t=8..18s
        mp_start = int(8.0 * rate_hz)
        mp_end = int(18.0 * rate_hz)
        gnss_multipath_offset[mp_start:mp_end, 0] = 55.0  # 55m East jump
        gnss_multipath_offset[mp_start:mp_end, 1] = -35.0 # 35m South jump

    elif scenario_id == "intermittent_gnss_flickering":
        speed[:] = 10.0
        # Rapid flickering outage 2s on, 2s off
        for sec in range(int(duration_s)):
            if (sec // 2) % 2 == 1:
                gnss_outage_mask[int(sec * rate_hz) : int((sec + 1) * rate_hz)] = True

    elif scenario_id == "indian_road_speed_breakers_succession":
        speed[:] = 8.0  # Slowing down to cross bumps
        for bump_t in [5.0, 11.0, 17.0, 23.0]:
            idx = int(bump_t * rate_hz)
            if idx < num_samples:
                vertical_accel[max(0, idx - 1) : min(num_samples, idx + 2)] += 6.5
                surface_events.append({"timestamp_s": bump_t, "kind": "SPEED_BREAKER", "severity": 0.75})

    elif scenario_id == "indian_road_severe_potholes":
        speed[:] = 9.0
        for pot_t in [7.0, 15.0, 22.0]:
            idx = int(pot_t * rate_hz)
            if idx < num_samples:
                vertical_accel[max(0, idx - 1) : min(num_samples, idx + 2)] -= 5.5
                surface_events.append({"timestamp_s": pot_t, "kind": "POTHOLE", "severity": 0.82})

    elif scenario_id == "motorcycle_high_lean_cornering":
        meta["vehicle_profile"] = "motorcycle"
        speed[:] = 15.0  # 54 km/h
        t_start = int(8.0 * rate_hz)
        t_dur = int(6.0 * rate_hz)
        if t_start + t_dur < num_samples:
            # Yaw rate of 0.35 rad/s at 15 m/s gives lean angle: atan(15 * 0.35 / 9.8) = ~28 deg
            yaw_rate[t_start : t_start + t_dur] = 0.35

    elif scenario_id == "motorcycle_low_speed_filtering_and_rumble":
        meta["vehicle_profile"] = "motorcycle"
        speed[:] = 5.0
        # High motorcycle single-cylinder engine vibration
        vertical_accel[:] = 0.35 * np.sin(2.0 * np.pi * 30.0 * t)
        # Small frequent balance turns
        yaw_rate[:] = 0.12 * np.sin(2.0 * np.pi * 0.8 * t)

    elif scenario_id == "phone_mount_shift_in_pocket":
        speed[:] = 12.0
        shift_idx = int(12.0 * rate_hz)
        meta["mount_shift_at_s"] = 12.0

    elif scenario_id == "external_high_rate_imu_200hz_drive":
        meta["sensor_rate_hz"] = 200.0
        speed[:] = 13.0
        yr_idx = int(10.0 * rate_hz)
        yr_dur = int(4.0 * rate_hz)
        yaw_rate[yr_idx : yr_idx + yr_dur] = 0.25

    # Trajectory Integration
    yaw_deg = np.zeros(num_samples, dtype=np.float64)
    pos_enu = np.zeros((num_samples, 3), dtype=np.float64)
    vel_enu = np.zeros((num_samples, 3), dtype=np.float64)

    cur_yaw = 0.0  # 0 deg = North
    cur_pos = np.array([0.0, 0.0, 0.0])

    for i in range(num_samples):
        cur_yaw = (cur_yaw + math.degrees(yaw_rate[i] * dt)) % 360.0
        yaw_deg[i] = cur_yaw

        head_rad = math.radians(cur_yaw)
        sp = speed[i]
        vx = sp * math.sin(head_rad)
        vy = sp * math.cos(head_rad)
        vz = 0.0

        vel_enu[i] = [vx, vy, vz]
        cur_pos = cur_pos + np.array([vx, vy, vz]) * dt
        pos_enu[i] = cur_pos.copy()

    # Accelerations & IMU synthesis
    fwd_accel = np.gradient(speed, dt)
    lat_accel = speed * yaw_rate

    # Phone IMU measurements
    imu_accel = np.zeros((num_samples, 3), dtype=np.float64)
    imu_gyro = np.zeros((num_samples, 3), dtype=np.float64)

    for i in range(num_samples):
        # Baseline gravity (Z=9.80665)
        gx, gy, gz = 0.0, 0.0, 9.80665

        # Mount shift logic
        if scenario_id == "phone_mount_shift_in_pocket" and i >= int(12.0 * rate_hz):
            # Rotated 35 deg pitch & roll
            gx = 3.5
            gy = 2.8
            gz = 8.7

        # In vehicle/phone frame
        ax = lat_accel[i] + gx + rng.normal(0.0, 0.03)
        ay = fwd_accel[i] + gy + rng.normal(0.0, 0.03)
        az = vertical_accel[i] + gz + rng.normal(0.0, 0.04)

        imu_accel[i] = [ax, ay, az]
        imu_gyro[i] = [
            rng.normal(0.0, 0.005),
            rng.normal(0.0, 0.005),
            yaw_rate[i] + rng.normal(0.0, 0.008),
        ]

    # Generate 1 Hz GNSS fixes
    gnss_fixes: list[dict[str, Any]] = []
    gnss_step = int(rate_hz)  # Every 1 second
    for idx in range(0, num_samples, gnss_step):
        t_fix = t[idx]
        is_out = bool(gnss_outage_mask[idx])
        e_pos = pos_enu[idx, 0] + gnss_multipath_offset[idx, 0]
        n_pos = pos_enu[idx, 1] + gnss_multipath_offset[idx, 1]

        # Add GNSS noise if not outage
        if not is_out:
            e_pos += rng.normal(0.0, 1.2)
            n_pos += rng.normal(0.0, 1.2)
            lat, lon = frame.to_wgs84(e_pos, n_pos)
            acc = 4.0 if np.linalg.norm(gnss_multipath_offset[idx]) == 0 else 45.0
            gnss_fixes.append({
                "timestamp_s": round(float(t_fix), 3),
                "latitude": round(float(lat), 7),
                "longitude": round(float(lon), 7),
                "speed_mps": round(float(abs(speed[idx])), 2),
                "bearing_deg": round(float(yaw_deg[idx]), 1),
                "accuracy_m": acc,
                "is_outage": False,
                "is_multipath": bool(np.linalg.norm(gnss_multipath_offset[idx]) > 0),
            })
        else:
            gnss_fixes.append({
                "timestamp_s": round(float(t_fix), 3),
                "is_outage": True,
            })

    return SyntheticScenarioResult(
        scenario_id=scenario_id,
        scenario_name=SCENARIO_CATALOG[scenario_id],
        duration_s=float(duration_s),
        sample_rate_hz=float(rate_hz),
        timestamps=t,
        ground_truth_pos=pos_enu,
        ground_truth_vel=vel_enu,
        ground_truth_yaw_deg=yaw_deg,
        ground_truth_speed_mps=speed,
        imu_accel=imu_accel,
        imu_gyro=imu_gyro,
        gnss_fixes=gnss_fixes,
        surface_events=surface_events,
        metadata=meta,
    )


def export_scenario_jsonl(scenario: SyntheticScenarioResult, path: str | Path) -> Path:
    """Export synthetic scenario to standard Continuum JSONL trip format (Schema 1.0.0)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    # Line 1: Metadata
    meta_line = {
        "type": "metadata",
        "version": "1.0.0",
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.scenario_name,
        "sample_rate_hz": scenario.sample_rate_hz,
        "duration_s": scenario.duration_s,
        "model_hash": "synthetic_ground_truth_v1",
        "device_model": "ContinuumSyntheticRig",
        "device_manufacturer": "ContinuumIDR",
        "os_version": "Synthetic-1.0",
        "vehicle_profile": scenario.metadata.get("vehicle_profile", "car"),
        "start_time_ms": 1700000000000,
    }
    lines.append(json.dumps(meta_line))

    # Interleave IMU and GNSS fixes chronologically
    gnss_by_time = {round(g["timestamp_s"], 1): g for g in scenario.gnss_fixes if not g.get("is_outage")}
    surface_by_time = {round(s["timestamp_s"], 1): s for s in scenario.surface_events}

    for i in range(len(scenario.timestamps)):
        t_s = float(scenario.timestamps[i])
        wall_ms = int(1700000000000 + t_s * 1000)

        # Check surface event
        t_round = round(t_s, 1)
        if t_round in surface_by_time:
            se = surface_by_time.pop(t_round)
            lines.append(json.dumps({
                "type": "surface",
                "wall_time_ms": wall_ms,
                "kind": se["kind"],
                "severity": se["severity"],
            }))

        # Check GNSS fix
        if t_round in gnss_by_time:
            gf = gnss_by_time.pop(t_round)
            lines.append(json.dumps({
                "type": "gnss",
                "wall_time_ms": wall_ms,
                "lat": gf["latitude"],
                "lon": gf["longitude"],
                "speed_mps": gf["speed_mps"],
                "bearing_deg": gf["bearing_deg"],
                "accuracy_m": gf["accuracy_m"],
                "provider": "synthetic_gps",
            }))

        # IMU sample (TYPE_ACCELEROMETER=1, TYPE_GYROSCOPE=4)
        lines.append(json.dumps({
            "type": "imu",
            "wall_time_ms": wall_ms,
            "sensor_type": 1,
            "timestamp_ns": int(t_s * 1e9),
            "values": [round(float(v), 5) for v in scenario.imu_accel[i]],
        }))
        lines.append(json.dumps({
            "type": "imu",
            "wall_time_ms": wall_ms,
            "sensor_type": 4,
            "timestamp_ns": int(t_s * 1e9),
            "values": [round(float(v), 5) for v in scenario.imu_gyro[i]],
        }))

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
