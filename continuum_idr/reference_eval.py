"""Continuum IDR — Reference Trajectory Evaluation Engine.

Provides rigorous ground-truth benchmarking against high-precision reference tracks
(RTK GNSS, Oxford OxTS, or synthetic ground truth).

Computes:
- Endpoint Euclidean error (m)
- Drift rate percentage of distance traveled (%)
- Max and RMSE horizontal error (m)
- Speed and Heading RMSE
- Along-track and Cross-track error decomposition
- Recovery settling time after GNSS outage (seconds to settle < threshold)
- Full temporal alignment with linear interpolation
- CSV point-by-point error export
- Markdown evaluation report generation
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .geo import LocalFrame, heading_deg_to_rad, wrap_heading_rad


@dataclass
class ReferencePoint:
    timestamp_s: float
    lat: float
    lon: float
    speed_mps: float | None = None
    heading_deg: float | None = None


@dataclass
class EstimatePoint:
    timestamp_s: float
    lat: float
    lon: float
    speed_mps: float | None = None
    heading_deg: float | None = None
    fallback: bool = False
    state: str = "GNSS_HEALTHY"


@dataclass
class EvaluationReport:
    trip_id: str
    provenance: str
    notice: str
    total_samples: int
    duration_s: float
    distance_traveled_m: float
    endpoint_error_m: float
    drift_pct: float
    max_horizontal_error_m: float
    rmse_horizontal_error_m: float
    mean_cross_track_error_m: float
    max_cross_track_error_m: float
    speed_rmse_mps: float | None
    heading_rmse_deg: float | None
    recovery_settling_time_s: float | None
    metrics_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "provenance": self.provenance,
            "notice": self.notice,
            "duration_s": round(self.duration_s, 2),
            "distance_traveled_m": round(self.distance_traveled_m, 2),
            "endpoint_error_m": round(self.endpoint_error_m, 2),
            "drift_pct": round(self.drift_pct, 2),
            "max_horizontal_error_m": round(self.max_horizontal_error_m, 2),
            "rmse_horizontal_error_m": round(self.rmse_horizontal_error_m, 2),
            "mean_cross_track_error_m": round(self.mean_cross_track_error_m, 2),
            "max_cross_track_error_m": round(self.max_cross_track_error_m, 2),
            "speed_rmse_mps": round(self.speed_rmse_mps, 3) if self.speed_rmse_mps is not None else None,
            "heading_rmse_deg": round(self.heading_rmse_deg, 2) if self.heading_rmse_deg is not None else None,
            "recovery_settling_time_s": round(self.recovery_settling_time_s, 2) if self.recovery_settling_time_s is not None else None,
            "total_samples": self.total_samples,
            "metrics_summary": self.metrics_summary,
        }


def load_reference_trajectory(ref_path: str | Path) -> tuple[str, list[ReferencePoint]]:
    """Load reference trajectory from CSV or JSONL."""
    p = Path(ref_path)
    if not p.exists():
        raise FileNotFoundError(f"Reference file '{p}' not found")

    points: list[ReferencePoint] = []
    provenance = "external_reference"

    if p.suffix.lower() == ".csv":
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = float(row.get("timestamp_s") or row.get("time_s") or row.get("timestamp") or 0.0)
                lat = float(row.get("lat") or row.get("latitude") or 0.0)
                lon = float(row.get("lon") or row.get("longitude") or 0.0)
                spd = float(row["speed_mps"]) if "speed_mps" in row and row["speed_mps"] else None
                hdg = float(row["heading_deg"]) if "heading_deg" in row and row["heading_deg"] else None
                points.append(ReferencePoint(timestamp_s=t, lat=lat, lon=lon, speed_mps=spd, heading_deg=hdg))
    else:  # JSONL
        with open(p, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if idx == 0 and obj.get("type") == "metadata":
                    if "synthetic" in obj.get("scenario_id", "") or "synthetic" in obj.get("source", ""):
                        provenance = "synthetic_ground_truth"
                    continue

                # Support position, reference, or ground_truth record
                if obj.get("type") in ("reference", "ground_truth", "position", "gnss"):
                    t = float(obj.get("timestamp_s") or (obj.get("wall_time_ms", 0) / 1000.0))
                    lat = float(obj.get("lat") or obj.get("latitude_deg") or 0.0)
                    lon = float(obj.get("lon") or obj.get("longitude_deg") or 0.0)
                    spd = float(obj["speed_mps"]) if "speed_mps" in obj else None
                    hdg = float(obj["heading_deg"]) if "heading_deg" in obj else None
                    if lat != 0.0 and lon != 0.0:
                        points.append(ReferencePoint(timestamp_s=t, lat=lat, lon=lon, speed_mps=spd, heading_deg=hdg))

    if not points:
        raise ValueError(f"No valid reference trajectory points found in '{p}'")

    points.sort(key=lambda pt: pt.timestamp_s)
    return provenance, points


def load_estimate_trajectory(trip_path: str | Path) -> tuple[str, str, list[EstimatePoint]]:
    """Load estimator positions from phone JSONL trip log."""
    p = Path(trip_path)
    if not p.exists():
        raise FileNotFoundError(f"Trip file '{p}' not found")

    pos_points: list[EstimatePoint] = []
    gnss_points: list[EstimatePoint] = []
    trip_id = p.stem
    provenance = "phone_telemetry"

    with open(p, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if idx == 0 and obj.get("type") == "metadata":
                if "synthetic" in obj.get("scenario_id", "") or "synthetic" in obj.get("source", ""):
                    provenance = "synthetic_ground_truth"
                trip_id = obj.get("scenario_id") or obj.get("trip_id") or p.stem
                continue

            rtype = obj.get("type")
            if rtype == "position":
                t = float(obj.get("timestamp_s") or (obj.get("wall_time_ms", 0) / 1000.0))
                lat = float(obj.get("lat", 0.0))
                lon = float(obj.get("lon", 0.0))
                spd = float(obj["speed_mps"]) if "speed_mps" in obj else None
                hdg = float(obj["heading_deg"]) if "heading_deg" in obj else None
                fb = bool(obj.get("fallback", False))
                st = str(obj.get("state", "GNSS_HEALTHY"))
                if lat != 0.0 and lon != 0.0:
                    pos_points.append(EstimatePoint(
                        timestamp_s=t,
                        lat=lat,
                        lon=lon,
                        speed_mps=spd,
                        heading_deg=hdg,
                        fallback=fb,
                        state=st,
                    ))
            elif rtype == "gnss" and not obj.get("is_outage", False):
                t = float(obj.get("timestamp_s") or (obj.get("wall_time_ms", 0) / 1000.0))
                lat = float(obj.get("lat") or obj.get("latitude_deg") or 0.0)
                lon = float(obj.get("lon") or obj.get("longitude_deg") or 0.0)
                spd = float(obj["speed_mps"]) if "speed_mps" in obj else None
                hdg = float(obj["heading_deg"]) if "heading_deg" in obj else None
                if lat != 0.0 and lon != 0.0:
                    gnss_points.append(EstimatePoint(
                        timestamp_s=t,
                        lat=lat,
                        lon=lon,
                        speed_mps=spd,
                        heading_deg=hdg,
                        fallback=False,
                        state="GNSS_HEALTHY",
                    ))

    points = pos_points if pos_points else gnss_points
    if not points:
        raise ValueError(f"No estimated position or GNSS records found in '{p}'")

    points.sort(key=lambda pt: pt.timestamp_s)
    return trip_id, provenance, points


def evaluate_trajectory_against_reference(
    trip_path: str | Path,
    reference_path: str | Path | None = None,
    recovery_threshold_m: float = 5.0,
    out_csv_path: str | Path | None = None,
    out_report_path: str | Path | None = None,
) -> EvaluationReport:
    """Compare estimated trip trajectory against high-precision reference track."""
    trip_id, est_prov, est_points = load_estimate_trajectory(trip_path)

    if reference_path is not None:
        ref_prov, ref_points = load_reference_trajectory(reference_path)
        provenance = ref_prov
    else:
        # If no external reference, but trip itself is synthetic with ground truth in another format,
        # otherwise label as telemetry only.
        provenance = "telemetry_only"
        ref_points = [ReferencePoint(
            timestamp_s=ep.timestamp_s,
            lat=ep.lat,
            lon=ep.lon,
            speed_mps=ep.speed_mps,
            heading_deg=ep.heading_deg,
        ) for ep in est_points]

    if provenance == "synthetic_ground_truth":
        notice = "Demonstrates simulator behavior only. Does not demonstrate real-road accuracy."
    elif provenance == "telemetry_only":
        notice = "Telemetry only, not accuracy validated. No independent high-precision truth was provided."
    else:
        notice = "Evaluated against external ground-truth reference trajectory."

    # Align timestamps: interpolate reference onto estimate points
    ref_times = np.array([r.timestamp_s for r in ref_points], dtype=float)
    ref_lats = np.array([r.lat for r in ref_points], dtype=float)
    ref_lons = np.array([r.lon for r in ref_points], dtype=float)

    has_ref_spd = all(r.speed_mps is not None for r in ref_points)
    ref_spds = np.array([r.speed_mps or 0.0 for r in ref_points], dtype=float) if has_ref_spd else None

    has_ref_hdg = all(r.heading_deg is not None for r in ref_points)
    ref_hdgs = np.array([r.heading_deg or 0.0 for r in ref_points], dtype=float) if has_ref_hdg else None

    # Filter est_points within reference time span
    t_min = float(ref_times[0])
    t_max = float(ref_times[-1])
    valid_est = [ep for ep in est_points if t_min <= ep.timestamp_s <= t_max]

    if len(valid_est) < 2:
        valid_est = est_points

    est_times = np.array([ep.timestamp_s for ep in valid_est], dtype=float)
    est_lats = np.array([ep.lat for ep in valid_est], dtype=float)
    est_lons = np.array([ep.lon for ep in valid_est], dtype=float)

    # Interpolate reference lat/lon
    interp_ref_lats = np.interp(est_times, ref_times, ref_lats)
    interp_ref_lons = np.interp(est_times, ref_times, ref_lons)

    # Local frame for ENU coordinate projection
    frame = LocalFrame(float(interp_ref_lats[0]), float(interp_ref_lons[0]))

    ref_enu = np.array([frame.to_enu(lat, lon) for lat, lon in zip(interp_ref_lats, interp_ref_lons)])
    est_enu = np.array([frame.to_enu(lat, lon) for lat, lon in zip(est_lats, est_lons)])

    # Compute Euclidean horizontal errors
    delta_e = est_enu[:, 0] - ref_enu[:, 0]
    delta_n = est_enu[:, 1] - ref_enu[:, 1]
    horiz_errors_m = np.hypot(delta_e, delta_n)

    # Endpoint error
    endpoint_error_m = float(horiz_errors_m[-1]) if len(horiz_errors_m) > 0 else 0.0
    max_horiz_error_m = float(np.max(horiz_errors_m)) if len(horiz_errors_m) > 0 else 0.0
    rmse_horiz_error_m = float(np.sqrt(np.mean(horiz_errors_m**2))) if len(horiz_errors_m) > 0 else 0.0

    # Total distance along reference
    diffs = np.diff(ref_enu, axis=0)
    step_dists = np.hypot(diffs[:, 0], diffs[:, 1])
    total_dist_m = float(np.sum(step_dists)) if len(step_dists) > 0 else 1.0
    total_dist_m = max(total_dist_m, 1.0)

    drift_pct = (endpoint_error_m / total_dist_m) * 100.0
    duration_s = float(est_times[-1] - est_times[0]) if len(est_times) > 1 else 0.0

    # Cross-track & along-track decomposition
    # Heading of reference track at each sample
    ref_track_headings = np.zeros(len(valid_est))
    if len(valid_est) > 1:
        # compute reference vector headings
        for i in range(len(valid_est) - 1):
            de = ref_enu[i + 1, 0] - ref_enu[i, 0]
            dn = ref_enu[i + 1, 1] - ref_enu[i, 1]
            ref_track_headings[i] = math.atan2(de, dn)
        ref_track_headings[-1] = ref_track_headings[-2]

    # Cross-track = -delta_e * sin(psi) + delta_n * cos(psi)
    # Along-track = delta_e * cos(psi) + delta_n * sin(psi)
    cross_track_m = -delta_e * np.sin(ref_track_headings) + delta_n * np.cos(ref_track_headings)
    along_track_m = delta_e * np.cos(ref_track_headings) + delta_n * np.sin(ref_track_headings)

    mean_cross_track = float(np.mean(np.abs(cross_track_m))) if len(cross_track_m) > 0 else 0.0
    max_cross_track = float(np.max(np.abs(cross_track_m))) if len(cross_track_m) > 0 else 0.0

    # Speed RMSE
    speed_rmse: float | None = None
    if ref_spds is not None:
        interp_ref_spd = np.interp(est_times, ref_times, ref_spds)
        est_spds = np.array([ep.speed_mps if ep.speed_mps is not None else 0.0 for ep in valid_est])
        speed_rmse = float(np.sqrt(np.mean((est_spds - interp_ref_spd) ** 2)))

    # Heading RMSE (circular wrap-around)
    heading_rmse: float | None = None
    if ref_hdgs is not None:
        # unwrap angles for proper circular difference
        interp_ref_hdg = np.interp(est_times, ref_times, ref_hdgs)
        est_hdgs = np.array([ep.heading_deg if ep.heading_deg is not None else 0.0 for ep in valid_est])
        ang_diffs_deg = np.array([
            math.degrees(wrap_heading_rad(heading_deg_to_rad(e) - heading_deg_to_rad(r)))
            for e, r in zip(est_hdgs, interp_ref_hdg)
        ])
        heading_rmse = float(np.sqrt(np.mean(ang_diffs_deg ** 2)))

    # Recovery Settling Time
    # Look for outage end (fallback -> not fallback)
    recovery_settling_time_s: float | None = None
    for i in range(1, len(valid_est)):
        prev_fb = valid_est[i - 1].fallback or valid_est[i - 1].state in ("FALLBACK_ACTIVE", "RECOVERING")
        curr_fb = valid_est[i].fallback or valid_est[i].state in ("FALLBACK_ACTIVE", "RECOVERING")
        if prev_fb and not curr_fb:
            recovery_start_t = valid_est[i].timestamp_s
            # Find first time error drops and stays below recovery_threshold_m
            settled_t = None
            for j in range(i, len(valid_est)):
                if horiz_errors_m[j] <= recovery_threshold_m:
                    settled_t = valid_est[j].timestamp_s
                    break
            if settled_t is not None:
                recovery_settling_time_s = max(0.0, settled_t - recovery_start_t)
            break

    # Export CSV if requested
    if out_csv_path:
        csv_p = Path(out_csv_path)
        csv_p.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_s",
                "est_lat",
                "est_lon",
                "ref_lat",
                "ref_lon",
                "horizontal_error_m",
                "cross_track_m",
                "along_track_m",
                "state",
            ])
            for i in range(len(valid_est)):
                writer.writerow([
                    round(est_times[i], 3),
                    round(est_lats[i], 7),
                    round(est_lons[i], 7),
                    round(float(interp_ref_lats[i]), 7),
                    round(float(interp_ref_lons[i]), 7),
                    round(float(horiz_errors_m[i]), 3),
                    round(float(cross_track_m[i]), 3),
                    round(float(along_track_m[i]), 3),
                    valid_est[i].state,
                ])

    report = EvaluationReport(
        trip_id=trip_id,
        provenance=provenance,
        notice=notice,
        total_samples=len(valid_est),
        duration_s=duration_s,
        distance_traveled_m=total_dist_m,
        endpoint_error_m=endpoint_error_m,
        drift_pct=drift_pct,
        max_horizontal_error_m=max_horiz_error_m,
        rmse_horizontal_error_m=rmse_horiz_error_m,
        mean_cross_track_error_m=mean_cross_track,
        max_cross_track_error_m=max_cross_track,
        speed_rmse_mps=speed_rmse,
        heading_rmse_deg=heading_rmse,
        recovery_settling_time_s=recovery_settling_time_s,
        metrics_summary={
            "drift_pass_10pct": drift_pct < 10.0,
            "drift_pass_20pct": drift_pct < 20.0,
            "recovery_settled": recovery_settling_time_s is not None,
        },
    )

    if out_report_path:
        rep_p = Path(out_report_path)
        rep_p.parent.mkdir(parents=True, exist_ok=True)
        md_text = generate_reference_evaluation_markdown(report)
        rep_p.write_text(md_text, encoding="utf-8")

    return report


def generate_reference_evaluation_markdown(rep: EvaluationReport) -> str:
    """Format reference evaluation as structured Markdown."""
    lines: list[str] = [
        f"# Continuum IDR — Reference Trajectory Evaluation Report",
        f"",
        f"**Trip ID:** `{rep.trip_id}`  ",
        f"**Provenance:** `{rep.provenance}`  ",
        f"**Notice:** *{rep.notice}*  ",
        f"",
        f"## 1. Primary Accuracy & Drift Benchmarks",
        f"",
        f"| Metric | Measured Value | Target Baseline | Compliance |",
        f"| :--- | :--- | :--- | :--- |",
        f"| **Endpoint Position Error** | **{rep.endpoint_error_m:.2f} m** | < 10.0 m | `{'PASS' if rep.endpoint_error_m < 10.0 else 'FAIL'}` |",
        f"| **Drift Rate (% Distance)** | **{rep.drift_pct:.2f}%** | < 10.0% | `{'PASS' if rep.drift_pct < 10.0 else 'FAIL'}` |",
        f"| **Horizontal Error RMSE** | {rep.rmse_horizontal_error_m:.2f} m | < 15.0 m | `{'PASS' if rep.rmse_horizontal_error_m < 15.0 else 'WARN'}` |",
        f"| **Maximum Horizontal Error** | {rep.max_horizontal_error_m:.2f} m | < 30.0 m | `{'PASS' if rep.max_horizontal_error_m < 30.0 else 'WARN'}` |",
        f"| **Mean Cross-Track Error** | {rep.mean_cross_track_error_m:.2f} m | < 5.0 m | `{'PASS' if rep.mean_cross_track_error_m < 5.0 else 'INFO'}` |",
        f"| **Max Cross-Track Error** | {rep.max_cross_track_error_m:.2f} m | < 15.0 m | `{'PASS' if rep.max_cross_track_error_m < 15.0 else 'INFO'}` |",
    ]

    if rep.speed_rmse_mps is not None:
        lines.append(f"| **Speed RMSE** | {rep.speed_rmse_mps:.2f} m/s | < 1.5 m/s | `{'PASS' if rep.speed_rmse_mps < 1.5 else 'WARN'}` |")
    if rep.heading_rmse_deg is not None:
        lines.append(f"| **Heading RMSE** | {rep.heading_rmse_deg:.2f}° | < 5.0° | `{'PASS' if rep.heading_rmse_deg < 5.0 else 'WARN'}` |")
    if rep.recovery_settling_time_s is not None:
        lines.append(f"| **Recovery Settling Time** | {rep.recovery_settling_time_s:.2f} s | < 3.0 s | `{'PASS' if rep.recovery_settling_time_s < 3.0 else 'WARN'}` |")
    else:
        lines.append(f"| **Recovery Settling Time** | N/A (no recovery event) | < 3.0 s | `INFO` |")

    lines.extend([
        f"",
        f"## 2. Operational Flight Parameters",
        f"",
        f"- **Duration:** {rep.duration_s:.1f} s",
        f"- **Total Reference Distance:** {rep.distance_traveled_m:.1f} m ({rep.distance_traveled_m / 1000.0:.2f} km)",
        f"- **Aligned Evaluation Samples:** {rep.total_samples:,}",
        f"",
        f"> [!IMPORTANT]",
        f"> **Integrity Declaration**: All reported metrics reflect causal dead reckoning. If provenance is `{rep.provenance}`, results must be interpreted within the declared operational and ground-truth boundary.",
        f"",
    ])

    return "\n".join(lines)
