from __future__ import annotations

import math
from dataclasses import dataclass


EARTH_RADIUS_M = 6_378_137.0


@dataclass(frozen=True)
class LocalFrame:
    latitude0_deg: float
    longitude0_deg: float

    def to_enu(self, latitude_deg: float, longitude_deg: float) -> tuple[float, float]:
        lat0 = math.radians(self.latitude0_deg)
        east = math.radians(longitude_deg - self.longitude0_deg) * EARTH_RADIUS_M * math.cos(lat0)
        north = math.radians(latitude_deg - self.latitude0_deg) * EARTH_RADIUS_M
        return east, north

    def to_wgs84(self, east_m: float, north_m: float) -> tuple[float, float]:
        lat0 = math.radians(self.latitude0_deg)
        latitude = self.latitude0_deg + math.degrees(north_m / EARTH_RADIUS_M)
        longitude = self.longitude0_deg + math.degrees(east_m / (EARTH_RADIUS_M * math.cos(lat0)))
        return latitude, longitude


def wrap_heading_rad(value: float) -> float:
    return value % (2.0 * math.pi)


def heading_deg_to_rad(value: float) -> float:
    """Convert degrees clockwise from north to radians clockwise from north."""
    return wrap_heading_rad(math.radians(value))


def heading_rad_to_deg(value: float) -> float:
    return math.degrees(wrap_heading_rad(value))
