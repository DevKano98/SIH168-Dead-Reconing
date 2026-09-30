import math

from continuum_idr.geo import LocalFrame, heading_deg_to_rad, heading_rad_to_deg


def test_local_frame_round_trip():
    frame = LocalFrame(52.4, -1.5)
    point = (52.4012, -1.4975)
    east, north = frame.to_enu(*point)
    latitude, longitude = frame.to_wgs84(east, north)
    assert abs(latitude - point[0]) < 1e-9
    assert abs(longitude - point[1]) < 1e-9


def test_heading_round_trip():
    for heading in (0, 45, 180, 359.9):
        assert math.isclose(heading_rad_to_deg(heading_deg_to_rad(heading)), heading)
