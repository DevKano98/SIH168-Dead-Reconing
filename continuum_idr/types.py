from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional, Tuple


Vec3 = Tuple[float, float, float]


class TrackingMode(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    ALIGNING = "ALIGNING"
    GNSS_AIDED = "GNSS_AIDED"
    DEAD_RECKONING = "DEAD_RECKONING"
    RECOVERING = "RECOVERING"


@dataclass(frozen=True)
class IMUSample:
    timestamp_s: float
    accel_mps2: Vec3
    gyro_radps: Vec3
    gravity_mps2: Optional[Vec3] = None
    sensor_id: str = "phone"


@dataclass(frozen=True)
class GNSSFix:
    timestamp_s: float
    latitude_deg: float
    longitude_deg: float
    speed_mps: Optional[float] = None
    course_deg: Optional[float] = None
    horizontal_accuracy_m: Optional[float] = None
    fix_id: Optional[str] = None


@dataclass
class EngineConfig:
    imu_rate_hz: float = 10.0
    model_update_hz: float = 2.0
    output_rate_hz: float = 10.0
    gnss_timeout_s: float = 1.5
    gnss_gate_sigma: float = 5.0
    min_gnss_std_m: float = 3.0
    max_imu_gap_s: float = 0.5
    speed_process_std_mps: float = 0.7
    yaw_process_std_radps: float = 0.05
    accel_bias_std_mps2: float = 0.05
    gyro_z_sign: float = -1.0
    gyro_yaw_index: int = 1
    initial_position_std_m: float = 5.0
    initial_speed_std_mps: float = 2.0
    initial_heading_std_deg: float = 15.0
    recovery_fixes: int = 2
    max_speed_mps: float = 55.0
    outage_covariance_inflation: float = 0.20
    enable_map_matching: bool = False
    enable_gyro_bias_adaptation: bool = True
    enable_zupt_hysteresis: bool = True
    enable_mount_detector: bool = True
    vehicle_profile: str = "passenger_car"
    sensor_grade: str = "phone"
    enable_can_odometry: bool = False


@dataclass(frozen=True)
class NavigationState:
    timestamp_s: float
    sequence: int
    tracking_mode: TrackingMode
    east_m: Optional[float]
    north_m: Optional[float]
    latitude_deg: Optional[float]
    longitude_deg: Optional[float]
    speed_mps: Optional[float]
    heading_deg: Optional[float]
    horizontal_uncertainty_m: Optional[float]
    last_accepted_gnss_age_s: Optional[float]
    alignment_status: str
    health_flags: tuple[str, ...] = field(default_factory=tuple)
    last_gnss_decision: str = "NONE"
    snapped_latitude_deg: Optional[float] = None
    snapped_longitude_deg: Optional[float] = None
    matched_segment_id: Optional[str] = None
    cross_track_error_m: Optional[float] = None
    estimated_gyro_bias_degps: Optional[float] = None
    surface_condition: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tracking_mode"] = self.tracking_mode.value
        data["health_flags"] = list(self.health_flags)
        return data
