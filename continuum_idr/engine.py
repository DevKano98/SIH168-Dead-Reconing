from __future__ import annotations

import math
from collections import deque
from dataclasses import replace
from typing import Any

import numpy as np

from .alignment import MountChangeDetector, OnlineGyroBiasEstimator, StopHysteresisFilter
from .features import linear_acceleration
from .geo import LocalFrame, heading_deg_to_rad, heading_rad_to_deg, wrap_heading_rad
from .maps import CandidateTracker, MapMatchResult, RoadGraph
from .model import MotionModelBundle
from .profiles import CAR_PROFILE, PROFILES, RoadSurfaceDetector, SurfaceEvent, VehicleProfile
from .types import EngineConfig, GNSSFix, IMUSample, NavigationState, TrackingMode


class IDREngine:
    """Causal planar GNSS/IMU estimator used by the P0 prototype.

    Reference vehicle data is deliberately absent from this API.
    """

    def __init__(self, first: Any = None, second: Any = None):
        if isinstance(first, EngineConfig) or (first is None and second is not None):
            self.config = first or EngineConfig()
            self.model = second
        elif isinstance(second, EngineConfig):
            self.model = first
            self.config = second
        else:
            self.model = first
            self.config = second or EngineConfig()
        if self.model is None:
            raise ValueError("motion model must be provided")
        if abs(self.model.sample_rate_hz - self.config.imu_rate_hz) > 1e-6:
            raise ValueError("model and engine IMU rates do not match")
        self._window: deque[np.ndarray] = deque(maxlen=self.model.window_samples)
        self.reset("initial")

    def reset(self, reason: str = "manual") -> None:
        self._x: np.ndarray | None = None  # east, north, speed, heading-clockwise-from-north
        self._p: np.ndarray | None = None
        self._frame: LocalFrame | None = None
        self._last_imu_s: float | None = None
        self._last_model_s: float | None = None
        self._last_gnss_s: float | None = None
        self._last_accepted_gnss_s: float | None = None
        self._mode = TrackingMode.UNINITIALIZED
        self._sequence = 0
        self._health: set[str] = set()
        self._last_gnss_decision = "NONE"
        self._recovery_count = 0
        self._consecutive_rejections = 0
        self._prev_fix_enu: np.ndarray | None = None
        self._window.clear()
        self._last_reset_reason = reason
        self._stop_hysteresis = StopHysteresisFilter()
        self._mount_detector = MountChangeDetector()
        self._bias_estimator = OnlineGyroBiasEstimator()
        self._surface_detector = RoadSurfaceDetector()
        self._vehicle_profile: VehicleProfile = PROFILES.get(self.config.vehicle_profile, CAR_PROFILE)
        self._candidate_tracker: CandidateTracker | None = None
        self._last_match_result: MapMatchResult | None = None
        self._last_surface_event: SurfaceEvent | None = None

    def set_road_graph(self, road_graph: RoadGraph) -> None:
        """Bind an offline road graph to enable multiple-hypothesis map matching."""
        self._candidate_tracker = CandidateTracker(road_graph)

    @property
    def estimated_gyro_bias_degps(self) -> float:
        return self._bias_estimator.estimated_bias_degps

    @property
    def initialized(self) -> bool:
        return self._x is not None

    def on_imu(self, sample: IMUSample) -> NavigationState:
        values = np.asarray(sample.accel_mps2 + sample.gyro_radps, dtype=float)
        if not np.isfinite(values).all():
            self._health.add("INVALID_IMU")
            return self.get_state(sample.timestamp_s)
        gravity = None if sample.gravity_mps2 is None else np.asarray(sample.gravity_mps2, dtype=float)
        linear = linear_acceleration(np.asarray(sample.accel_mps2, dtype=float), gravity)
        gyro = np.asarray(sample.gyro_radps, dtype=float)
        self._window.append(np.concatenate([linear, gyro]))

        # Check surface condition
        surf = self._surface_detector.update(
            sample.timestamp_s,
            sample.accel_mps2,
            sample.gravity_mps2,
            speed_mps=float(self._x[2]) if self._x is not None else 10.0,
        )
        if surf is not None:
            self._last_surface_event = surf
            self._health.add(surf.event_type)

        # Mount change detection
        if self.config.enable_mount_detector and sample.gravity_mps2 is not None:
            is_stat = self._stop_hysteresis.is_stopped
            mount_status = self._mount_detector.update(sample.gravity_mps2, is_stationary=is_stat)
            if mount_status.mount_disturbance_detected:
                self._health.add("SUSPECT_ALIGNMENT")
            elif mount_status.is_aligned:
                self._health.discard("SUSPECT_ALIGNMENT")

        # Gyro yaw processing with bias compensation and lean-angle correction
        raw_yaw = float(gyro[self.config.gyro_yaw_index])
        yaw_rate = raw_yaw
        if self.config.enable_gyro_bias_adaptation:
            yaw_rate = self._bias_estimator.correct(yaw_rate)
        if self._vehicle_profile.lean_angle_compensation and self._x is not None:
            yaw_rate = self._vehicle_profile.compensate_yaw_rate(
                tuple(float(v) for v in gyro), speed_mps=float(self._x[2]), yaw_index=self.config.gyro_yaw_index
            )

        if self._last_imu_s is not None:
            dt = sample.timestamp_s - self._last_imu_s
            if dt <= 0:
                self._health.add("OUT_OF_ORDER_IMU")
                return self.get_state(sample.timestamp_s)
            if dt > self.config.max_imu_gap_s:
                self._health.add("IMU_GAP")
                if self._p is not None:
                    self._p[:2, :2] += np.eye(2) * min(dt * dt * 4.0, 100.0)
            if self._x is not None:
                self._propagate(
                    min(dt, self.config.max_imu_gap_s),
                    float(linear[0]),
                    yaw_rate,
                )
        self._last_imu_s = sample.timestamp_s

        if (
            self.config.model_update_hz > 0
            and self._x is not None
            and len(self._window) == self.model.window_samples
            and (self._last_model_s is None or sample.timestamp_s - self._last_model_s >= (1.0 / self.config.model_update_hz) - 1e-6)
        ):
            prediction = self.model.predict(np.stack(self._window))
            variance = max(prediction.speed_std_mps**2, 0.25)
            self._scalar_update(2, prediction.speed_mps, variance)

            # Guarded ZUPT with hysteresis
            if self.config.enable_zupt_hysteresis:
                linear_arr = np.asarray([w[:3] for w in self._window], dtype=float)
                acc_var = float(np.var(linear_arr[:, 0])) if len(self._window) > 5 else 0.0
                is_stop = self._stop_hysteresis.update(
                    prediction.stop_probability, current_speed_mps=float(self._x[2]), accel_variance=acc_var
                )
            else:
                is_stop = prediction.stop_probability >= 0.85 and (self._x[2] < 2.5 or prediction.stop_probability >= 0.95)

            if is_stop:
                self._scalar_update(2, 0.0, 0.05**2)
                self._x[2] = 0.0
                if self.config.enable_gyro_bias_adaptation:
                    self._bias_estimator.update_from_zupt(raw_yaw)

            self._x[2] = float(np.clip(self._x[2], 0.0, self.config.max_speed_mps))
            self._last_model_s = sample.timestamp_s

        # Map matching constraint update
        if self.config.enable_map_matching and self._candidate_tracker is not None and self._x is not None:
            match = self._candidate_tracker.match(
                float(self._x[0]),
                float(self._x[1]),
                heading_rad_to_deg(float(self._x[3])),
                float(self._x[2]),
            )
            self._last_match_result = match
            if match.matched and not match.is_ambiguous and match.cross_track_error_m < 25.0:
                h_pos = np.zeros((2, 4), dtype=float)
                h_pos[0, 0] = 1.0
                h_pos[1, 1] = 1.0
                z_snap = np.asarray([match.snapped_east_m, match.snapped_north_m], dtype=float)
                r_snap = np.eye(2) * (max(match.cross_track_error_m * 0.4, 2.5) ** 2)
                self._vector_update(h_pos, z_snap, r_snap)

        self._update_mode(sample.timestamp_s)
        return self.get_state(sample.timestamp_s)

    def on_gnss(self, fix: GNSSFix) -> NavigationState:
        self._last_gnss_s = fix.timestamp_s
        if self._last_accepted_gnss_s is not None and fix.timestamp_s <= self._last_accepted_gnss_s:
            self._last_gnss_decision = "REJECT_OUT_OF_ORDER"
            self._health.add("GNSS_REJECTED")
            return self.get_state(fix.timestamp_s)
        if not all(math.isfinite(v) for v in (fix.latitude_deg, fix.longitude_deg)):
            self._last_gnss_decision = "REJECT_INVALID"
            self._health.add("GNSS_REJECTED")
            return self.get_state(fix.timestamp_s)
        if not (-90 <= fix.latitude_deg <= 90 and -180 <= fix.longitude_deg <= 180):
            self._last_gnss_decision = "REJECT_RANGE"
            self._health.add("GNSS_REJECTED")
            return self.get_state(fix.timestamp_s)

        if self._frame is None:
            self._frame = LocalFrame(fix.latitude_deg, fix.longitude_deg)
        east, north = self._frame.to_enu(fix.latitude_deg, fix.longitude_deg)
        z = np.asarray([east, north], dtype=float)

        if self._x is None:
            speed = max(0.0, float(fix.speed_mps or 0.0))
            heading_known = (
                fix.course_deg is not None
                and math.isfinite(fix.course_deg)
                and speed >= 2.0
            )
            heading = heading_deg_to_rad(float(fix.course_deg)) if heading_known else 0.0
            self._x = np.asarray([east, north, speed, heading], dtype=float)
            heading_std = math.radians(
                self.config.initial_heading_std_deg if heading_known else 180.0
            )
            self._p = np.diag(
                [
                    self.config.initial_position_std_m**2,
                    self.config.initial_position_std_m**2,
                    self.config.initial_speed_std_mps**2,
                    heading_std**2,
                ]
            )
            self._last_accepted_gnss_s = fix.timestamp_s
            self._last_gnss_decision = "ACCEPT_INITIAL"
            self._mode = TrackingMode.GNSS_AIDED if heading_known else TrackingMode.ALIGNING
            self._prev_fix_enu = z.copy()
            return self.get_state(fix.timestamp_s)

        assert self._p is not None

        # Check alignment from consecutive fixes if heading was uninitialized
        if self._mode == TrackingMode.ALIGNING and self._prev_fix_enu is not None:
            delta = z - self._prev_fix_enu
            dist = float(np.linalg.norm(delta))
            if dist >= 6.0 or (fix.speed_mps is not None and float(fix.speed_mps) >= 2.0):
                bearing = math.atan2(delta[0], delta[1])
                if (
                    fix.course_deg is not None
                    and math.isfinite(fix.course_deg)
                    and fix.speed_mps is not None
                    and float(fix.speed_mps) >= 2.0
                ):
                    bearing = heading_deg_to_rad(float(fix.course_deg))
                self._x[3] = wrap_heading_rad(bearing)
                self._p[3, 3] = math.radians(self.config.initial_heading_std_deg) ** 2
                self._mode = TrackingMode.GNSS_AIDED

        accuracy = max(float(fix.horizontal_accuracy_m or 8.0), self.config.min_gnss_std_m)
        innovation = z - self._x[:2]
        s = self._p[:2, :2] + np.eye(2) * accuracy**2
        nis = float(innovation.T @ np.linalg.solve(s, innovation))
        gate = self.config.gnss_gate_sigma**2

        was_outage = self._last_accepted_gnss_s is None or (
            fix.timestamp_s - self._last_accepted_gnss_s > self.config.gnss_timeout_s
        )
        in_outage_mode = was_outage or (self._mode == TrackingMode.DEAD_RECKONING)

        # Allow smooth recovery re-entry if coming out of outage / dead reckoning
        recovery_candidate = in_outage_mode and (
            nis <= max(gate * 4.0, 100.0) or float(np.linalg.norm(innovation)) < 150.0
        )

        if nis > gate and not recovery_candidate:
            self._last_gnss_decision = f"REJECT_INNOVATION_{nis:.1f}"
            self._health.add("GNSS_REJECTED")
            self._consecutive_rejections += 1
            self._recovery_count = 0
            self._update_mode(fix.timestamp_s)
            return self.get_state(fix.timestamp_s)

        # Measurement noise matrix (inflated on recovery fix for smooth pull)
        meas_r = np.eye(2) * (accuracy**2 if not in_outage_mode else max(accuracy, 12.0) ** 2)
        h = np.zeros((2, 4), dtype=float)
        h[0, 0] = 1.0
        h[1, 1] = 1.0
        self._vector_update(h, z, meas_r)

        if fix.speed_mps is not None and math.isfinite(fix.speed_mps):
            self._scalar_update(2, max(0.0, float(fix.speed_mps)), max(0.5, accuracy * 0.08) ** 2)
        if fix.course_deg is not None and math.isfinite(fix.course_deg) and self._x[2] > 2.0:
            measured = heading_deg_to_rad(float(fix.course_deg))
            residual = (measured - self._x[3] + math.pi) % (2 * math.pi) - math.pi
            self._scalar_update(3, self._x[3] + residual, math.radians(8.0) ** 2)
            self._x[3] = wrap_heading_rad(float(self._x[3]))

        self._prev_fix_enu = z.copy()
        self._last_accepted_gnss_s = fix.timestamp_s
        self._last_gnss_decision = "ACCEPT"
        self._health.discard("GNSS_REJECTED")
        self._consecutive_rejections = 0

        if was_outage or self._mode == TrackingMode.DEAD_RECKONING:
            self._recovery_count += 1
            self._mode = TrackingMode.RECOVERING
            if self._recovery_count >= self.config.recovery_fixes:
                self._mode = TrackingMode.GNSS_AIDED
                self._recovery_count = 0
        elif self._mode == TrackingMode.RECOVERING:
            self._recovery_count += 1
            if self._recovery_count >= self.config.recovery_fixes:
                self._mode = TrackingMode.GNSS_AIDED
                self._recovery_count = 0
        elif self._mode != TrackingMode.ALIGNING:
            self._mode = TrackingMode.GNSS_AIDED

        return self.get_state(fix.timestamp_s)

    def tick(self, timestamp_s: float) -> NavigationState:
        self._update_mode(timestamp_s)
        return self.get_state(timestamp_s)

    def _propagate(self, dt: float, accel_forward: float, gyro_z: float) -> None:
        assert self._x is not None and self._p is not None
        east, north, speed, heading = self._x
        yaw_rate = self.config.gyro_z_sign * gyro_z
        next_speed = float(np.clip(speed + accel_forward * dt, 0.0, self.config.max_speed_mps))
        mid_speed = 0.5 * (speed + next_speed)
        mid_heading = heading + 0.5 * yaw_rate * dt
        east += mid_speed * math.sin(mid_heading) * dt
        north += mid_speed * math.cos(mid_heading) * dt
        heading = wrap_heading_rad(heading + yaw_rate * dt)
        self._x[:] = [east, north, next_speed, heading]

        f = np.eye(4)
        f[0, 2] = math.sin(mid_heading) * dt
        f[0, 3] = mid_speed * math.cos(mid_heading) * dt
        f[1, 2] = math.cos(mid_heading) * dt
        f[1, 3] = -mid_speed * math.sin(mid_heading) * dt

        pos_noise = (
            (0.05**2) * dt
            if self._mode != TrackingMode.DEAD_RECKONING
            else ((0.05**2) + (self.config.outage_covariance_inflation * max(mid_speed, 1.0)) ** 2) * dt
        )
        q = np.diag(
            [
                pos_noise,
                pos_noise,
                self.config.speed_process_std_mps**2 * dt,
                self.config.yaw_process_std_radps**2 * dt,
            ]
        )
        self._p = f @ self._p @ f.T + q

    def _scalar_update(self, index: int, value: float, variance: float) -> None:
        assert self._x is not None and self._p is not None
        h = np.zeros((1, 4), dtype=float)
        h[0, index] = 1.0
        self._vector_update(h, np.asarray([value], dtype=float), np.asarray([[variance]], dtype=float))

    def _vector_update(self, h: np.ndarray, z: np.ndarray, r: np.ndarray) -> None:
        assert self._x is not None and self._p is not None
        innovation = z - h @ self._x
        s = h @ self._p @ h.T + r
        k = self._p @ h.T @ np.linalg.inv(s)
        self._x = self._x + k @ innovation
        identity = np.eye(4)
        # Joseph form preserves symmetry/positive semidefiniteness better.
        a = identity - k @ h
        self._p = a @ self._p @ a.T + k @ r @ k.T
        self._p = 0.5 * (self._p + self._p.T)

    def _update_mode(self, timestamp_s: float) -> None:
        if self._x is None:
            self._mode = TrackingMode.UNINITIALIZED
            return
        if self._last_accepted_gnss_s is None or timestamp_s - self._last_accepted_gnss_s > self.config.gnss_timeout_s:
            self._mode = TrackingMode.DEAD_RECKONING

    def on_wheel_speed(self, sample: Any) -> NavigationState:
        """Fuse vehicle CAN bus wheel speed odometry into Kalman filter."""
        if self._x is None:
            return self.get_state(sample.timestamp_s)
        from .odometry import CANOdometryAdapter
        if not hasattr(self, "_can_adapter"):
            self._can_adapter = CANOdometryAdapter()
        imu_acc = float(self._window[-1][0]) if self._window else None
        odom = self._can_adapter.process(sample, imu_longitudinal_accel_mps2=imu_acc)
        self._scalar_update(2, odom.vehicle_speed_mps, odom.speed_std_mps**2)
        if odom.is_slipping:
            self._health.add("WHEEL_SLIP")
        else:
            self._health.discard("WHEEL_SLIP")
        return self.get_state(sample.timestamp_s)

    def get_state(self, timestamp_s: float | None = None) -> NavigationState:
        now = float(
            timestamp_s
            if timestamp_s is not None
            else self._last_imu_s
            if self._last_imu_s is not None
            else self._last_gnss_s
            if self._last_gnss_s is not None
            else 0.0
        )
        self._sequence += 1
        if self._x is None or self._p is None or self._frame is None:
            return NavigationState(
                now,
                self._sequence,
                self._mode,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "ESTIMATING" if self._window else "UNAVAILABLE",
                tuple(sorted(self._health)),
                self._last_gnss_decision,
            )
        latitude, longitude = self._frame.to_wgs84(float(self._x[0]), float(self._x[1]))
        eig = max(float(np.linalg.eigvalsh(self._p[:2, :2]).max()), 0.0)
        uncertainty95 = math.sqrt(5.991 * eig)
        age = None if self._last_accepted_gnss_s is None else max(0.0, now - self._last_accepted_gnss_s)

        snapped_lat = self._last_match_result.snapped_latitude_deg if self._last_match_result and self._last_match_result.matched else None
        snapped_lon = self._last_match_result.snapped_longitude_deg if self._last_match_result and self._last_match_result.matched else None
        matched_id = self._last_match_result.segment_id if self._last_match_result and self._last_match_result.matched else None
        cross_err = self._last_match_result.cross_track_error_m if self._last_match_result and self._last_match_result.matched else None
        gyro_bias = self._bias_estimator.estimated_bias_degps if self.config.enable_gyro_bias_adaptation else None
        surface = self._last_surface_event.event_type if self._last_surface_event else None

        return NavigationState(
            now,
            self._sequence,
            self._mode,
            float(self._x[0]),
            float(self._x[1]),
            latitude,
            longitude,
            float(self._x[2]),
            heading_rad_to_deg(float(self._x[3])),
            uncertainty95,
            age,
            "READY" if len(self._window) == self.model.window_samples else "ESTIMATING",
            tuple(sorted(self._health)),
            self._last_gnss_decision,
            snapped_latitude_deg=snapped_lat,
            snapped_longitude_deg=snapped_lon,
            matched_segment_id=matched_id,
            cross_track_error_m=cross_err,
            estimated_gyro_bias_degps=gyro_bias,
            surface_condition=surface,
        )
