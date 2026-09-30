"""Privacy-preserving, short-lived cooperative traffic reports.

Transport is deliberately separate: BLE, Wi-Fi Direct and an internet gateway
can all carry the same validated packet.  A relay is never counted as a new
observation.
"""
from __future__ import annotations

import hashlib
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
