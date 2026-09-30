"""Continuum IDR — Cooperative Traffic Hazard Local Gateway.

FastAPI service for receiving, deduplicating, clustering, and querying
localized vehicle-to-everything (V2X) traffic hazards (GNSS outages, speed bumps,
potholes, and congestion).
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .cooperative import HazardStore, TrafficHazardReport, TrafficReportStore

app = FastAPI(
    title="Continuum IDR Traffic Gateway",
    description="Localized Cooperative V2X Traffic & Hazard Clearinghouse",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hazard_store = HazardStore(cluster_radius_m=35.0)
traffic_store = TrafficReportStore()
total_ingested_count = 0
gateway_start_time_s = time.time()


class IngestHazardRequest(BaseModel):
    hazard_type: str = Field(..., description="Hazard type: GNSS_OUTAGE, SPEED_BREAKER, POTHOLE, TRAFFIC_JAM")
    severity: float = Field(0.5, ge=0.0, le=1.0, description="Severity score between 0.0 and 1.0")
    latitude: float = Field(..., description="WGS-84 latitude in degrees")
    longitude: float = Field(..., description="WGS-84 longitude in degrees")
    heading_deg: float = Field(0.0, ge=0.0, le=360.0, description="Vehicle heading in degrees")
    source_vehicle_id: str = Field("anon_vehicle", description="Anonymous source vehicle identifier")
    ttl_s: float = Field(3600.0, gt=0.0, description="Time-to-live in seconds")


@app.post("/api/traffic/report")
async def report_hazard(req: IngestHazardRequest) -> dict[str, Any]:
    global total_ingested_count
    now_s = time.time()

    valid_types = {"GNSS_OUTAGE", "SPEED_BREAKER", "POTHOLE", "TRAFFIC_JAM"}
    if req.hazard_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid hazard type. Valid: {list(valid_types)}")

    ident = f"{req.hazard_type}|{round(req.latitude, 4)}|{round(req.longitude, 4)}|{round(now_s / 60)}"
    hid = hashlib.sha256(ident.encode()).hexdigest()[:16]

    report = TrafficHazardReport(
        hazard_id=hid,
        hazard_type=req.hazard_type,
        severity=req.severity,
        latitude=req.latitude,
        longitude=req.longitude,
        heading_deg=req.heading_deg,
        observed_at_s=now_s,
        expires_at_s=now_s + req.ttl_s,
        source_vehicle_id=req.source_vehicle_id,
        confidence=0.6,
    )

    merged = hazard_store.ingest(report, now_s)
    total_ingested_count += 1

    return {
        "status": "accepted",
        "hazard": merged.to_dict(),
    }


@app.get("/api/traffic/active")
async def get_active_hazards(
    lat: float = Query(..., description="Vehicle current latitude"),
    lon: float = Query(..., description="Vehicle current longitude"),
    radius_m: float = Query(500.0, ge=10.0, le=20000.0, description="Search radius in meters"),
) -> dict[str, Any]:
    now_s = time.time()
    active = hazard_store.get_active(lat, lon, radius_m=radius_m, now_s=now_s)
    return {
        "query": {
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
        },
        "count": len(active),
        "hazards": [h.to_dict() for h in active],
    }


@app.get("/api/traffic/health")
async def gateway_health() -> dict[str, Any]:
    now_s = time.time()
    hazard_store.prune(now_s)
    return {
        "status": "healthy",
        "service": "Continuum IDR Cooperative Traffic Gateway",
        "uptime_s": round(now_s - gateway_start_time_s, 1),
        "total_ingested_reports": total_ingested_count,
        "active_hazard_clusters": len(hazard_store._hazards),
    }


def run_gateway(host: str = "127.0.0.1", port: int = 8080) -> None:
    import uvicorn
    uvicorn.run("continuum_idr.traffic_gateway:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run_gateway()
