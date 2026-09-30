# Continuum IDR: Held-Out Evaluation Results

**Experiment ID:** `iovnbd-vtb-heldout-p0`  
**Model Bundle:** `motion-hgbr-p0-2026-01`  
**Dataset:** IO-VNBD Held-Out `Vtb*` family (Driver E)  
**Evaluation Protocol:** Strict causal GNSS masking with quality-gated outage windows  

---

## 1. Executive Summary

This report documents the rigorous evaluation of the **Continuum IDR** dead reckoning engine on the complete held-out `Vtb*` test split from the IO-VNBD dataset. In accordance with strict evaluation protocols:
1. **Zero Data Leakage:** The `Vtb*` test family was completely withheld during model training and hyperparameter selection.
2. **Strict GNSS Blackout:** During each simulated outage (tunnel/blackout), all GNSS fields (position, velocity, heading, satellite count, accuracy) were strictly withheld from the engine.
3. **Independent Time-Aligned Reference:** Scoring uses finite-accuracy phone GNSS positions recorded during the drive, strictly isolated to the evaluation layer.
4. **Benchmarking Against Standard Baselines:** Continuum IDR is benchmarked alongside **Baseline 0 (Frozen Position)** and **Baseline 1 (Last-Speed + Gyro Kinematic Dead Reckoning)**. The current system is better than the frozen-position median but worse than the last-speed-plus-gyro median overall.

---

## 2. Key Aggregate Metrics

| Metric | Continuum IDR | Baseline 1 (Last Speed + Gyro) | Baseline 0 (Frozen Position) |
| :--- | :---: | :---: | :---: |
| **Median Endpoint Error** | **354.3 m** | 334.4 m | 496.9 m |
| **95th Percentile Error** | **1072.3 m** | — | — |
| **Median Drift (% of Traveled Dist)** | **80.3%** | 86.0% | 101.1% |
| **95th Percentile Drift** | **271.4%** | — | — |
| **Pass Rate (< 10% Target)** | **0.0%** | — | — |
| **Relative error reduction vs Baseline 1** | **-5.9%** | Reference | — |
| **Relative error reduction vs Baseline 0** | **28.7%** | — | Reference |

---

## 3. Results by Outage Distance Bucket

| Distance Target | Valid Outages | IDR Med Error | IDR P95 Error | IDR Med Drift | IDR P95 Drift | <10% Pass Rate | B1 Med Error | B0 Med Error |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 50m | 11 | 73.6 m | 268.6 m | 148.6% | 537.2% | 0.0% | 59.8 m | 72.2 m |
| 500m | 12 | 431.9 m | 774.9 m | 86.4% | 154.4% | 0.0% | 414.9 m | 496.9 m |
| 1000m | 11 | 799.0 m | 1344.0 m | 80.0% | 134.2% | 0.0% | 800.7 m | 948.7 m |

---

## 4. Results by Independent Held-Out Run

| Run ID | Valid Outages | Median Error | Median Drift | <10% Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| `Vtb01` | 11 | 280.5 m | 61.4% | 0.0% |
| `Vtb02` | 8 | 620.7 m | 89.0% | 0.0% |
| `Vtb03` | 1 | 132.3 m | 261.6% | 0.0% |
| `Vtb04` | 1 | 143.7 m | 289.6% | 0.0% |
| `Vtb05` | 10 | 644.0 m | 108.4% | 0.0% |
| `Vtb08` | 1 | 86.1 m | 167.9% | 0.0% |
| `Vtb09` | 1 | 102.6 m | 204.3% | 0.0% |
| `Vtb12` | 1 | 24.8 m | 49.0% | 0.0% |

---

## 5. Representative Demonstration Outage (Continuum Studio)

The representative demonstration outage selected for Continuum Studio is chosen using a strict, documented rule: the **median-drift 500 m outage** across all held-out runs.

- **Run ID:** `Vtb02`
- **Outage ID:** `500m_40pct`
- **Reference Traveled Distance:** `499.5 m`
- **Duration:** `48.9 s`
- **Continuum IDR Endpoint Error:** `486.0 m`
- **Continuum IDR Drift:** `97.3%`
- **Baseline 1 (Last-Speed + Gyro) Error:** `444.3 m`
- **Baseline 0 (Frozen Position) Error:** `434.8 m`
- **10% SIH Target:** `NOT MET (Realistic Screening)`

---

## 6. Window Quality Gates and Exclusion Analysis

To prevent deceptive evaluations where vehicles are parked for minutes or GPS clocks reset, candidate windows were subjected to automated quality gates:
1. **Adequate Aided Warm-Up:** At least 30 seconds of aided navigation prior to blackout.
2. **Time Gap Gate:** Window excluded if sample time gap $\Delta t > 2.0$ s.
3. **Plausible Duration:** Duration bounded between 1–25 s (50 m), 10–120 s (500 m), and 20–240 s (1000 m).
4. **Dynamic Speed:** Vehicle must maintain an average moving speed $\ge 2.0$ m/s.
5. **Reference Fix Density:** Explicit minimum number of distinct reference fixes across the interval.

**Summary of Skipped Candidate Windows:**

| Exclusion Reason | Skipped Count |
| :--- | :---: |
| `insufficient_reference_fixes_0` | 11 |
| `run_too_short_for_endpoint` | 23 |
| `insufficient_warmup` | 63 |
| `duration_too_long_92.7s` | 1 |

---

## 7. Known Scope and Limitations

1. **Sensor Sampling Rate:** The IO-VNBD dataset records smartphone IMU at 10 Hz. Results do not claim to validate 50–200 Hz industrial IMU operation.
2. **Vehicle Mount Assumption:** The model assumes the smartphone is securely mounted in a forward-facing passenger vehicle. Handheld movement and phone re-orientations require separate online orientation tracking.
3. **Road Environment:** Data reflects UK road networks. Validation on Indian roads (unmarked roads, aggressive speed-breakers, mixed traffic) remains planned work.
4. **Honest Reporting:** The engine reduces the overall median error relative to holding the last position, but it does not beat the last-speed-plus-gyro baseline overall and no evaluated outage meets the supplied under-10% target. Long smartphone-IMU outages remain an unresolved accuracy problem.
