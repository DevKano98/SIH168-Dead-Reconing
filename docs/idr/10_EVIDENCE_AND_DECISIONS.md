# 10. Evidence, corrections, and design decisions

## Existing local evidence

| Evidence | What it supports | What it does not prove |
| --- | --- | --- |
| [Dataset catalog](../BENCHMARKS_AND_EVIDENCE.md) | File inventory, parsed schemas/ranges, missing cells, duplicate counts | Correct semantics for every field, synchronization, learned navigation performance |
| [IO-VNBD paper](../../README_1.pdf) | Published experiment setup and run metadata | Perfect labels, universal schema consistency, phone deployment accuracy |
| Raw S-M sample comparison | Identical gyro triplet values can appear under YPR and XYZ labels | The physical axis mapping without additional validation |
| Raw S-A4 sample and raw profile | Values are inconsistent with headers from the inserted blank onward | A validated repair without checking every affected row |
| Pair row-count review from catalog | 9 of 72 canonical synchronized pairs differ in length | That the other 63 pairs are synchronized correctly |

No trained model, implemented IDR runtime, Android app, navigation report, or measured drift result was found in the workspace at the start of this documentation task. This package does not change that implementation status.

## Corrections to the supplied advice

| Advice/claim | Correct interpretation used in this design |
| --- | --- |
| V files are “ground truth” | They are useful reference measurements with finite error and quality issues |
| S files have exactly 24 columns | The scan found 18-, 24-, and 25-column variants |
| Row-wise S/V pairing is safe in synchronized folders | Unequal row counts and potential clock offsets require explicit pairing |
| Gyro labels directly give vehicle yaw | Mounting and source-axis semantics must be verified |
| Error accumulation is always exponential | A constant acceleration bias gives quadratic position error; mechanisms differ |
| Map constraints make position a solved 1D problem | Only conditional on a correct road hypothesis; along-road and route ambiguity remain |
| Each turn resets error | A distinctive, correctly associated turn can constrain error; repeated geometry may not |
| ZUPT wipes out position drift | It constrains velocity, not accumulated absolute position |
| Low IMU variance proves a stop | Smooth constant-speed travel can be uninformative too |
| NHC means zero upward velocity | Constraints are frame- and motion-dependent; ramps and lean need appropriate modeling |
| The live UI can always show true drift | True error requires an independent reference; live operation usually shows estimated uncertainty |
| Smartphone web streaming completes edge deployment | It demonstrates streaming; laptop inference remains laptop inference |
| A 200 Hz input profile proves external-sensor accuracy | Throughput and calibrated navigation accuracy need separate evidence |
| Speed breakers automatically correct position | Landmarks require independently known locations, detection and association |
| Innovation gating means spoof-proof | It is a consistency check with measurable failure cases |
| Meeting 10% drift means lane-level | These are different accuracy criteria |

## Primary sources consulted

These support design choices and technical interfaces, not claims that this proposed implementation achieves their results.

| Source | Relevant use |
| --- | --- |
| [AI-IMU Dead-Reckoning](https://arxiv.org/abs/1904.06064) | Prior work combining vehicle inertial filtering with learned noise adaptation; different dataset/sensor conditions |
| [Learning Car Speed Using Inertial Sensors](https://arxiv.org/abs/2205.07883) | Prior work using learned car-speed pseudo-measurements in dead reckoning |
| [TLIO author project](https://cathias.github.io/TLIO/) | Learned relative motion and uncertainty within an EKF; pedestrian setting |
| [Newson and Krumm map matching](https://www.microsoft.com/en-us/research/publication/hidden-markov-map-matching-noise-sparseness/) | Established HMM formulation for road-sequence inference |
| [Android sensor overview](https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview) | Sensor coordinate/rate/platform constraints to check in the native adapter |
| [Android Location](https://developer.android.com/reference/android/location/Location) | Measurement timestamps, speed, and accuracy field semantics |
| [ONNX Runtime mobile](https://onnxruntime.ai/docs/tutorials/mobile/) | Planned model-runtime route across desktop and Android |
| [MapLibre Android offline API](https://maplibre.org/maplibre-native/android/api/-map-libre%20-native%20-android/org.maplibre.android.offline/index.html) | Candidate native map display capability, separate from the navigation graph |
| [W3C motion/orientation specification](https://www.w3.org/TR/orientation-event/) | Browser sensor-access constraints for an optional streaming bridge |
| [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) | Choose a suitable source/packaging route for offline display assets |

## Decision register

| ID | Decision | Reason | Revisit when |
| --- | --- | --- | --- |
| D01 | SDK is the product; Studio is a client | Makes integration and portability demonstrable | Stable API feedback from another client |
| D02 | P0 uses deterministic held-out replay | Produces reproducible screening evidence | Android data path is ready |
| D03 | Mounted-car profile first | Matches the immediate paired training evidence | Independent motorcycle/mount validation exists |
| D04 | Small causal temporal CNN first | Bounded history and a manageable export path | GRU comparison establishes a useful gain |
| D05 | Compare direct and anchored speed models | Absolute velocity has observability limits | Held-out rollout evidence selects the model |
| D06 | Learned uncertainty is measured, not trusted automatically | Correlated IMU/model errors can create overconfidence | Calibration and correlation-aware filtering improve |
| D07 | P0 planar filter; later 3D error-state filter | Keeps an initial demonstrator understandable | Gradients/lean/external profiles require 3D states |
| D08 | Road matching is optional and multi-hypothesis | Prevents incorrect forced road locks | Reviewed graph and road-level validation are ready |
| D09 | ONNX is the proposed export path | One runtime family for desktop and Android | Operator support, size or phone timing prevents use |
| D10 | Native Android is the final phone path | Gives explicit sensor and runtime control | Team constraints justify another measured option |
| D11 | No numerical accuracy claims before experiments | Prevents confusing goals with results | Artifacts supply measured values |
| D12 | Existing raw files remain intact | Preserves provenance and reproducibility | No reason to modify originals for this plan |

## Assumptions and unresolved items

- The first video is for preliminary screening; the supplied statement also requires a model and position plots, so the video is not the only artifact.
- Team size, deadline, target Android device, external sensor availability, and hardware budget remain unspecified. The roadmap uses person-day ranges and device-specific measurement gates.
- IO-VNBD unit/axis/synchronization ambiguities are implementation blockers for training, not blockers to designing the product.
- The main model, stop thresholds, gate settings, covariance calibration, and best window length must be selected through validation.
- The initial title is provisional. No brand or novelty clearance has been performed.
- This documentation defines a technically testable plan; whether it meets the drift benchmark is an empirical question.

## Documentation completion map

| Requested outcome | Location |
| --- | --- |
| Comprehensive SDK product ideation | Product vision, architecture, SDK specification |
| End-to-end prototype definition | Requirements, data/model plan, evaluation, prototype/video |
| What to show in the video | Screens, scenarios, storyboard and claim checklist |
| Full documentation for implementation | Roadmap, API contracts, source register, templates and root index |
| Path to the complete final solution | P1/P2/P3 requirements and release gates |
