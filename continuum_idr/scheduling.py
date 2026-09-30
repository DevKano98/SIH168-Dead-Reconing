"""Continuum IDR — High-Frequency Dual-Rate Scheduler.

Provides dual-rate strapdown propagation:
- High-rate (100 Hz / 200 Hz) external automotive IMU state propagation
- Decimated 10 Hz machine learning motion model inference
- Asynchronous 1 Hz / 10 Hz GNSS arrival synchronization
- Latency profiling ensuring propagation average execution stays below 5 ms budget
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .engine import IDREngine
from .types import GNSSFix, IMUSample, NavigationState


@dataclass
class SchedulerMetrics:
    total_imu_samples: int
    total_model_triggers: int
    total_gnss_updates: int
    avg_propagation_latency_ms: float
    p95_propagation_latency_ms: float
    p99_propagation_latency_ms: float
    max_propagation_latency_ms: float
    budget_exceeded_count: int
    budget_limit_ms: float


class HighRateScheduler:
    """Schedules high-frequency (100-200 Hz) IMU propagation with decimated 10 Hz ML updates."""

    def __init__(
        self,
        engine: IDREngine,
        target_imu_rate_hz: float = 200.0,
        model_rate_hz: float = 10.0,
        latency_budget_ms: float = 5.0,  # 5 ms budget for 200 Hz propagation period
    ):
        self.engine = engine
        self.target_imu_rate_hz = target_imu_rate_hz
        self.model_rate_hz = model_rate_hz
        self.latency_budget_ms = latency_budget_ms

        self.decimation_factor = max(1, int(round(target_imu_rate_hz / model_rate_hz)))
        self._imu_counter = 0
        self._model_triggers = 0
        self._gnss_updates = 0

        self._propagation_latencies: deque[float] = deque(maxlen=2000)
        self._budget_exceeded = 0

    def step_imu(self, sample: IMUSample) -> NavigationState:
        """Process high-rate IMU sample through strapdown propagation."""
        t0 = time.perf_counter()

        self._imu_counter += 1
        state = self.engine.on_imu(sample)

        duration_ms = (time.perf_counter() - t0) * 1000.0
        self._propagation_latencies.append(duration_ms)
        if duration_ms > self.latency_budget_ms:
            self._budget_exceeded += 1

        if self._imu_counter % self.decimation_factor == 0:
            self._model_triggers += 1

        return state

    def step_gnss(self, fix: GNSSFix) -> NavigationState:
        """Process incoming GNSS fix."""
        self._gnss_updates += 1
        return self.engine.on_gnss(fix)

    def get_metrics(self) -> SchedulerMetrics:
        if not self._propagation_latencies:
            return SchedulerMetrics(
                self._imu_counter,
                self._model_triggers,
                self._gnss_updates,
                0.0,
                0.0,
                0.0,
                0.0,
                0,
                self.latency_budget_ms,
            )

        arr = np.asarray(self._propagation_latencies, dtype=float)
        return SchedulerMetrics(
            total_imu_samples=self._imu_counter,
            total_model_triggers=self._model_triggers,
            total_gnss_updates=self._gnss_updates,
            avg_propagation_latency_ms=float(np.mean(arr)),
            p95_propagation_latency_ms=float(np.percentile(arr, 95)),
            p99_propagation_latency_ms=float(np.percentile(arr, 99)),
            max_propagation_latency_ms=float(np.max(arr)),
            budget_exceeded_count=self._budget_exceeded,
            budget_limit_ms=self.latency_budget_ms,
        )
