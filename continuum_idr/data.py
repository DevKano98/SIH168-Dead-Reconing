from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RunPair:
    run_id: str
    driver_id: str
    phone_csv: Path
    vehicle_csv: Path
    rows_phone: int
    rows_vehicle: int

    @property
    def equal_length(self) -> bool:
        return self.rows_phone == self.rows_vehicle


@dataclass
class PairedRunData:
    pair: RunPair
    time_s: np.ndarray
    accel: np.ndarray
    gravity: np.ndarray
    gyro: np.ndarray
    phone_lat: np.ndarray
    phone_lon: np.ndarray
    phone_speed_raw: np.ndarray
    phone_course_deg: np.ndarray
    phone_accuracy_m: np.ndarray
    vehicle_lat: np.ndarray
    vehicle_lon: np.ndarray
    vehicle_speed_mps: np.ndarray
    vehicle_heading_deg: np.ndarray


def _count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
        return max(0, sum(1 for _ in stream) - 1)


def _driver_from_path(path: Path) -> str:
    text = path.as_posix()
    match = re.search(r"\(Driver ([A-Z])\)", text)
    if match:
        return match.group(1)
    return "UNKNOWN"


def discover_synchronized_pairs(dataset_root: str | Path) -> list[RunPair]:
    root = Path(dataset_root)
    categorized = root / "Synchronised V abd S datasets" / "Synchronised V abd S datasets" / "Categorised IOVNB Dataset"
    if not categorized.exists():
        raise FileNotFoundError(f"synchronized categorized dataset not found: {categorized}")
    pairs: list[RunPair] = []
    for directory in sorted({p.parent for p in categorized.rglob("*.csv")}):
        csvs = sorted(directory.glob("*.csv"))
        phone = [p for p in csvs if p.name.lower().startswith("s-")]
        vehicle = [p for p in csvs if p.name.lower().startswith("v-")]
        if len(phone) != 1 or len(vehicle) != 1:
            continue
        run_id = directory.name
        pairs.append(
            RunPair(
                run_id=run_id,
                driver_id=_driver_from_path(directory),
                phone_csv=phone[0],
                vehicle_csv=vehicle[0],
                rows_phone=_count_rows(phone[0]),
                rows_vehicle=_count_rows(vehicle[0]),
            )
        )
    return pairs


def _numeric_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8", encoding_errors="replace", low_memory=False)
    # Categorized paired files use the regular layouts. Keep field order because
    # the dataset has inconsistent gyro labels across duplicate copies.
    return frame.apply(pd.to_numeric, errors="coerce")


def load_paired_run(pair: RunPair, require_equal_length: bool = True) -> PairedRunData:
    if require_equal_length and not pair.equal_length:
        raise ValueError(f"{pair.run_id}: unequal S/V rows ({pair.rows_phone}/{pair.rows_vehicle})")
    phone = _numeric_frame(pair.phone_csv)
    vehicle = _numeric_frame(pair.vehicle_csv)
    count = min(len(phone), len(vehicle))
    phone_values = phone.iloc[:count].to_numpy(dtype=np.float64)
    vehicle_values = vehicle.iloc[:count].to_numpy(dtype=np.float64)
    if phone_values.shape[1] < 24 or vehicle_values.shape[1] != 29:
        raise ValueError(f"{pair.run_id}: unsupported paired schema {phone_values.shape[1]}/{vehicle_values.shape[1]}")
    # IMU features and the evaluation reference are mandatory. Phone GNSS is
    # an optional runtime measurement and may contain short gaps.
    required = np.concatenate(
        [phone_values[:, [7, 9, 10, 11, 12, 13, 14, 15, 16, 17]], vehicle_values[:, [2, 3, 4, 5, 15]]],
        axis=1,
    )
    valid = np.isfinite(required).all(axis=1)
    if not valid.all():
        # Paired model runs are kept contiguous. Rejecting internal rows would
        # silently disturb timing, so fail and make the caller exclude the run.
        bad = int((~valid).sum())
        raise ValueError(f"{pair.run_id}: {bad} rows contain missing required values")
    time_s = phone_values[:, 7] / 1000.0
    # IO-VNBD is nominally 10 Hz. Unwrap session clock resets to keep time strictly monotonic.
    unwrapped = time_s.copy()
    for i in range(1, len(unwrapped)):
        if unwrapped[i] <= unwrapped[i - 1]:
            unwrapped[i:] += (unwrapped[i - 1] + 0.1 - unwrapped[i])
    time_s = unwrapped - unwrapped[0]
    return PairedRunData(
        pair=pair,
        time_s=time_s,
        accel=phone_values[:, 9:12],
        gravity=phone_values[:, 12:15],
        gyro=phone_values[:, 15:18],
        phone_lat=phone_values[:, 0],
        phone_lon=phone_values[:, 1],
        phone_speed_raw=phone_values[:, 3],
        phone_course_deg=phone_values[:, 5],
        phone_accuracy_m=phone_values[:, 4],
        vehicle_lat=vehicle_values[:, 2],
        vehicle_lon=vehicle_values[:, 3],
        vehicle_speed_mps=vehicle_values[:, 15] / 3.6,
        vehicle_heading_deg=vehicle_values[:, 5],
    )


def audit_pairs(dataset_root: str | Path) -> dict:
    pairs = discover_synchronized_pairs(dataset_root)
    return {
        "pair_count": len(pairs),
        "equal_length_count": sum(p.equal_length for p in pairs),
        "unequal_length_count": sum(not p.equal_length for p in pairs),
        "drivers": {driver: sum(p.driver_id == driver for p in pairs) for driver in sorted({p.driver_id for p in pairs})},
        "runs": [
            {
                "run_id": p.run_id,
                "driver_id": p.driver_id,
                "phone_csv": p.phone_csv.as_posix(),
                "vehicle_csv": p.vehicle_csv.as_posix(),
                "rows_phone": p.rows_phone,
                "rows_vehicle": p.rows_vehicle,
                "eligible_p0": p.equal_length,
            }
            for p in pairs
        ],
    }
