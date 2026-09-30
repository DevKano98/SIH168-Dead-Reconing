"""Interactive raw-recording sessions. Saved prediction traces are never inputs."""
from __future__ import annotations

import math
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable
from uuid import uuid4

import numpy as np

from .data import PairedRunData, discover_synchronized_pairs, load_paired_run
from .engine import IDREngine
from .geo import LocalFrame
from .model import MotionModelBundle
from .types import EngineConfig, GNSSFix, IMUSample


class RuntimeSession:
    """One local, shared experiment, advanced by polling using recorded timestamps.

    Controls take effect after the last processed sample. Polling catches up with
    elapsed wall time in bounded batches; it never drops IMU samples. Reference
    interpolation is exclusively for scoring and is not supplied to IDREngine.
    """

    def __init__(self, run: PairedRunData, model: MotionModelBundle,
                 start_index: int, end_index: int, *, clock: Callable = time.monotonic):
        if not 0 <= start_index <= end_index < len(run.time_s):
            raise ValueError("Invalid recording interval")
        self.run, self.model = run, model
        self.start, self.end = start_index, end_index
        self.clock = clock
        self.lock = threading.Lock()
        self.config = EngineConfig(imu_rate_hz=model.sample_rate_hz, gnss_timeout_s=12.0)
        valid = np.isfinite(run.phone_lat) & np.isfinite(run.phone_lon)
        self.fixes = valid & np.r_[True, (np.diff(run.phone_lat) != 0) | (np.diff(run.phone_lon) != 0)]
        fix_indices = np.flatnonzero(self.fixes)
        before = fix_indices[fix_indices <= start_index]
        if not len(before):
            raise ValueError("No GNSS fix available to initialize this recording")
        warm = before[before <= max(0, start_index - 100)]
        self.warm_start = int(warm[-1] if len(warm) else before[0])
        self.frame = LocalFrame(float(run.phone_lat[before[0]]), float(run.phone_lon[before[0]]))
        # Future reference fixes are allowed in offline scoring, never inference.
        lat = np.interp(run.time_s, run.time_s[fix_indices], run.phone_lat[fix_indices])
        lon = np.interp(run.time_s, run.time_s[fix_indices], run.phone_lon[fix_indices])
        self.reference = np.asarray([self.frame.to_enu(a, b) for a, b in zip(lat, lon)])
        self._reset()

    def _reset(self):
        self.engine = IDREngine(self.model, self.config)
        self.session_id = str(uuid4())
        self.revision = 0
        self.playing, self.rate, self.gnss_enabled = False, 1.0, True
        self.history, self.events = [], []
        self.imu_processed = self.gnss_delivered = self.gnss_withheld = 0
        self.cursor = self.warm_start - 1
        for index in range(self.warm_start, self.start + 1):
            self._process(index, capture=index >= self.start)
        self.anchor_time = float(self.run.time_s[self.cursor])
        self.anchor_wall = self.clock()
        self._event("restart")

    def _event(self, action):
        self.revision += 1
        self.events.append({"action": action, "after_source_index": self.cursor,
                            "time_s": float(self.run.time_s[self.cursor]),
                            "gnss_enabled": self.gnss_enabled, "rate": self.rate})

    def _process(self, index, *, capture=True):
        run = self.run
        timestamp = float(run.time_s[index])
        new_fix = bool(self.fixes[index])
        delivered = new_fix and self.gnss_enabled
        if delivered:
            speed, course, accuracy = (run.phone_speed_raw[index], run.phone_course_deg[index],
                                       run.phone_accuracy_m[index])
            self.engine.on_gnss(GNSSFix(
                timestamp_s=timestamp, latitude_deg=float(run.phone_lat[index]),
                longitude_deg=float(run.phone_lon[index]),
                speed_mps=max(0.0, float(speed)) if np.isfinite(speed) else None,
                course_deg=float(course) if np.isfinite(course) else None,
                horizontal_accuracy_m=float(np.clip(accuracy, 3, 50)) if np.isfinite(accuracy) else 15.0,
                fix_id=f"{run.pair.run_id}:{index}"))
            self.gnss_delivered += 1
        elif new_fix:
            self.gnss_withheld += 1
        state = self.engine.on_imu(IMUSample(
            timestamp_s=timestamp, accel_mps2=tuple(map(float, run.accel[index])),
            gyro_radps=tuple(map(float, run.gyro[index])),
            gravity_mps2=tuple(map(float, run.gravity[index])), sensor_id="iovnbd-phone"))
        self.imu_processed += 1
        self.cursor = index
        self.revision += 1
        if capture:
            east, north = (None, None) if state.latitude_deg is None else self.frame.to_enu(
                state.latitude_deg, state.longitude_deg)
            ref_e, ref_n = map(float, self.reference[index])
            error = None if east is None else math.hypot(east - ref_e, north - ref_n)
            self.history.append({
                "index": len(self.history), "source_index": index, "time_s": timestamp,
                "elapsed_s": timestamp - float(run.time_s[self.start]),
                "gnss_enabled": self.gnss_enabled, "gnss_available": new_fix,
                "gnss_delivered": delivered, "gnss_withheld": new_fix and not delivered,
                "state": state.to_dict(), "east_m": east, "north_m": north,
                "reference_east_m": ref_e, "reference_north_m": ref_n, "error_m": error})

    def _advance(self):
        if not self.playing:
            return
        target = self.anchor_time + (self.clock() - self.anchor_wall) * self.rate
        limit = min(self.end, self.cursor + 100)
        while self.cursor < limit and self.run.time_s[self.cursor + 1] <= target:
            self._process(self.cursor + 1)
        if self.cursor == self.end:
            self.playing = False

    def _snapshot(self):
        errors = [row["error_m"] for row in self.history if row["error_m"] is not None]
        return {
            "session_id": self.session_id, "revision": self.revision,
            "execution": "interactive_sdk", "input_source": "recorded_iovnbd_sensors",
            "run_id": self.run.pair.run_id, "model_id": self.model.model_id,
            "playing": self.playing, "rate": self.rate, "gnss_enabled": self.gnss_enabled,
            "completed": self.cursor == self.end, "index": len(self.history) - 1,
            "sample_count": self.end - self.start + 1,
            "duration_s": float(self.run.time_s[self.end] - self.run.time_s[self.start]),
            "warmup_samples": self.start - self.warm_start,
            "counters": {"imu_processed": self.imu_processed, "gnss_delivered": self.gnss_delivered,
                         "gnss_withheld": self.gnss_withheld},
            "config": asdict(self.config), "current": self.history[-1],
            "metrics": {"current_error_m": self.history[-1]["error_m"],
                        "max_error_m": max(errors) if errors else None},
            "samples": list(self.history), "events": list(self.events),
            "reference_note": "Interpolated phone GNSS for offline scoring only; not survey ground truth.",
        }

    def snapshot(self):
        with self.lock:
            self._advance()
            return self._snapshot()

    def control(self, action, value=None):
        # Validate before advancing or mutating anything.
        if action not in {"play", "pause", "restart", "rate", "gnss", "step"}:
            raise ValueError("Supported actions: play, pause, restart, rate, gnss, step; seeking is not supported")
        if action == "rate" and (type(value) not in (int, float) or value not in (0.5, 1, 2, 4)):
            raise ValueError("rate must be 0.5, 1, 2, or 4")
        if action == "gnss" and type(value) is not bool:
            raise ValueError("gnss value must be a boolean")
        if action == "step" and (type(value) is not int or not 1 <= value <= 100):
            raise ValueError("step must be an integer from 1 to 100")
        with self.lock:
            if action == "step" and self.playing:
                raise ValueError("Pause before stepping")
            self._advance()
            if action == "restart":
                self._reset()
            else:
                if action == "play":
                    if self.cursor == self.end:
                        raise ValueError("Session completed; restart to run again")
                    self.playing = True
                elif action == "pause":
                    self.playing = False
                elif action == "rate":
                    self.rate = float(value)
                elif action == "gnss":
                    self.gnss_enabled = value
                elif action == "step":
                    for index in range(self.cursor + 1, min(self.end, self.cursor + value) + 1):
                        self._process(index)
                self._event(action)
                self.anchor_time = float(self.run.time_s[self.cursor])
                self.anchor_wall = self.clock()
            return self._snapshot()


def load_runtime(dataset: Path, model_path: Path, demo: dict) -> RuntimeSession:
    model = MotionModelBundle.load(model_path)
    run_id = demo["run_id"]
    if run_id not in model.manifest.get("test_runs", []):
        raise ValueError("The selected run must belong to the model's held-out split")
    pairs = [p for p in discover_synchronized_pairs(dataset) if p.run_id == run_id and p.equal_length]
    if len(pairs) != 1:
        raise ValueError(f"Expected one synchronized raw recording for {run_id}")
    run = load_paired_run(pairs[0])
    # Only scenario identity and boundaries come from the artifact, never predictions.
    start = max(0, int(demo["outage"]["start_index"]) - 200)
    end = min(len(run.time_s) - 1, int(demo["outage"]["end_index"]) + 100)
    return RuntimeSession(run, model, start, end)
