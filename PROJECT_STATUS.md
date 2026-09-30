# Continuum IDR — Project Status Report

The canonical status is maintained in [CURRENT_STATUS.md](CURRENT_STATUS.md). This file remains as a stable link for older documentation.

## Current delivery

- Working Python research SDK and trained motion model.
- Reproducible IO-VNBD outage evaluator and checked-in evidence.
- Continuum Studio replay at `/`.
- Synchronized driver-facing replay at `/mobile`.
- SDK developer documentation portal at `/docs`.
- Portable model runner and Kotlin Android integration source.
- Unit-tested experimental map, vehicle-profile, scheduling, calibration, and odometry modules.

## Current result

The authoritative `artifacts/evaluation/summary.json` reports 34 evaluated held-out outages, 354.3 m median endpoint error, 80.3% median drift, and a 0.0% pass rate below the supplied 10% drift target. The current result is preliminary and does not support lane-level or production-readiness claims.

## Run the prototype

```powershell
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --port 8000
```

See [README.md](README.md) for setup and integration, [artifacts/evaluation/RESULTS.md](artifacts/evaluation/RESULTS.md) for the generated benchmark report, and [CURRENT_STATUS.md](CURRENT_STATUS.md) for component status, limitations, and the next milestone.
