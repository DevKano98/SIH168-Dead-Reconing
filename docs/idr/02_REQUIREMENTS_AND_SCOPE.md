# 2. Requirements and release scope

The scope below preserves the complete problem statement while giving the first prototype a finishable release boundary. All features are **planned**, unless explicitly identified as existing dataset evidence.

## Releases

| Release | Purpose | Included |
| --- | --- | --- |
| P0: screening prototype | Show a real end-to-end SDK and preliminary AI results | Reviewed data, alignment, trained motion model, planar fusion, GNSS masking, uncertainty output, Studio, headless integration, reports |
| P1: road and robustness prototype | Demonstrate constraints and recovery | Candidate-based offline map matching, guarded stop updates, GNSS consistency tests, mounting-change handling, controlled adaptation |
| P2: phone demonstrator | Meet the on-device application requirement | Android sensor adapter, embedded runtime and model, offline map display, local recordings, phone performance tests |
| P3: external IMU and broader validation | Meet portable edge-engine and expanded-domain requirements | Native runtime package, external sensor calibration profiles, 200 Hz scheduling, real external data, two-wheeler validation |

P0 provides a complete input-to-result workflow. It is not a claim that all final requirements are already delivered. A visually attractive replay alone is insufficient: the model, SDK, evaluation outputs, and integration example are mandatory P0 artifacts.

## Requirement traceability

| ID | Requirement | First release | Completion evidence |
| --- | --- | --- | --- |
| R01 | Accept accelerometer and gyro without OBD at inference | P0 | Event log and integration example contain no vehicle-speed input |
| R02 | Initial phone-to-vehicle alignment and gravity handling | P0 | Documented axis mapping and orientation tests; stationary and turn checks |
| R03 | Learned velocity/motion correction | P0 | Trained checkpoint, held-out speed error, position results versus non-ML baseline |
| R04 | Noise and bias management | P0, expanded P1 | Causal filtering specification and bias/rough-road ablations |
| R05 | Continuous GNSS-aided and outage estimation | P0 | One uninterrupted estimator trace across loss and recovery |
| R06 | AI-assisted GNSS/INS fusion | P0 motion uncertainty, P1 adaptation | Learned versus fixed covariance/measurement ablation |
| R07 | Offline map constraints and matching | P1 | Correct-road tests plus ambiguity and off-map behavior |
| R08 | Non-holonomic constraints when appropriate | P1 | Enabled/disabled comparisons and rejection on invalid motion |
| R09 | Re-alignment after phone movement | P1 | Labeled movement event, degraded state, recovery time and errors |
| R10 | Drift under 10% during blackout | P0 evaluation onward | Per-outage error/distance table and aggregate pass rate, with failures |
| R11 | Approximately 10 Hz phone position updates | P2 | Sustained actual-device timestamp and latency report |
| R12 | Approximately 200 Hz external-IMU processing | P3 | Real sensor replay/live timing; separately measured accuracy |
| R13 | Working mobile navigation interface | P2 | APK running locally with network disabled and offline assets |
| R14 | Reusable edge-deployable software engine | P0 Python API; P3 native package | Installable package, second client, contract tests and native artifacts |
| R15 | Preliminary models and position plots for screening | P0 | Checkpoint, exported model, reference/predicted plots and experiment manifest |
| R16 | Smooth GNSS recovery | P0, hardened P1 | First-fix gating, estimator correction trace, distinct display smoothing |
| R17 | Lane-level aspiration | Research beyond P0 | Independent lane-level reference, lane-map quality, lateral-error metrics; not inferred from R10 |

## P0 acceptance gates

| Gate | Required result |
| --- | --- |
| G0: data ready | Canonical run list, valid units/axes, timestamp pairing, parent-session split, rejected-run log |
| G1: real ML | Trained causal model; model card; held-out comparison against last-speed and non-ML baselines |
| G2: engine ready | SDK runs headless, emits states through GNSS loss/recovery, records uncertainty and health |
| G3: honest evaluation | No withheld or future measurements enter the engine; outage metrics and plots are exported |
| G4: demonstration ready | Studio is connected to SDK outputs; video scenario is repeatable and displays measured results |
| G5: reproducibility | Another user can install, load the same model/run configuration, and reproduce a report |

If the drift target is missed, P0 can still demonstrate valid preliminary research. The report must show the actual result and next experiment; neither map rendering nor animation can substitute for an accuracy result.

## P0 exclusions with explicit continuation

| Feature | Why it is not a P0 dependency | Continuation |
| --- | --- | --- |
| Browser phone-to-laptop streaming | Browser permission, sensor, and scheduling differences add integration risk | Optional bridge after deterministic replay; label execution location |
| Full navigation routing and turn-by-turn directions | The SDK estimates state; routing is a separate client service | Add to Android client after positioning is evaluated |
| Learned pothole/speed-breaker landmarks | IO-VNBD lacks a sufficient event-level landmark reference set | Collect high-rate data and an independent landmark map |
| Automatic vehicle-type recognition | Classifying a vehicle does not prove the corresponding estimator works | Initially select an explicit validated profile |
| Pocket/handheld phone tracking | Sensor motion is no longer rigidly attached to the vehicle | Separate motion model and validation program |
| Universal spoofing protection | Innovation gating has known consistency limitations | Robustness experiments with bounded claims |
| Blockchain or vehicle mesh | No dependency in the supplied positioning requirements | No allocation in this product plan |

## Proposed operational targets

These are engineering targets to measure, not current results.

- P0 model input: a causal 2-second window at 10 Hz, with a documented longer-window ablation.
- P0 replay: sustained 10 Hz state publication at real-time playback on the recorded test laptop.
- P2 phone: 10 Hz position output, with p95 total estimator work below 100 ms per output interval and recorded missed deadlines.
- Initial model-pack size budget: below 5 MB; measure runtime memory separately because model size is not process memory.
- P3 propagation: average work below the 5 ms period at 200 Hz, with p95/p99 latency and queue growth reported. Heavy map and model updates may run more slowly than propagation.
- GNSS loss: no estimator restart. Missing-fix detection latency is measured against the expected fix cadence; it cannot be guaranteed within milliseconds of an unobservable RF failure.

## Definition of a trustworthy demo

The run is held out from training; the outage schedule and model are frozen before reporting; the reference is visibly marked as evaluation-only; failed cases remain in the report; live error is shown only when a reference is available. No result cell contains a fabricated success value.

## Scenario coverage across the product

This matrix distinguishes required experiments from unsupported promises. A release assignment means work is planned, not that the capability has been demonstrated.

| Scenario | Planned treatment | Evidence / boundary |
| --- | --- | --- |
| Straight tunnel-like blackout | P0 preserved entry state, learned motion, growing uncertainty | Open-sky masking first; real tunnel reference is a separate test |
| Turns, roundabouts, braking | P0 alignment and heading/velocity estimation | Held-out trajectory errors by motion category |
| Stop-and-go and crawling | P1 guarded zero-velocity updates | False stops and low-speed errors, not just stop recall |
| Potholes and rough-road shocks | P0 conservative filtering; P2 measured local validation | Navigation error and recovery after independently annotated events |
| Speed-breaker landmarks | P2/P3 experimental extension | Detection and correct association to an independently built landmark map |
| Flyover gradients and banking | P2/P3 attitude-aware propagation | Reference trajectory and comparison with planar approximation |
| Parallel/service roads and divided highways | P1 multiple road candidates | Wrong-road lock rate, ambiguity and unmatched behavior |
| Multi-level parking | Later 3D/floor-aware research within the final application scope | Requires suitable floor geometry and independent vertical/floor evidence; no P0 floor claim |
| Magnetic disturbance | Optional magnetometer rejected/down-weighted | Tests with and without magnetic aid |
| Phone nudged in holder | P1 suspect-alignment state and re-estimation | Detection and recovery, plus false alarms on actual vehicle maneuvers |
| Two-wheelers and loose mounts | P2/P3 explicit profile and new recordings | Lean-aware, mount-specific accuracy; no automatic transfer claim |
| Pocket or handheld phone | Future scope beyond the initial mounted-phone product | Requires separating phone motion from vehicle motion |
| Degraded GNSS and urban-canyon jumps | P1 quality gate and recovery policy | Defined corruption tests plus clean-fix acceptance |
| Dropped samples or timestamp jitter | P0 adapter checks and gap policy | Reproducible timing-injection tests |
| Temperature/phone-model variation | P2/P3 profile validation and optional calibration | Actual device/temperature recordings, not noise augmentation alone |
| Offline operation | Local runtime and permitted map/application assets | Disconnect network and repeat the demonstration |
| Long outages beyond the benchmark | Stress tests and honest uncertainty | Error growth and failure limits, not indefinite bounded-drift claims |
| Restart while GNSS is absent | Later versioned state recovery with age validation | Unknown motion during downtime remains uncertain |
| Cold start without an absolute fix | Relative tracking only when enabled | No invented latitude/longitude or absolute heading |
| External IMU at 200 Hz | P3 clock/frame/noise adapter and rate scheduling | Real external data, latency report and separate accuracy evidence |
