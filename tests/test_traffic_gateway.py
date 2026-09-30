from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from continuum_idr.cooperative import (
    HazardStore,
    TrafficHazardReport,
    TrafficReportStore,
    create_slowdown_report,
)
from continuum_idr.traffic_gateway import app


def test_traffic_slowdown_report_clustering():
    store = TrafficReportStore()
    t = 1000.0

    r1 = create_slowdown_report("veh_1", "seg_101", 90.0, t, speed_mps=2.0, position_uncertainty_m=4.0)
    r2 = create_slowdown_report("veh_2", "seg_101", 92.0, t + 5.0, speed_mps=1.5, position_uncertainty_m=3.5)

    assert store.ingest(r1, t) is True
    assert store.ingest(r2, t + 5.0) is True

    # At t + 5.0, check confirmation threshold
    assert store.confirmed_slowdown("seg_101", 90.0, t + 5.0, min_independent_origins=3) is False
    assert store.confirmed_slowdown("seg_101", 90.0, t + 5.0, min_independent_origins=2) is True


def test_hazard_store_spatial_clustering_and_confidence_boost():
    store = HazardStore(cluster_radius_m=35.0)
    t = 1000.0

    # Vehicle 1 reports speed breaker at (12.8450, 77.6600)
    h1 = TrafficHazardReport(
        hazard_id="h1",
        hazard_type="SPEED_BREAKER",
        severity=0.7,
        latitude=12.8450,
        longitude=77.6600,
        heading_deg=0.0,
        observed_at_s=t,
        expires_at_s=t + 3600.0,
        source_vehicle_id="veh_1",
        confidence=0.5,
    )
    m1 = store.ingest(h1, t)
    assert m1.confirmation_count == 1
    assert m1.confidence == 0.5

    # Vehicle 2 reports same speed breaker 10m away
    h2 = TrafficHazardReport(
        hazard_id="h2",
        hazard_type="SPEED_BREAKER",
        severity=0.8,
        latitude=12.84508,  # ~9 meters North
        longitude=77.6600,
        heading_deg=0.0,
        observed_at_s=t + 10.0,
        expires_at_s=t + 3600.0,
        source_vehicle_id="veh_2",
        confidence=0.6,
    )
    m2 = store.ingest(h2, t + 10.0)
    assert m2.confirmation_count == 2
    assert m2.confidence > 0.75  # Boosted confidence!
    assert m2.severity == 0.8    # Highest severity retained

    # Query active hazards within 200m
    active = store.get_active(12.8450, 77.6600, radius_m=200.0, now_s=t + 15.0)
    assert len(active) == 1
    assert active[0].hazard_type == "SPEED_BREAKER"

    # Query far away (5000m away)
    far = store.get_active(12.9000, 77.6600, radius_m=200.0, now_s=t + 15.0)
    assert len(far) == 0


def test_traffic_gateway_fastapi_endpoints():
    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/api/traffic/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Ingest report
    payload = {
        "hazard_type": "POTHOLE",
        "severity": 0.85,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "heading_deg": 180.0,
        "source_vehicle_id": "test_car_1",
        "ttl_s": 1800.0,
    }
    res_post = client.post("/api/traffic/report", json=payload)
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["status"] == "accepted"
    assert data["hazard"]["hazard_type"] == "POTHOLE"

    # 3. Query active hazards
    res_query = client.get("/api/traffic/active?lat=12.9716&lon=77.5946&radius_m=300")
    assert res_query.status_code == 200
    qdata = res_query.json()
    assert qdata["count"] >= 1
    assert any(h["hazard_type"] == "POTHOLE" for h in qdata["hazards"])

    # 4. Invalid hazard type rejected
    bad_payload = {**payload, "hazard_type": "INVALID_HAZARD"}
    res_bad = client.post("/api/traffic/report", json=bad_payload)
    assert res_bad.status_code == 400
