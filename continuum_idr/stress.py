"""Continuum IDR — GNSS Stress Testing & Fault-Injection Framework.

Simulates harsh real-world conditions:
- Multipath position jumps (urban canyons, tunnels, overpasses)
- Stale repeating fixes (GNSS receiver firmware freeze)
- Non-monotonic timestamps (packet re-ordering / jitter)
- Accuracy degradation (poor satellite geometry / high DOP)
- Complete signal blackout followed by re-acquisition
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .engine import IDREngine
from .geo import LocalFrame
from .model import MotionModelBundle
from .types import EngineConfig, GNSSFix, IMUSample, TrackingMode


@dataclass
class CorruptionScenario:
    scenario_id: str
    description: str
    multipath_jump_m: tuple[float, float] | None = None
    stale_duration_s: float = 0.0
    out_of_order_offset_s: float = 0.0
    degraded_accuracy_m: float | None = None
    drop_rate: float = 0.0


@dataclass
class RobustnessResult:
    scenario_id: str
    fixes_injected: int
    fixes_rejected: int
    rejection_rate_pct: float
    max_position_error_vs_clean_m: float
    cleanly_recovered: bool
    recovery_time_s: float | None
    health_flags_raised: list[str]


class CorruptedFixInjector:
    """Injects controlled sensor faults into GNSS streams for stress testing."""

    def __init__(self, frame: LocalFrame):
        self.frame = frame

    def apply_multipath_jump(self, fix: GNSSFix, delta_east_m: float, delta_north_m: float) -> GNSSFix:
        """Offset fix coordinates by east/north delta in meters."""
        e, n = self.frame.to_enu(fix.latitude_deg, fix.longitude_deg)
        new_lat, new_lon = self.frame.to_wgs84(e + delta_east_m, n + delta_north_m)
        return GNSSFix(
            timestamp_s=fix.timestamp_s,
            latitude_deg=new_lat,
            longitude_deg=new_lon,
            speed_mps=fix.speed_mps,
            course_deg=fix.course_deg,
            horizontal_accuracy_m=fix.horizontal_accuracy_m,
            fix_id=f"{fix.fix_id}:corrupt_multipath",
        )

    def apply_stale_fix(self, last_fix: GNSSFix, current_timestamp_s: float) -> GNSSFix:
        """Repeat last fix coordinates with current timestamp."""
        return GNSSFix(
            timestamp_s=current_timestamp_s,
            latitude_deg=last_fix.latitude_deg,
            longitude_deg=last_fix.longitude_deg,
            speed_mps=last_fix.speed_mps,
            course_deg=last_fix.course_deg,
            horizontal_accuracy_m=last_fix.horizontal_accuracy_m,
            fix_id=f"{last_fix.fix_id}:stale",
        )

    def apply_timestamp_reversal(self, fix: GNSSFix, backward_offset_s: float = 2.0) -> GNSSFix:
        """Set timestamp earlier than preceding fixes."""
        return GNSSFix(
            timestamp_s=fix.timestamp_s - backward_offset_s,
            latitude_deg=fix.latitude_deg,
            longitude_deg=fix.longitude_deg,
            speed_mps=fix.speed_mps,
            course_deg=fix.course_deg,
            horizontal_accuracy_m=fix.horizontal_accuracy_m,
            fix_id=f"{fix.fix_id}:out_of_order",
        )

    def apply_degradation(self, fix: GNSSFix, degraded_accuracy_m: float = 75.0) -> GNSSFix:
        """Simulate high dilution of precision."""
        return GNSSFix(
            timestamp_s=fix.timestamp_s,
            latitude_deg=fix.latitude_deg,
            longitude_deg=fix.longitude_deg,
            speed_mps=fix.speed_mps,
            course_deg=fix.course_deg,
            horizontal_accuracy_m=degraded_accuracy_m,
            fix_id=f"{fix.fix_id}:degraded",
        )


def evaluate_stress_scenario(
    model: MotionModelBundle,
    scenario: CorruptionScenario,
    duration_s: float = 60.0,
    speed_mps: float = 12.0,
) -> RobustnessResult:
    """Run an automated stress test against the IDR engine."""
    frame = LocalFrame(52.4, -1.5)
    injector = CorruptedFixInjector(frame)
    config = EngineConfig(gnss_timeout_s=2.0)

    # 1. Clean engine run
    clean_engine = IDREngine(model, config)
    # 2. Corrupted engine run
    test_engine = IDREngine(model, config)

    clean_positions = []
    test_positions = []
    all_flags = set()

    fixes_injected = 0
    fixes_rejected = 0

    corruption_start_s = max(duration_s * 0.3, 1.0)
    corruption_end_s = max(duration_s * 0.6, corruption_start_s + 2.0)

    samples = int(duration_s * 10)
    last_clean_fix = None

    for i in range(samples):
        t = i * 0.1
        # Trajectory moving Eastward
        east = t * speed_mps
        north = 0.0
        lat, lon = frame.to_wgs84(east, north)

        imu_sample = IMUSample(
            timestamp_s=t,
            accel_mps2=(0.0, 0.0, 9.80665),
            gyro_radps=(0.0, 0.0, 0.0),
            gravity_mps2=(0.0, 0.0, 9.80665),
        )

        clean_state = clean_engine.on_imu(imu_sample)
        test_state = test_engine.on_imu(imu_sample)

        # 1 Hz GNSS fixes
        if i % 10 == 0:
            clean_fix = GNSSFix(
                timestamp_s=t,
                latitude_deg=lat,
                longitude_deg=lon,
                speed_mps=speed_mps,
                course_deg=90.0,
                horizontal_accuracy_m=3.0,
                fix_id=f"fix_{i}",
            )
            clean_state = clean_engine.on_gnss(clean_fix)
            last_clean_fix = clean_fix

            test_fix = clean_fix
            in_corruption_window = corruption_start_s <= t <= corruption_end_s

            if in_corruption_window:
                fixes_injected += 1
                if scenario.multipath_jump_m is not None:
                    test_fix = injector.apply_multipath_jump(
                        clean_fix, scenario.multipath_jump_m[0], scenario.multipath_jump_m[1]
                    )
                elif scenario.out_of_order_offset_s > 0:
                    test_fix = injector.apply_timestamp_reversal(clean_fix, scenario.out_of_order_offset_s)
                elif scenario.degraded_accuracy_m is not None:
                    test_fix = injector.apply_degradation(clean_fix, scenario.degraded_accuracy_m)

            test_state = test_engine.on_gnss(test_fix)

            if in_corruption_window and test_state.last_gnss_decision.startswith("REJECT"):
                fixes_rejected += 1

            for flag in test_state.health_flags:
                all_flags.add(flag)

        if clean_state.east_m is not None and test_state.east_m is not None:
            clean_positions.append((clean_state.east_m, clean_state.north_m))
            test_positions.append((test_state.east_m, test_state.north_m))

    # Calculate max deviation
    max_error = 0.0
    for (ce, cn), (te, tn) in zip(clean_positions, test_positions):
        err = math.hypot(te - ce, tn - cn)
        if err > max_error:
            max_error = err

    rejection_rate = 100.0 * (fixes_rejected / max(fixes_injected, 1))
    recovered = test_engine.get_state().tracking_mode == TrackingMode.GNSS_AIDED

    return RobustnessResult(
        scenario_id=scenario.scenario_id,
        fixes_injected=fixes_injected,
        fixes_rejected=fixes_rejected,
        rejection_rate_pct=rejection_rate,
        max_position_error_vs_clean_m=max_error,
        cleanly_recovered=recovered,
        recovery_time_s=None,
        health_flags_raised=sorted(list(all_flags)),
    )
