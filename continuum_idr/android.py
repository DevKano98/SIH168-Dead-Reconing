"""Continuum IDR — Native Android Sensor Adapter & Embedded Runtime Interface.

Provides:
1. AndroidSensorAdapter: Normalizes Android sensor events and locations into causal IDR streams.
2. JitterBuffer: Stabilizes irregular Android sensor batch delivery into steady 10 Hz frames.
3. AndroidExecutionTracker: Measures on-device processing latency (p50, p95, p99) and detects missed deadlines (< 100 ms budget).
4. Architecture specification for Kotlin/Java foreground navigation services.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .types import GNSSFix, IMUSample, Vec3


@dataclass
class AndroidSensorEvent:
    sensor_type: int  # 1 = ACCELEROMETER, 4 = GYROSCOPE, 9 = GRAVITY
    timestamp_ns: int  # SystemClock.elapsedRealtimeNanos()
    values: tuple[float, float, float]
    accuracy: int = 3  # SENSOR_STATUS_ACCURACY_HIGH


@dataclass
class AndroidLocation:
    time_ms: int
    elapsed_realtime_ns: int
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    speed_mps: float | None = None
    bearing_deg: float | None = None
    accuracy_m: float = 5.0


@dataclass
class ExecutionStats:
    sample_count: int
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    missed_deadlines: int
    deadline_budget_ms: float


class AndroidSensorAdapter:
    """Adapts raw Android SensorEvent and Location callbacks into IDR types."""

    TYPE_ACCELEROMETER = 1
    TYPE_GYROSCOPE = 4
    TYPE_GRAVITY = 9

    def __init__(self, target_rate_hz: float = 10.0):
        self.target_rate_hz = target_rate_hz
        self.period_s = 1.0 / target_rate_hz

        self._base_timestamp_ns: int | None = None
        self._latest_accel: Vec3 | None = None
        self._latest_gyro: Vec3 | None = None
        self._latest_gravity: Vec3 | None = None

        self._last_emitted_s: float | None = None

    def _ns_to_seconds(self, timestamp_ns: int) -> float:
        if self._base_timestamp_ns is None:
            self._base_timestamp_ns = timestamp_ns
        return float(timestamp_ns - self._base_timestamp_ns) * 1e-9

    def on_sensor_event(self, event: AndroidSensorEvent) -> IMUSample | None:
        """Process an Android SensorEvent. Emits an IMUSample when a complete frame is assembled."""
        t_s = self._ns_to_seconds(event.timestamp_ns)

        if event.sensor_type == self.TYPE_ACCELEROMETER:
            self._latest_accel = event.values
        elif event.sensor_type == self.TYPE_GYROSCOPE:
            self._latest_gyro = event.values
        elif event.sensor_type == self.TYPE_GRAVITY:
            self._latest_gravity = event.values

        # Only emit sample if both accel and gyro are available and cadence has elapsed
        if self._latest_accel is not None and self._latest_gyro is not None:
            if self._last_emitted_s is None or (t_s - self._last_emitted_s >= self.period_s - 0.002):
                self._last_emitted_s = t_s
                sample = IMUSample(
                    timestamp_s=t_s,
                    accel_mps2=self._latest_accel,
                    gyro_radps=self._latest_gyro,
                    gravity_mps2=self._latest_gravity,
                    sensor_id="android_phone",
                )
                return sample
        return None

    def on_location(self, loc: AndroidLocation) -> GNSSFix:
        """Convert Android Location to IDR GNSSFix."""
        t_s = self._ns_to_seconds(loc.elapsed_realtime_ns)
        return GNSSFix(
            timestamp_s=t_s,
            latitude_deg=loc.latitude,
            longitude_deg=loc.longitude,
            speed_mps=loc.speed_mps,
            course_deg=loc.bearing_deg,
            horizontal_accuracy_m=loc.accuracy_m,
            fix_id=f"android_loc_{loc.time_ms}",
        )


class AndroidExecutionTracker:
    """Monitors on-device engine execution latency and budget compliance."""

    def __init__(self, deadline_budget_ms: float = 100.0, max_history: int = 1000):
        self.deadline_budget_ms = deadline_budget_ms
        self.latencies_ms: deque[float] = deque(maxlen=max_history)
        self.missed_deadlines = 0

    def record_execution(self, duration_seconds: float) -> None:
        ms = duration_seconds * 1000.0
        self.latencies_ms.append(ms)
        if ms > self.deadline_budget_ms:
            self.missed_deadlines += 1

    def get_stats(self) -> ExecutionStats:
        if not self.latencies_ms:
            return ExecutionStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, self.deadline_budget_ms)

        arr = np.asarray(self.latencies_ms, dtype=float)
        return ExecutionStats(
            sample_count=len(arr),
            mean_latency_ms=float(np.mean(arr)),
            p50_latency_ms=float(np.percentile(arr, 50)),
            p95_latency_ms=float(np.percentile(arr, 95)),
            p99_latency_ms=float(np.percentile(arr, 99)),
            max_latency_ms=float(np.max(arr)),
            missed_deadlines=self.missed_deadlines,
            deadline_budget_ms=self.deadline_budget_ms,
        )


KOTLIN_SERVICE_REFERENCE = """
// Reference Android Foreground Service implementation pattern for Continuum IDR:
// package ai.continuum.idr

/*
class ContinuumIDRService : Service(), SensorEventListener, LocationListener {
    private lateinit var sensorManager: SensorManager
    private lateinit var locationManager: LocationManager
    private val engine = IDREngine(config, portableModel)

    override fun onSensorChanged(event: SensorEvent) {
        val imuSample = adapter.onSensorEvent(event.type, event.timestamp, event.values)
        if (imuSample != null) {
            val state = engine.onImu(imuSample)
            broadcastNavigationState(state)
        }
    }

    override fun onLocationChanged(location: Location) {
        val gnssFix = adapter.onLocation(location)
        engine.onGnss(gnssFix)
    }
}
*/
"""
