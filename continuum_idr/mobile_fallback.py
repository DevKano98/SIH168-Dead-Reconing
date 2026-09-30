from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .alignment import MountChangeDetector
from .engine import IDREngine
from .maps import CandidateTracker, RoadGraph
from .model import MotionModelBundle
from .profiles import PROFILES, RoadSurfaceDetector, SurfaceEvent, VehicleProfile
from .types import EngineConfig, GNSSFix, IMUSample, NavigationState, TrackingMode


class FallbackState(str, Enum):
    GNSS_HEALTHY = "GNSS_HEALTHY"
    OUTAGE_PENDING = "OUTAGE_PENDING"
    FALLBACK_ACTIVE = "FALLBACK_ACTIVE"
    RECOVERING = "RECOVERING"


@dataclass
class MobileLocationUpdate:
    timestamp_s: float
    latitude_deg: float
    longitude_deg: float
    speed_mps: float
    bearing_deg: float
    accuracy_m: float
    provider: str  # "gps" or "continuum_idr"
    is_fallback: bool
    fallback_state: FallbackState
    road_segment_id: Optional[str] = None
    road_orthogonal_dist_m: Optional[float] = None
    surface_event: Optional[str] = None
    mount_displaced: bool = False
    active_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp_s": self.timestamp_s,
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "speed_mps": self.speed_mps,
            "speed_kmh": self.speed_mps * 3.6,
            "bearing_deg": self.bearing_deg,
            "accuracy_m": self.accuracy_m,
            "provider": self.provider,
            "is_fallback": self.is_fallback,
            "fallback_state": self.fallback_state.value,
            "road_segment_id": self.road_segment_id,
            "road_orthogonal_dist_m": self.road_orthogonal_dist_m,
            "surface_event": self.surface_event,
            "mount_displaced": self.mount_displaced,
            "active_flags": list(self.active_flags),
        }


class MobileFallbackEngine:
    """Production-grade mobile navigation fallback provider.

    Wraps IDREngine, RoadGraph candidate tracker, MountChangeDetector, and
    RoadSurfaceDetector to deliver an uninterrupted stream of MobileLocationUpdates.
    When GNSS drops or degrades, Continuum IDR smoothly takes over with zero visual
    coordinate teleportation.
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        model_bundle: Optional[MotionModelBundle] = None,
        road_graph: Optional[RoadGraph] = None,
        gnss_timeout_s: float = 2.0,
        gnss_accuracy_threshold_m: float = 25.0,
    ) -> None:
        self.config = config or EngineConfig()
        if model_bundle is None:
            # Try to load default trained bundle if exists
            default_path = Path("models/motion_p0")
            if default_path.exists():
                model_bundle = MotionModelBundle.load(str(default_path))
            else:
                model_bundle = MotionModelBundle.create_mock_bundle()

        self.model_bundle = model_bundle
        self.engine = IDREngine(self.config, self.model_bundle)
        self.road_graph = road_graph
        self.candidate_tracker = CandidateTracker(road_graph) if road_graph else None
        self.surface_detector = RoadSurfaceDetector()
        self.mount_detector = MountChangeDetector(angle_threshold_deg=15.0)

        self.gnss_timeout_s = gnss_timeout_s
        self.gnss_accuracy_threshold_m = gnss_accuracy_threshold_m

        self.fallback_state = FallbackState.GNSS_HEALTHY
        self.last_gnss_fix: Optional[GNSSFix] = None
        self.last_gnss_time_s: float = -1.0
        self.latest_nav_state: Optional[NavigationState] = None
        self.last_location_update: Optional[MobileLocationUpdate] = None
        self.last_mount_change_flag = False
        self.last_surface_event: Optional[SurfaceEvent] = None

    def on_gnss(self, fix: GNSSFix) -> MobileLocationUpdate:
        """Handle incoming GNSS fix from mobile OS location manager."""
        self.last_gnss_time_s = fix.timestamp_s
        self.last_gnss_fix = fix

        # Pass fix into IDR engine for Kalman innovation gating and filter updates
        nav_state = self.engine.on_gnss(fix)
        self.latest_nav_state = nav_state

        is_accurate = fix.horizontal_accuracy_m <= self.gnss_accuracy_threshold_m
        if nav_state.last_gnss_decision.startswith("ACCEPT") and is_accurate:
            if self.fallback_state == FallbackState.FALLBACK_ACTIVE:
                self.fallback_state = FallbackState.RECOVERING
            else:
                self.fallback_state = FallbackState.GNSS_HEALTHY
        else:
            # Degraded accuracy or rejected by innovation gate
            self.fallback_state = FallbackState.FALLBACK_ACTIVE

        # Check map matching if graph is supplied
        road_id = None
        ortho_dist = None
        lat = fix.latitude_deg
        lon = fix.longitude_deg
        bearing = fix.course_deg

        if self.candidate_tracker and nav_state.east_m is not None and nav_state.north_m is not None:
            match = self.candidate_tracker.match(
                nav_state.east_m, nav_state.north_m, heading_deg=bearing, speed_mps=fix.speed_mps
            )
            if match.matched and match.segment_id:
                road_id = match.segment_id
                ortho_dist = match.cross_track_error_m
                if match.snapped_latitude_deg is not None and match.snapped_longitude_deg is not None:
                    lat = match.snapped_latitude_deg
                    lon = match.snapped_longitude_deg

        flags = list(nav_state.health_flags)
        if not is_accurate:
            flags.append("GNSS_ACCURACY_DEGRADED")

        update = MobileLocationUpdate(
            timestamp_s=fix.timestamp_s,
            latitude_deg=lat,
            longitude_deg=lon,
            speed_mps=fix.speed_mps,
            bearing_deg=bearing,
            accuracy_m=fix.horizontal_accuracy_m,
            provider="gps" if self.fallback_state == FallbackState.GNSS_HEALTHY else "continuum_idr",
            is_fallback=self.fallback_state != FallbackState.GNSS_HEALTHY,
            fallback_state=self.fallback_state,
            road_segment_id=road_id,
            road_orthogonal_dist_m=ortho_dist,
            surface_event=self.last_surface_event.event_type if self.last_surface_event else None,
            mount_displaced=self.last_mount_change_flag,
            active_flags=flags,
        )
        self.last_location_update = update
        return update

    def on_imu(self, sample: IMUSample) -> Optional[MobileLocationUpdate]:
        """Handle incoming high-frequency IMU sample (10 Hz - 200 Hz)."""
        # 1. Update mount displacement detector
        align_status = self.mount_detector.update(sample.gravity_mps2)
        self.last_mount_change_flag = align_status.mount_disturbance_detected

        # 2. Propagate EKF and run causal ML motion model
        nav_state = self.engine.on_imu(sample)
        self.latest_nav_state = nav_state

        # 3. Update road surface anomaly shock detector
        speed_est = nav_state.speed_mps if nav_state.speed_mps is not None else 10.0
        self.last_surface_event = self.surface_detector.update(
            sample.timestamp_s, sample.accel_mps2, sample.gravity_mps2, speed_mps=speed_est
        )

        # 4. Check for GNSS outage conditions
        now = sample.timestamp_s
        time_since_fix = now - self.last_gnss_time_s if self.last_gnss_time_s >= 0 else 999.0

        if time_since_fix > self.gnss_timeout_s:
            self.fallback_state = FallbackState.FALLBACK_ACTIVE
        elif time_since_fix > 1.0:
            self.fallback_state = FallbackState.OUTAGE_PENDING

        # If fallback is active or GNSS was lost, produce a synthetic mobile location fix
        if self.fallback_state in (FallbackState.FALLBACK_ACTIVE, FallbackState.OUTAGE_PENDING):
            if nav_state.latitude_deg is None or nav_state.longitude_deg is None:
                return None

            lat = nav_state.latitude_deg
            lon = nav_state.longitude_deg
            bearing = nav_state.heading_deg
            speed = nav_state.speed_mps
            accuracy = nav_state.horizontal_uncertainty_m

            road_id = None
            ortho_dist = None
            if self.candidate_tracker and nav_state.east_m is not None and nav_state.north_m is not None:
                match = self.candidate_tracker.match(
                    nav_state.east_m, nav_state.north_m, heading_deg=bearing, speed_mps=speed
                )
                if match.matched and match.segment_id:
                    road_id = match.segment_id
                    ortho_dist = match.cross_track_error_m
                    if match.snapped_latitude_deg is not None and match.snapped_longitude_deg is not None:
                        lat = match.snapped_latitude_deg
                        lon = match.snapped_longitude_deg

            flags = list(nav_state.health_flags)
            if self.last_mount_change_flag:
                flags.append("MOUNT_TILT_FLAG")

            update = MobileLocationUpdate(
                timestamp_s=sample.timestamp_s,
                latitude_deg=lat,
                longitude_deg=lon,
                speed_mps=speed,
                bearing_deg=bearing,
                accuracy_m=accuracy,
                provider="continuum_idr",
                is_fallback=True,
                fallback_state=self.fallback_state,
                road_segment_id=road_id,
                road_orthogonal_dist_m=ortho_dist,
                surface_event=self.last_surface_event.event_type if self.last_surface_event else None,
                mount_displaced=self.last_mount_change_flag,
                active_flags=flags,
            )
            self.last_location_update = update
            return update

        return None
