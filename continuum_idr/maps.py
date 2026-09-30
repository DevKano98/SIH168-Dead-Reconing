"""Continuum IDR — Offline Road Graph and Map-Matching Engine.

Provides regional road topology indexing, multiple-hypothesis candidate tracking,
cross-track/along-track error computation, road snapping, and ambiguity detection
to eliminate lateral MEMS gyro drift during GNSS outages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .geo import LocalFrame, heading_deg_to_rad, heading_rad_to_deg, wrap_heading_rad


@dataclass(frozen=True)
class RoadNode:
    node_id: str
    latitude_deg: float
    longitude_deg: float
    east_m: float
    north_m: float


@dataclass(frozen=True)
class RoadSegment:
    segment_id: str
    from_node: str
    to_node: str
    start_enu: tuple[float, float]
    end_enu: tuple[float, float]
    heading_deg: float
    length_m: float
    speed_limit_mps: float = 20.0
    lane_count: int = 1
    road_type: str = "primary"  # motorway, primary, secondary, residential, service
    one_way: bool = False

    @property
    def heading_rad(self) -> float:
        return heading_deg_to_rad(self.heading_deg)


@dataclass
class MapMatchResult:
    matched: bool
    segment_id: str | None
    snapped_east_m: float | None
    snapped_north_m: float | None
    snapped_latitude_deg: float | None
    snapped_longitude_deg: float | None
    cross_track_error_m: float
    along_track_distance_m: float
    road_heading_deg: float | None
    heading_divergence_deg: float | None
    match_confidence: float  # 0.0 to 1.0
    is_ambiguous: bool = False
    candidate_count: int = 0
    alternative_segments: list[str] = field(default_factory=list)


class RoadGraph:
    """Regional road network representation with spatial cell indexing."""

    def __init__(self, cell_size_m: float = 100.0, reference_frame: LocalFrame | None = None):
        self.cell_size_m = cell_size_m
        self.reference_frame = reference_frame
        self.nodes: dict[str, RoadNode] = {}
        self.segments: dict[str, RoadSegment] = {}
        # Spatial grid mapping (cell_x, cell_y) -> list of segment_ids
        self._grid: dict[tuple[int, int], list[str]] = {}

    def _cell_coords(self, east_m: float, north_m: float) -> tuple[int, int]:
        return (
            int(math.floor(east_m / self.cell_size_m)),
            int(math.floor(north_m / self.cell_size_m)),
        )

    def add_node(self, node_id: str, lat: float, lon: float, east: float | None = None, north: float | None = None) -> RoadNode:
        if east is None or north is None:
            if self.reference_frame is None:
                self.reference_frame = LocalFrame(lat, lon)
            east, north = self.reference_frame.to_enu(lat, lon)
        node = RoadNode(node_id, lat, lon, float(east), float(north))
        self.nodes[node_id] = node
        return node

    def add_segment(
        self,
        segment_id: str,
        from_node_id: str,
        to_node_id: str,
        speed_limit_mps: float = 20.0,
        lane_count: int = 1,
        road_type: str = "primary",
        one_way: bool = False,
    ) -> RoadSegment:
        from_node = self.nodes[from_node_id]
        to_node = self.nodes[to_node_id]
        de = to_node.east_m - from_node.east_m
        dn = to_node.north_m - from_node.north_m
        length = math.hypot(de, dn)
        # Bearing clockwise from North: atan2(de, dn)
        bearing = wrap_heading_rad(math.atan2(de, dn))
        heading_deg = heading_rad_to_deg(bearing)

        start_enu = (from_node.east_m, from_node.north_m)
        end_enu = (to_node.east_m, to_node.north_m)

        segment = RoadSegment(
            segment_id=segment_id,
            from_node=from_node_id,
            to_node=to_node_id,
            start_enu=start_enu,
            end_enu=end_enu,
            heading_deg=heading_deg,
            length_m=length,
            speed_limit_mps=speed_limit_mps,
            lane_count=lane_count,
            road_type=road_type,
            one_way=one_way,
        )
        self.segments[segment_id] = segment

        # Register in spatial grid along bounding box + margin
        min_e = min(start_enu[0], end_enu[0])
        max_e = max(start_enu[0], end_enu[0])
        min_n = min(start_enu[1], end_enu[1])
        max_n = max(start_enu[1], end_enu[1])

        c_min_x, c_min_y = self._cell_coords(min_e, min_n)
        c_max_x, c_max_y = self._cell_coords(max_e, max_n)

        for cx in range(c_min_x, c_max_x + 1):
            for cy in range(c_min_y, c_max_y + 1):
                self._grid.setdefault((cx, cy), []).append(segment_id)

        return segment

    def get_candidate_segments(self, east_m: float, north_m: float, radius_m: float = 50.0) -> list[RoadSegment]:
        """Find candidate road segments within search radius."""
        cx_min, cy_min = self._cell_coords(east_m - radius_m, north_m - radius_m)
        cx_max, cy_max = self._cell_coords(east_m + radius_m, north_m + radius_m)

        seen_ids: set[str] = set()
        candidates: list[RoadSegment] = []

        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                for seg_id in self._grid.get((cx, cy), []):
                    if seg_id not in seen_ids:
                        seen_ids.add(seg_id)
                        candidates.append(self.segments[seg_id])

        return candidates

    @classmethod
    def create_synthetic_corridor(
        cls,
        origin_lat: float = 52.4,
        origin_lon: float = -1.5,
        length_m: float = 5000.0,
        lane_count: int = 2,
    ) -> "RoadGraph":
        """Build a synthetic test road network corridor with main road and parallel service road."""
        frame = LocalFrame(origin_lat, origin_lon)
        graph = cls(cell_size_m=100.0, reference_frame=frame)

        # Main road running East-West (heading 90 deg)
        step = 250.0
        steps = int(length_m / step)
        for i in range(steps + 1):
            east = i * step
            north = 0.0
            lat, lon = frame.to_wgs84(east, north)
            graph.add_node(f"main_{i}", lat, lon, east, north)
            if i > 0:
                graph.add_segment(
                    segment_id=f"seg_main_{i-1}_{i}",
                    from_node_id=f"main_{i-1}",
                    to_node_id=f"main_{i}",
                    speed_limit_mps=25.0,
                    lane_count=lane_count,
                    road_type="motorway",
                )

        # Parallel service road 25m North
        for i in range(steps + 1):
            east = i * step
            north = 25.0
            lat, lon = frame.to_wgs84(east, north)
            graph.add_node(f"service_{i}", lat, lon, east, north)
            if i > 0:
                graph.add_segment(
                    segment_id=f"seg_service_{i-1}_{i}",
                    from_node_id=f"service_{i-1}",
                    to_node_id=f"service_{i}",
                    speed_limit_mps=12.0,
                    lane_count=1,
                    road_type="service",
                )

        return graph


class CandidateTracker:
    """Tracks road candidates and projects dead reckoning states onto road topologies."""

    def __init__(
        self,
        road_graph: RoadGraph,
        search_radius_m: float = 40.0,
        sigma_dist_m: float = 12.0,
        sigma_heading_deg: float = 25.0,
        min_confidence_thresh: float = 0.20,
        ambiguity_margin: float = 0.15,
    ):
        self.graph = road_graph
        self.search_radius_m = search_radius_m
        self.sigma_dist_m = sigma_dist_m
        self.sigma_heading_deg = sigma_heading_deg
        self.min_confidence_thresh = min_confidence_thresh
        self.ambiguity_margin = ambiguity_margin
        self._last_matched_segment_id: str | None = None

    @staticmethod
    def project_point_to_segment(
        px: float, py: float, x1: float, y1: float, x2: float, y2: float
    ) -> tuple[float, float, float, float]:
        """Project (px, py) onto segment (x1, y1)-(x2, y2).
        
        Returns:
            snapped_x, snapped_y, cross_track_dist, along_track_dist
        """
        dx = x2 - x1
        dy = y2 - y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq < 1e-9:
            dist = math.hypot(px - x1, py - y1)
            return x1, y1, dist, 0.0

        # Parameter t along the line segment
        t = ((px - x1) * dx + (py - y1) * dy) / seg_len_sq
        t_clamped = max(0.0, min(1.0, t))

        snapped_x = x1 + t_clamped * dx
        snapped_y = y1 + t_clamped * dy

        # Cross track perpendicular distance (signed: positive = right of road vector)
        # Vector cross product: dx * (py - y1) - dy * (px - x1)
        cross_prod = dx * (py - y1) - dy * (px - x1)
        signed_cross = cross_prod / math.sqrt(seg_len_sq)

        along_track = t_clamped * math.sqrt(seg_len_sq)
        return snapped_x, snapped_y, abs(signed_cross), along_track

    def match(
        self,
        east_m: float,
        north_m: float,
        heading_deg: float | None = None,
        speed_mps: float | None = None,
    ) -> MapMatchResult:
        """Find best matching road candidate."""
        candidates = self.graph.get_candidate_segments(east_m, north_m, radius_m=self.search_radius_m)
        if not candidates:
            return MapMatchResult(
                matched=False,
                segment_id=None,
                snapped_east_m=None,
                snapped_north_m=None,
                snapped_latitude_deg=None,
                snapped_longitude_deg=None,
                cross_track_error_m=math.nan,
                along_track_distance_m=math.nan,
                road_heading_deg=None,
                heading_divergence_deg=None,
                match_confidence=0.0,
                is_ambiguous=False,
                candidate_count=0,
            )

        scored_candidates: list[tuple[float, RoadSegment, float, float, float, float]] = []

        for seg in candidates:
            sx, sy, cross_dist, along_dist = self.project_point_to_segment(
                east_m, north_m, seg.start_enu[0], seg.start_enu[1], seg.end_enu[0], seg.end_enu[1]
            )

            # Distance likelihood
            p_dist = math.exp(-0.5 * (cross_dist / self.sigma_dist_m) ** 2)

            # Heading likelihood
            p_heading = 1.0
            heading_div = 0.0
            if heading_deg is not None and math.isfinite(heading_deg) and (speed_mps or 0.0) >= 1.5:
                # Wrap heading difference to [-180, 180]
                diff = (heading_deg - seg.heading_deg + 180.0) % 360.0 - 180.0
                if not seg.one_way:
                    # If bidirectional, test both directions
                    opp_diff = (heading_deg - (seg.heading_deg + 180.0) + 180.0) % 360.0 - 180.0
                    if abs(opp_diff) < abs(diff):
                        diff = opp_diff
                heading_div = abs(diff)
                p_heading = math.exp(-0.5 * (heading_div / self.sigma_heading_deg) ** 2)

            # Temporal continuity bonus if staying on same segment
            continuity_bonus = 1.25 if seg.segment_id == self._last_matched_segment_id else 1.0

            total_score = p_dist * p_heading * continuity_bonus
            scored_candidates.append((total_score, seg, sx, sy, cross_dist, along_dist))

        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_seg, best_sx, best_sy, best_cross, best_along = scored_candidates[0]

        # Normalization
        score_sum = sum(item[0] for item in scored_candidates)
        confidence = float(best_score / max(score_sum, 1e-6))

        if confidence < self.min_confidence_thresh or best_cross > self.search_radius_m:
            return MapMatchResult(
                matched=False,
                segment_id=None,
                snapped_east_m=None,
                snapped_north_m=None,
                snapped_latitude_deg=None,
                snapped_longitude_deg=None,
                cross_track_error_m=best_cross,
                along_track_distance_m=best_along,
                road_heading_deg=best_seg.heading_deg,
                heading_divergence_deg=None,
                match_confidence=confidence,
                is_ambiguous=False,
                candidate_count=len(scored_candidates),
            )

        # Check ambiguity: second best close in score
        is_ambiguous = False
        alternatives = []
        if len(scored_candidates) > 1:
            second_score = scored_candidates[1][0]
            second_conf = float(second_score / max(score_sum, 1e-6))
            if (confidence - second_conf) < self.ambiguity_margin:
                is_ambiguous = True
                alternatives = [scored_candidates[1][1].segment_id]

        self._last_matched_segment_id = best_seg.segment_id

        # Convert snapped ENU to WGS84
        snapped_lat, snapped_lon = None, None
        if self.graph.reference_frame is not None:
            snapped_lat, snapped_lon = self.graph.reference_frame.to_wgs84(best_sx, best_sy)

        diff = 0.0
        if heading_deg is not None:
            diff = abs((heading_deg - best_seg.heading_deg + 180.0) % 360.0 - 180.0)

        return MapMatchResult(
            matched=True,
            segment_id=best_seg.segment_id,
            snapped_east_m=best_sx,
            snapped_north_m=best_sy,
            snapped_latitude_deg=snapped_lat,
            snapped_longitude_deg=snapped_lon,
            cross_track_error_m=best_cross,
            along_track_distance_m=best_along,
            road_heading_deg=best_seg.heading_deg,
            heading_divergence_deg=diff,
            match_confidence=confidence,
            is_ambiguous=is_ambiguous,
            candidate_count=len(scored_candidates),
            alternative_segments=alternatives,
        )
