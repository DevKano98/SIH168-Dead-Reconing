# Continuum IDR — Field Trip Validation Report

**File:** `tunnel_demo.jsonl`  
**Status:** `VALID SCHEMA 1.0.0`  
**Device:** `ContinuumIDR ContinuumSyntheticRig`  
**Vehicle Profile:** `CAR`  
**Model SHA-256:** `synthetic_ground_truth_v1`  

## 1. Sensor Health & Data Quality Audit

| Metric | Value | Reference Standard | Assessment |
| :--- | :--- | :--- | :--- |
| Total Recorded Lines | 1,211 | > 500 lines | `PASS` |
| Trip Duration | 59.9 s | Continuous | `PASS` |
| Average IMU Sampling Rate | 10.0 Hz | >= 10.0 Hz | `PASS` |
| Maximum Sensor Latency Gap | 0.100 s | < 0.250 s | `PASS` |
| GNSS Fix Coverage | 16.9% | Variable | `INFO` |
| Surface Anomaly Events | 0 events | Indian Road | `DETECTED` |
| Mount Orientation Shifts | 0 events | Tilt Stability | `STABLE` |

## 2. GNSS Outage Drift Benchmark

*No GNSS outage episodes were detected during this recording.*
