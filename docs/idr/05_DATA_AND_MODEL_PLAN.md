# 5. Data preparation and model plan

## What is available

The [dataset catalog](../../DATASET_CATALOG.md) records 564 CSVs: 323 vehicle files with 29 columns, and 241 smartphone files with five header variants. There are 9,189,756 rows across copies, but only 329 distinct CSV byte streams after exact-file hashing. Byte-distinct files can still contain the same journey with different headers or trimming, so 329 is not a count of independent drives.

Use the actual extracted directory:

```text
Synchronised V abd S datasets/
  Synchronised V abd S datasets/
    Categorised IOVNB Dataset/
```

It contains 72 S/V run pairs in the catalog. Choose one canonical copy per parent recording. Other copies are useful for audit and provenance; they are not additional training examples.

## Preparation gates that must precede training

### Pairing and time

The prior full scan's row counts show nine unequal pairs even in the synchronized categorized branch:

| Smartphone file | S rows | Corresponding V rows |
| --- | ---: | ---: |
| S-Vfa01.csv | 11,486 | 11,535 |
| S-Vfa02.csv | 67,523 | 67,755 |
| S-Vta1b.csv | 954 | 953 |
| S-Vtb10.csv | 196 | 195 |
| S-Vw1.csv | 20,476 | 20,475 |
| S-Vw2.csv | 52,713 | 52,712 |
| S-Vw4.csv | 126,526 | 126,527 |
| S-Vw9.csv | 552 | 553 |
| S-Vw15.csv | 1,380 | 1,391 |

Equal row counts would still not prove correct synchronization. Use smartphone elapsed time/date and vehicle time-of-day to establish a documented mapping, accounting for clock offsets, time zones and rollover where relevant. Validate offsets with motion signatures such as turns or braking, and use only overlapping coverage. Record offset, estimated drift, overlap, and residual alignment quality in the manifest.

Resampling a training reference label inside a known overlap is permitted and must be documented. Runtime feature construction must remain causal. Do not align or retune a held-out run using future reference data that would be unavailable to the estimator. If a benchmark requires an offline label-time correction, keep that correction in the evaluator and disclose it separately from runtime alignment.

### Semantic and unit checks

- `S-A4.csv` appears to have a blank inserted at field 7 that shifts later data beneath the wrong headings: satellites under elapsed time, milliseconds under Date, and a date string under acceleration X. Quarantine it. A possible repair removes that blank data field and the trailing empty header, but it must pass full-file type and physical checks before becoming a versioned transformation.
- Phone `GPS SPEED (Kmh)` cannot be converted blindly from its label. Audited schema ranges and samples raise a unit question. Compare displacement/time, credible vehicle speed, and the source export conventions on moving segments; resolve per source family and record the conversion. Do not choose whichever conversion makes test error look best.
- Gyro Yaw/Pitch/Roll and X/Y/Z headers can label the same column positions in different copies. Raw S-M samples show identical numerical triplets under different labels. Validate the physical axis/sign mapping against turns; do not select the column named Yaw without checking.
- Normalize header whitespace/encoding through explicit alias maps while retaining original names. Reject unexpected schemas.
- Vehicle `Height (km)`, requested gear, and accelerator-pedal headings have conflicts with observed values. These fields are not required by the initial model and should not silently enter features. A direct inspection of Driver D also shows that equal S/V row counts do not preserve time alignment through the whole run; same-index coordinates diverge substantially. P0 therefore uses the phone GNSS stream as a withheld, time-aligned training/evaluation reference. Vehicle references remain excluded from P0 metrics until a verified cross-clock mapping is implemented.
- Phone GPS coordinates often repeat between fresh fixes. Repeated values in a 10 Hz file do not create independent 10 Hz GNSS observations.

## Canonical record and provenance

Each prepared run contains:

```text
run_id, parent_session_id, source_paths, source_hashes
driver_id, phone_id_if_known, vehicle_id_if_known, recording_date
schema_id, unit_profile_id, axis_profile_id, pairing_quality
time_s, accel_sensor_mps2[3], gyro_sensor_radps[3]
optional gravity[3], magnetometer[3], availability_masks
separate GNSS event stream with freshness/provenance
separate training/evaluation reference stream
split, exclusion_flags, transformation_version
```

Raw files remain preserved. Processed records, training features, and reference labels occupy separate artifacts. The runtime loader never exposes V-file columns or future GNSS through a convenience “all columns” tensor.

## Label policy

| Quantity | Preferred source | Limitation |
| --- | --- | --- |
| P0 training forward-speed reference | Quality-checked phone GNSS speed aligned to the phone clock; observed values behave as m/s despite the header | Weak/self-derived label; unavailable to runtime during simulated outages |
| Later paired forward-speed reference | V indicated speed after verified cross-clock alignment, converted with verified units | Reference measurement, not exact truth; may have bias |
| Speed cross-check | V GPS speed and wheel rates | Wheel angular velocity needs a validated effective radius to become linear speed |
| P0 evaluation position reference | Withheld phone GNSS latitude/longitude | Time-aligned and finite-accuracy; unavailable to runtime during outages |
| Later paired position reference | Quality-checked V GPS after verified cross-clock alignment | Finite accuracy; exclude/report unreliable intervals |
| Stop labels | Sustained agreement between credible speed sources | Use hysteresis; avoid labeling slow crawl as stationary |
| Phone-only exploratory labels | Credible phone GNSS in open sky | Weak/self-derived reference; report separately from paired evaluation |
| Bump/landmark labels | Independent local annotations and landmark locations | Not supplied as a reliable event-level set by IO-VNBD |

Wheel rates in rad/s are not a ready-made m/s label. Tyre pressure and slip can change their relationship to speed. Likewise, a V-file GPS position is a practical reference for preliminary screening, not survey-grade lane truth.

## Leakage-resistant splits

Freeze a manifest before fitting normalization, model parameters, thresholds, or uncertainty calibration.

1. Link categorized/uncategorized, synchronized/unsynchronized, renamed, and clipped versions to a parent recording.
2. Group related segments such as S3a/b/c and adjacent Vta/Vtb/Vw sections when their parent journey or overlapping motion identifies a shared session. Check paper metadata and timestamps; do not infer independence solely from filenames.
3. Assign parent groups wholly to train, validation, or test. Build windows only after assignment.
4. P0 trains on Driver A and non-Vtb Driver E families, validates on Driver B, and holds out the complete Vtb family. This is a family/session holdout, not an unseen-driver claim. Driver D is retained as an exploratory transfer/failure-analysis set because its phone GNSS reference contains sparse/discontinuous behavior that makes the initial distance benchmark unreliable. Report the number of independent parent journeys and add clean unseen-driver tests when feasible.
5. Treat F/G/H phone-only data as a separate exploratory transfer benchmark. Their GNSS references and available channels differ from the paired subset.
6. Reserve unseen local phone/vehicle/mount sessions for later Indian-road testing. Do not update the generic model on those sessions and still label them untouched tests.

Bias estimation or scale adaptation from trusted data *before* a simulated outage is allowed if it is part of the deployed algorithm and declared in the protocol. It cannot use future test labels.

## Feature path

Build a six-channel core from verified, gravity-handled acceleration and gyro vectors. Supply actual `dt`, validity masks, and, for the anchored model, the prior estimated speed/state confidence as separate context. Magnetometer is optional and quality-gated; a model must continue with the declared missing-sensor behavior.

Initial window: 20 samples at 10 Hz, ending at the current time. Compare a longer causal window on validation. Train and deploy the same preprocessing. A causal low-pass filter may reduce noise but cannot remove all road dynamics without also removing braking/turn information.

Do not use latitude, longitude, GPS speed, GPS heading, vehicle speed, steering angle, or wheel speed as IMU feature channels during an outage. Initialization from the last accepted GNSS state is a separate, permitted input condition.

At 10 Hz, frequencies above 5 Hz are not recoverable as unique signal content. IO-VNBD therefore cannot establish a high-frequency tyre-vibration odometer. Collect higher-rate data for that experiment.

## Initial model and training experiment

Use a compact causal temporal convolutional model as the default. It has a short export path and no requirement to retain an unbounded sequence history. A GRU is the comparison model, not a second mandatory product branch.

Proposed initial network:

| Part | Initial design |
| --- | --- |
| Encoder | Three small causal Conv1D blocks, approximately 32 channels, kernel size 3, increasing dilation |
| Context | Prior estimated velocity/confidence for anchored mode; no current withheld GNSS |
| Motion head | Residual to the physical speed prediction; direct absolute-speed head as an ablation |
| Uncertainty head | Positive variance via a bounded transform and a variance floor |
| Stop head | Stop probability, used only with validated additional consistency checks |
| Objective | Speed error + calibrated likelihood term + stop classification; relative-distance consistency as a later ablation |
| Export | ONNX, initially floating point; quantization only after exported-model parity is measured |

For a speed estimate `mu`, reference `v_ref`, and predicted log variance `s`, a candidate likelihood term is `0.5 * exp(-s) * (v_ref - mu)^2 + 0.5 * s`. Clamp pathological variance predictions and assess calibration rather than interpreting this loss as a guarantee.

Fit scalers on training data only. Balance long stationary segments and moving segments so the model cannot win a speed metric by frequently predicting zero. Report moving-only, stationary, low-speed, and turning performance separately.

Train anchored-state behavior using rollouts and simulated outages. Teacher-forcing the reference speed at every step and then testing recursively would create a major train/deploy mismatch. During held-out blackout inference, every prior state must come from the engine's own preceding prediction.

Use physically consistent augmentations: small sensor bias, noise, timing jitter, missing samples, and common rigid rotations of all relevant vectors. Arbitrarily rotating acceleration without gyro/gravity produces an impossible example. Synthetic perturbations supplement, rather than prove, real phone/mount transfer.

## Experiment sequence

| Experiment | Question answered |
| --- | --- |
| E0: last accepted speed + gyro | Is ML better than carrying the entry speed through the outage? |
| E1: physical propagation + fixed-noise fusion | What does the non-ML estimator achieve? |
| E2: direct speed model | Does a short IMU window learn useful speed information on held-out journeys? |
| E3: anchored residual model | Does preserving known entry velocity improve rollout drift? |
| E4: learned uncertainty | Does predicted uncertainty improve calibration and fusion versus a fixed value? |
| E5: gated stop updates | Do stops help without harmful false zero-speed decisions? |
| E6: map candidates and adaptation | What additional gain comes from these modules on the same fixed outages? |

A prior study demonstrates learned car-speed pseudo-measurements in a dead-reckoning system, supporting this as a research direction. Its data and results do not establish performance on our phone/dataset combination. [Learning Car Speed Using Inertial Sensors](https://arxiv.org/abs/2205.07883)

## Local collection plan

Start with a small pilot, then expand toward 2–4 hours if resources allow. This is an initial engineering dataset, not proof of broad generalization. Record measured sample intervals, raw acceleration/gyro, optional magnetometer, GNSS with source timestamps and accuracy, phone model, mount, and vehicle profile.

Include stationary calibration, straight steady driving, acceleration/braking, turns, stop-and-go, gradients, rough roads, and independently annotated speed breakers. Use a passenger/logger operator; do not ask a driver to manipulate the phone while driving. Controlled mounting changes should be recorded when safely possible.

Open-sky GNSS masking provides a reference during the artificial outage. A real tunnel requires an independent position reference or a limited endpoint check; entry/exit markers alone do not validate the whole tunnel trajectory. Never build a landmark map from the same held-out outage's hidden trajectory.
