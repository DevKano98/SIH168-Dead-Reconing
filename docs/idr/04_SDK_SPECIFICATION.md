# 4. SDK specification

**Status: proposed public contract, version 0.1. These examples describe the intended API and are not executable in the current repository.**

## Package boundary

The package name proposed for implementation is `continuum_idr`. The engine has no mandatory dependency on a browser, network, database, or map renderer. An optional map matcher is supplied through an interface. Sensor readers, file readers, and HTTP servers are adapters.

```python
# Illustrative API; implementation is a roadmap deliverable.
from continuum_idr import IDREngine, EngineConfig, SensorProfile

engine = IDREngine(
    config=EngineConfig.load("configs/car_phone.json"),
    sensor_profile=SensorProfile.load("profiles/iovnbd_reviewed.json"),
    model_bundle="models/motion_v1/",
    map_provider=None,
)

for event in source.events_in_timestamp_order():
    if event.kind == "imu":
        engine.on_imu(event.sample)
    elif event.kind == "gnss":
        engine.on_gnss(event.fix)
    state = engine.get_state()
    client.consume(state)

engine.close()
```

Both Studio and the headless example call this package. A replay controller may remove GNSS events, but the engine has no `reference_path` or `true_speed` argument.

## Public methods

| Method | Meaning |
| --- | --- |
| `IDREngine(config, sensor_profile, model_bundle, map_provider=None)` | Validate compatibility and allocate state; no implicit network access |
| `initialize(initial_state)` | Optional explicit seed from an accepted or externally known state, with uncertainty and provenance |
| `on_imu(sample) -> IngestResult` | Process an IMU sample or return a typed rejection/quality result |
| `on_gnss(fix) -> IngestResult` | Validate and gate a GNSS fix; return accepted/rejected reason |
| `tick(timestamp_ns) -> None` | Advance freshness/status checks when no measurement arrives; never invent an IMU sample |
| `get_state() -> NavigationState` | Return an immutable snapshot; no hidden filtering or wall-clock extrapolation |
| `get_diagnostics() -> Diagnostics` | Timing, buffers, quality counters and last measurement decisions |
| `reset(reason) -> None` | Clear dynamic state, history and covariance while retaining validated configuration/model |
| `close() -> None` | Release resources; later ingestion fails explicitly |

P0 uses a single event-processing thread. A live adapter owns a bounded queue and serializes calls. A read-only snapshot may be exposed to clients. Overflow drops are counted and surfaced; a silent growing backlog is unacceptable.

## Input contracts

### IMU sample

| Field | Type / unit | Requirement |
| --- | --- | --- |
| `timestamp_ns` | integer, monotonic ns | Measurement time in the declared clock domain |
| `clock_id` | string | Must match the engine session domain after adapter conversion |
| `sensor_id` | string | Selects the verified sensor profile |
| `accel_mps2` | float[3] | Raw specific-force convention; gravity handling documented in profile |
| `gyro_radps` | float[3] | Sensor-axis angular velocity |
| `mag_uT` | optional float[3] | Optional aid; missing is explicit, not a zero vector |
| `gravity_mps2` | optional float[3] | Only accepted with documented convention/source |
| `temperature_c` | optional float | Used only by a calibrated temperature model |
| `quality_flags` | string[] | Saturation, hardware failure, interpolation, or other provenance |

### GNSS fix

| Field | Type / unit | Requirement |
| --- | --- | --- |
| `timestamp_ns`, `clock_id` | integer / string | Measurement time, not callback arrival time |
| `lat_deg`, `lon_deg` | float | WGS84; valid range required |
| `altitude_m` | optional float | Datum must be recorded; P0 does not depend on altitude |
| `speed_mps` | optional float | Declared valid; unit conversion occurs in the adapter |
| `course_deg` | optional float | Clockwise from north; quality/low-speed checks apply |
| `horizontal_accuracy_m` | optional float | Accuracy semantics recorded by provider, not assumed to be covariance |
| `position_covariance_enu_m2` | optional matrix | If supplied, frame and statistical meaning must be declared |
| `speed_std_mps` | optional float | Validated uncertainty, when available |
| `provider` | string | Raw GNSS, platform-fused, dataset, or another identified source |
| `fix_id` | string | Supports duplicate-fix detection |
| `quality_flags` | string[] | Suspect, stale, synthetic injection, or source-specific status |

A repeated latitude/longitude can be a genuinely stationary new fix. Deduplication therefore uses source timestamp/fix identity, not coordinates alone. Android provides elapsed-realtime timestamps and separate position/speed accuracy fields; preserve their meaning in the adapter. [Android Location API](https://developer.android.com/reference/android/location/Location)

## Output contract

`NavigationState` contains:

| Field | Meaning |
| --- | --- |
| `timestamp_ns`, `sequence` | State time and monotonically increasing output index |
| `tracking_mode` | `UNINITIALIZED`, `ALIGNING`, `GNSS_AIDED`, `DEAD_RECKONING`, or `RECOVERING` |
| `health_flags` | Independent flags such as `LOW_CONFIDENCE`, `IMU_GAP`, `MOUNT_UNCERTAIN`, `GNSS_REJECTED` |
| `position_enu_m` | Estimate in the session's local coordinate frame, or null before initialization |
| `position_wgs84` | Latitude/longitude if an absolute anchor exists, otherwise null |
| `speed_mps`, `heading_deg` | Estimates with corresponding validity indicators |
| `position_covariance_enu_m2` | Estimated covariance, with calibration/version metadata |
| `horizontal_ellipse` | Confidence level, axes and orientation, only when computed appropriately |
| `road_match` | Optional edge ID, along-edge distance, confidence, alternatives, or unmatched |
| `last_accepted_gnss_age_s` | Measurement freshness, not network connectivity |
| `alignment_status` | Unavailable, estimating, ready, or suspect |
| `model_id`, `profile_id`, `config_hash` | Provenance needed for reproducing behavior |

**The runtime output has no true-error or true-distance field.** Those belong to `EvaluationMetrics` in the evaluation toolkit. The live UI shows estimated uncertainty; replay with an independent reference can additionally show measured error.

## Initialization and lifecycle

1. Validate the model's expected channels, normalization, sampling rate, frame, and profile.
2. Begin in `UNINITIALIZED`; collect observations without publishing fabricated absolute coordinates.
3. Move to `ALIGNING` while collecting sufficient mounting and motion information.
4. Establish an anchor, velocity, heading, and covariance from credible initialization data or an explicit `InitialState`.
5. Enter `GNSS_AIDED` while accepted fixes are current. Enter `DEAD_RECKONING` when fixes are absent/unusable; maintain the state.
6. Enter `RECOVERING` while validating returning fixes; return to aided operation when recovery criteria are met.

Health flags can indicate degraded output in any tracking mode. A cold start with no absolute reference can support relative tracking if explicitly enabled, but `position_wgs84` stays null.

## Failure and clock semantics

| Condition | Required behavior |
| --- | --- |
| NaN/Inf, wrong vector size, invalid coordinates | Reject with `INVALID_SAMPLE`; count and report |
| Wrong unit/frame/model schema | Fail configuration with `PROFILE_MISMATCH` before replay |
| Clock-domain mismatch | Reject with `CLOCK_MISMATCH`; never silently align by row index |
| Duplicate or out-of-order event | Reject/log under P0 policy; later buffering must be bounded and specified |
| Large IMU gap | Set `IMU_GAP`, increase uncertainty, and stop unsupported propagation as configured |
| Missing magnetometer | Continue if the selected model permits it |
| Missing required model channel | Refuse prediction; use a declared fallback with low confidence |
| GNSS rejected by gate | Continue propagation; record reason and innovation diagnostics |
| No plausible road | Return unmatched; preserve the unconstrained state |
| Expired saved state after restart | Require re-initialization; do not pretend the vehicle remained still |

## Versioned packs

Every model bundle should contain `model.onnx`, training checkpoint, `manifest.json`, normalization constants, uncertainty calibration parameters, model card, and export-parity results. Its manifest records model version/hash, ordered feature names, window size, sample rate, units/frame, optional-channel behavior, training/split hashes, and supported profile family.

A sensor profile records axes/signs, acceleration convention, sampling expectations, clock mapping, noise parameters, saturation limits, and validated vehicle/mount assumptions. Supporting a new external IMU may require a new calibration and retraining; changing the sampling-rate number alone is insufficient.

A map pack records geographic coverage, graph version, coordinate system, source/attribution, edge geometry, topology, direction restrictions, optional layer/bridge/tunnel attributes, and build date. Map data and display tiles are separate assets.

## Proposed command-line workflow

These commands are interface targets for implementation, not commands available today:

```text
idr audit --dataset <root> --output artifacts/audit
idr prepare --manifest manifests/runs.json --output data/processed
idr train --config configs/train_motion.json
idr evaluate --experiment experiments/screening.json
idr replay --run <run-id> --model models/motion_v1 --scenario <scenario-id>
idr studio --experiment experiments/screening.json
idr export-model --checkpoint <path> --output models/motion_v1
```

Reports must include input/model/config hashes. A packaged headless example and Studio must produce matching states for the same ordered events. A future native implementation must pass numerical parity tests within declared tolerances rather than merely exposing similarly named methods.
