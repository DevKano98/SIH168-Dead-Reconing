# 9. Proposal wording and judge questions

## Working title and pitch

**Continuum IDR: an uncertainty-aware navigation SDK for GNSS interruptions.**

“We are developing a reusable engine that combines smartphone inertial measurements, learned motion estimates, and GNSS quality checks to keep estimating vehicle position through GNSS interruptions. A reproducible evaluation toolkit measures its drift, and the same sensor interface supports a path from desktop experiments to Android and external IMUs.”

This wording describes the proposed product. Once implementation is complete, replace future-tense statements only for features demonstrated by artifacts.

## Proposal abstract draft

Vehicle navigation becomes unreliable when satellite measurements are blocked or corrupted. Low-cost phone IMUs continue sensing motion, but biases, mounting errors, vibration, and weak observability make unaided position estimates drift. We propose Continuum IDR, a modular navigation SDK that combines causal inertial processing with a compact learned motion model and a physical fusion estimator.

The engine maintains a single running state while GNSS observations are accepted, rejected, or unavailable. A learned motion estimate and its uncertainty support dead reckoning from the last accepted state. Subsequent development adds candidate-based offline road constraints, controlled mounting recovery, and calibration from trusted GNSS periods. The SDK exposes position, velocity, heading, uncertainty, and quality information to application developers.

Our screening prototype will use a reviewed subset of IO-VNBD with parent-session separation and simulated GNSS outages. A replay application will display estimated and withheld-reference trajectories, while an independent evaluator measures endpoint error, outage drift, and recovery behavior against simple baselines. The submission will include the preliminary model, model card, SDK integration example, position plots, and reproducible experiment configuration. Android inference and independent Indian-road and external-IMU validation are subsequent release milestones. The supplied sub-10% drift benchmark is an evaluation target, not a claimed result before measurement.

## Suggested six-slide deck

| Slide | Main message | Evidence or visual |
| --- | --- | --- |
| 1 | GNSS interruptions need continuous, confidence-aware positioning | Simple outage scenario |
| 2 | A reusable SDK is the product | Input/output API and product components |
| 3 | Hybrid learned motion plus physical estimation | Architecture diagram and uncertainty output |
| 4 | We understand the dataset and prevent leakage | Canonical pairing, grouped split, withheld-reference diagram |
| 5 | Here is the actual prototype and measured performance | Generated trajectory, baseline table, video still |
| 6 | Here is the route to the complete deliverable | Android/external-sensor milestones and known limitations |

Before experiments are complete, slide 5 must say `Planned experiment` and show no invented performance. For screening, replace it with real outputs and attach the model as required.

## Questions to prepare for

**Why is this an SDK rather than just an app?**

The estimator is an importable package with a typed sensor interface and versioned model/profile. Studio and a headless example use the same package. Android later embeds the runtime. Demonstrate those two integrations rather than relying on the label “SDK.”

**What is the AI contribution?**

A small model learns motion corrections and uncertainty from IMU history. The evaluator compares the model with physical and last-speed baselines, and compares learned uncertainty with a fixed value. The claimed contribution is the improvement actually measured in those comparisons.

**Can an IMU determine any constant speed?**

No. Ideal inertial measurements alone do not uniquely distinguish different straight constant speeds. The engine preserves a credible entry state, uses motion history and learned priors, and grows uncertainty when evidence is weak.

**Are the vehicle files perfect ground truth?**

No. They provide useful speed and GPS references with finite error. We quality-check them and keep them outside test-time inference. Lane-level verification would require a better reference and an appropriate lane map.

**How do you prove GPS is really absent from the engine?**

The replay adapter suppresses every GNSS-derived event during the saved interval. The runtime API cannot receive the withheld reference. Logs and automated leakage checks establish that boundary.

**Why not compare only with a frozen marker?**

A frozen marker is an intuitive visual baseline, but last-known-speed plus gyro and a non-ML estimator are stronger quantitative baselines. The report includes them.

**Does ZUPT reset all drift?**

It constrains velocity when a stop is correctly detected and may help estimate bias. Accumulated position and absolute-heading errors remain. False stops during smooth travel can be harmful.

**Does the road map remove all position uncertainty?**

No. The road itself may be ambiguous or wrong, and distance along it remains uncertain. We retain road candidates and unmatched output rather than always choosing the closest road.

**Can you detect jamming or spoofing?**

The proposed quality gate checks consistency, freshness, and reported quality. We test specified faults and report false decisions. That is not a universal security guarantee.

**Why use IO-VNBD if it is only around 10 Hz?**

It is the required screening dataset and supports initial vehicle-motion experiments. High-frequency vibration or precise bump signatures need separate higher-rate recordings. We will not claim that upsampling restores missing signal bandwidth.

**Where do Indian roads and motorcycles enter?**

They are a later explicit validation program, with new phones/mounts, reference quality, and vehicle profiles. Speed breakers are candidate landmarks only after their independent locations and association reliability have been established.

**Does the current prototype run on the phone?**

P0 runs on the documented desktop device. A phone streaming sensors to a laptop is labeled accordingly. On-device inference is demonstrated only after the Android runtime, model, and actual-device timing tests exist.

**What does external-IMU support mean?**

The API supports sensor profiles and timestamps independent of Android. Accuracy still depends on calibration, noise characteristics, rate, and training coverage. Real external-sensor tests establish performance; a replay adapter alone establishes compatibility.

**How will you show the 200 Hz requirement?**

Measure real sensor event handling and propagation with timestamped outputs and latency statistics. Model and map updates may run at slower rates. Accuracy and throughput are reported separately.

**What happens if the target is not met?**

We report the actual pass rate, error distribution, and failure cases, then use ablations to identify whether speed, heading, alignment, or reference quality is responsible. Preliminary results remain honest evidence for a proposal.

## Claim ladder

| Statement | Evidence needed before saying it |
| --- | --- |
| “We designed the SDK and prototype” | This documentation package |
| “We trained a preliminary model” | Actual checkpoint, split and model card |
| “The SDK runs through simulated outages” | Saved causal predictions and withholding log |
| “It improved drift” | Comparison on the same frozen held-out windows |
| “It met the benchmark” | Explicit test population, pass rate and failures |
| “It runs on a phone” | Embedded runtime on a named physical device |
| “It works on Indian roads/external IMUs” | Independent domain-specific recordings and reference-based metrics |

The documentation currently supports the first statement. The roadmap identifies the artifacts required for the rest.
