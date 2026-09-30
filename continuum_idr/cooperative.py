"""Privacy-preserving, short-lived cooperative traffic reports.

Transport is deliberately separate: BLE, Wi-Fi Direct and an internet gateway
can all carry the same validated packet.  A relay is never counted as a new
observation.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TrafficReport:
    report_id: str
    origin_id: str
    road_segment_id: str
    direction_deg: float
    observed_at_s: float
    expires_at_s: float
    speed_mps: float
    position_uncertainty_m: float
    hop_count: int = 0

    def is_live(self, now_s: float) -> bool:
        return self.observed_at_s <= now_s < self.expires_at_s

    def relay(self) -> "TrafficReport | None":
        if self.hop_count >= 8:
            return None
        return TrafficReport(**{**self.__dict__, "hop_count": self.hop_count + 1})


def create_slowdown_report(origin_id: str, road_segment_id: str, direction_deg: float, now_s: float,
                           speed_mps: float, position_uncertainty_m: float, ttl_s: float = 300.0) -> TrafficReport:
    if not origin_id or not road_segment_id:
        raise ValueError("origin and road segment are required")
    if not 0.0 <= speed_mps <= 55.0 or position_uncertainty_m < 0.0 or ttl_s <= 0.0:
        raise ValueError("invalid report measurements")
    identity = f"{origin_id}|{road_segment_id}|{round(now_s)}|{round(direction_deg)%360}"
    report_id = hashlib.sha256(identity.encode()).hexdigest()[:20]
    return TrafficReport(report_id, origin_id, road_segment_id, direction_deg % 360, now_s, now_s + ttl_s,
                         speed_mps, position_uncertainty_m)


class TrafficReportStore:
    """Deduplicates packets and only raises a warning after independent reports agree."""
    def __init__(self) -> None:
        self._reports: dict[str, TrafficReport] = {}

    def ingest(self, report: TrafficReport, now_s: float) -> bool:
        self.prune(now_s)
        if not report.is_live(now_s) or report.report_id in self._reports:
            return False
        self._reports[report.report_id] = report
        return True

    def prune(self, now_s: float) -> None:
        self._reports = {key: value for key, value in self._reports.items() if value.is_live(now_s)}

    def confirmed_slowdown(self, road_segment_id: str, direction_deg: float, now_s: float,
                           min_independent_origins: int = 2) -> bool:
        self.prune(now_s)
        origins = {report.origin_id for report in self._reports.values()
                   if report.road_segment_id == road_segment_id
                   and abs((report.direction_deg - direction_deg + 180) % 360 - 180) <= 35
                   and report.speed_mps < 4.0}
        return len(origins) >= min_independent_origins


@dataclass
class TrafficHazardReport:
    hazard_id: str
    hazard_type: str  # GNSS_OUTAGE, SPEED_BREAKER, POTHOLE, TRAFFIC_JAM
    severity: float  # 0.0 to 1.0
    latitude: float
    longitude: float
    heading_deg: float
    observed_at_s: float
    expires_at_s: float
    source_vehicle_id: str
    confidence: float = 0.5
    confirmation_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "hazard_id": self.hazard_id,
            "hazard_type": self.hazard_type,
            "severity": round(self.severity, 2),
            "latitude": round(self.latitude, 7),
            "longitude": round(self.longitude, 7),
            "heading_deg": round(self.heading_deg, 1),
            "observed_at_s": round(self.observed_at_s, 2),
            "expires_at_s": round(self.expires_at_s, 2),
            "source_vehicle_id": self.source_vehicle_id,
            "confidence": round(self.confidence, 3),
            "confirmation_count": self.confirmation_count,
        }


class HazardStore:
    """In-memory spatial-temporal hazard repository with clustering and confidence decay."""

    def __init__(self, cluster_radius_m: float = 35.0):
        self.cluster_radius_m = cluster_radius_m
        self._hazards: dict[str, TrafficHazardReport] = {}

    def ingest(self, report: TrafficHazardReport, now_s: float) -> TrafficHazardReport:
        self.prune(now_s)

        # Check for nearby existing hazard of same type
        matched_id = None
        for hid, existing in self._hazards.items():
            if existing.hazard_type != report.hazard_type:
                continue
            # Flat earth distance in meters
            dlat = (report.latitude - existing.latitude) * 111132.954
            dlon = (report.longitude - existing.longitude) * 111132.954 * math.cos(math.radians(existing.latitude))
            dist = math.hypot(dlat, dlon)
            if dist <= self.cluster_radius_m:
                matched_id = hid
                break

        if matched_id is not None:
            existing = self._hazards[matched_id]
            # Cluster and boost confidence
            new_count = existing.confirmation_count + 1
            new_conf = min(0.99, 1.0 - (1.0 - existing.confidence) * (1.0 - report.confidence))
            new_sev = max(existing.severity, report.severity)
            new_expires = max(existing.expires_at_s, report.expires_at_s)

            merged = TrafficHazardReport(
                hazard_id=existing.hazard_id,
                hazard_type=existing.hazard_type,
                severity=new_sev,
                latitude=(existing.latitude * existing.confirmation_count + report.latitude) / new_count,
                longitude=(existing.longitude * existing.confirmation_count + report.longitude) / new_count,
                heading_deg=report.heading_deg,
                observed_at_s=report.observed_at_s,
                expires_at_s=new_expires,
                source_vehicle_id=f"cluster_{new_count}",
                confidence=new_conf,
                confirmation_count=new_count,
            )
            self._hazards[matched_id] = merged
            return merged
        else:
            self._hazards[report.hazard_id] = report
            return report

    def prune(self, now_s: float) -> None:
        self._hazards = {k: v for k, v in self._hazards.items() if v.expires_at_s > now_s}

    def get_active(self, lat: float, lon: float, radius_m: float = 500.0, now_s: float | None = None) -> list[TrafficHazardReport]:
        import time
        t_now = now_s if now_s is not None else time.time()
        self.prune(t_now)

        results = []
        for h in self._hazards.values():
            dlat = (h.latitude - lat) * 111132.954
            dlon = (h.longitude - lon) * 111132.954 * math.cos(math.radians(lat))
            dist = math.hypot(dlat, dlon)
            if dist <= radius_m:
                results.append(h)

        results.sort(key=lambda h: h.confidence, reverse=True)
        return results
