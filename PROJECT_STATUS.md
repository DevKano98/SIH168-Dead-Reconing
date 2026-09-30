# Continuum IDR — Project Status Report

The canonical status is maintained in [CURRENT_STATUS.md](CURRENT_STATUS.md). This file remains as a stable link for older documentation.

## Current delivery

- Verified, buildable Android project producing `android/app/build/outputs/apk/debug/app-debug.apk` (1.10 MB, SHA-256: `6d894a74...`) with embedded trained model (`motion_portable.json`) and regional road pack (`sample_road_pack.json`).
- On-device Kotlin dead reckoning (`ContinuumLocationEngine`) with microsecond latency instrumentation, offline vector road map (`MapView`), foreground trip recorder (`TrackingService`), route category selection, and cooperative BLE hazard sharing (`TrafficBleManager`) with relay statistics HUD (direct ~10-30m range).
- Working Python research SDK, trained motion model, and 122 passed unit and integration tests.
- 17-category synthetic Indian-road expansion generator (`continuum_idr/synthetic_dataset.py`, `idr generate-synthetic-dataset`).
- Leakage-safe trip folder validation and train/val/test splitting (`continuum_idr/phone_data.py`, `idr validate-field-folder`).
- Ground-truth reference trajectory evaluation engine (`continuum_idr/reference_eval.py`, `idr evaluate-reference`).
- Comparative candidate architecture experimentation framework (`continuum_idr/experiments.py`, `idr run-experiments`).
- Windows ADB device validation automation (`tools/adb/device_validate.ps1`, `tools/adb/device_validate.bat`).
- Standardized protocols in `docs/FIELD_TEST_PLANS.md` and verification gates in `docs/DEVICE_VALIDATION_CHECKLIST.md`.
- Multi-stage deterministic Python/Kotlin parity test suite (`ParityTest.kt` and `test_parity.py`).
- Deterministic 20-scenario synthetic generator (`continuum_idr/synthetic.py`) and CLI `idr synthetic`.
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
