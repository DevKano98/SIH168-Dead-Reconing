# Continuum IDR — Project Status Report

The canonical status is maintained in [CURRENT_STATUS.md](CURRENT_STATUS.md). This file remains as a stable link for older documentation.

## Current delivery

- Verified, buildable Android project producing `android/app/build/outputs/apk/debug/app-debug.apk` (1.09 MB) with embedded trained model (`motion_portable.json`) and regional road pack (`sample_road_pack.json`).
- On-device Kotlin dead reckoning (`ContinuumLocationEngine`), offline vector road map (`MapView`), foreground trip recorder (`TrackingService`), and cooperative BLE hazard sharing (`TrafficBleManager`).
- Working Python research SDK, trained motion model, and 110 passed unit and integration tests.
- Multi-stage deterministic Python/Kotlin parity test suite (`ParityTest.kt` and `test_parity.py`).
- Deterministic 20-scenario synthetic generator (`continuum_idr/synthetic.py`) and CLI `idr synthetic`.
- Indian-road collection and validation pipeline (`continuum_idr/phone_data.py`, `docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md`).
- Local cooperative V2X traffic gateway (`continuum_idr/traffic_gateway.py`).
- Reproducible IO-VNBD outage evaluator and checked-in evidence.
- Continuum Studio replay at `/`, driver-facing view at `/mobile`, and developer portal at `/docs`.

## Current result

The authoritative `artifacts/evaluation/summary.json` reports 34 evaluated held-out outages, 354.3 m median endpoint error, 80.3% median drift, and a 0.0% pass rate below the supplied 10% drift target. The current result is preliminary and does not support lane-level or production-readiness claims.

## Run the prototype

```powershell
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --port 8000
```

See [README.md](README.md) for setup and integration, [artifacts/evaluation/RESULTS.md](artifacts/evaluation/RESULTS.md) for the generated benchmark report, and [CURRENT_STATUS.md](CURRENT_STATUS.md) for component status, limitations, and the next milestone.
