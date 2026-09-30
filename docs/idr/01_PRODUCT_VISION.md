# 1. Product vision

## The product

Continuum IDR is a local navigation SDK for applications that must continue estimating vehicle motion when GNSS becomes unavailable or unreliable. Its primary output is an estimate with uncertainty and a validity status. The SDK does not promise to manufacture precise absolute position when the necessary observations are missing.

The central product promise is **continuity with measurable confidence**: the client keeps receiving time-stamped estimates, knows which measurements were accepted, and can change its behavior when confidence falls.

The first target user is a developer building a fleet, delivery, ride-hailing, or emergency-response navigation application. The immediate evaluation user is a judge who needs to see a trained model, a position plot, a reproducible outage experiment, and a credible deployment path.

## Product components

| Component | Responsibility | Deliverable |
| --- | --- | --- |
| IDR Core | Alignment, propagation, fusion, quality states, uncertainty | Importable Python prototype; later native library |
| Model Pack | Small learned motion model, normalization, calibration, compatibility metadata | Checkpoint, exported model, model card |
| Sensor Adapters | IO-VNBD, Android, and external IMU conversion into one event contract | Adapters with explicit units, axes, and clock mapping |
| Map Pack | Offline road graph and optional independently surveyed landmarks | Versioned regional graph; optional display assets |
| Evaluation Kit | GNSS masking, reference comparison, baselines, reports | CLI and reproducible experiment manifests |
| Continuum Studio | Replay, diagnostics, visual comparison, result export | Browser dashboard using the SDK |
| Android Reference App | Embedded engine, local sensors, offline display | Later APK and Android SDK integration sample |

These components belong to one product. Studio is a client of the SDK; it must not contain a second navigation algorithm that behaves differently from the packaged engine.

## User journeys

**Application developer:** install the runtime, load a compatible model/profile, deliver ordered sensor events, subscribe to state updates, and draw the returned position. The app handles permissions, recording, and display. The SDK handles estimation.

**Research or ML developer:** build a reviewed dataset manifest, train a model, run held-out outage tests, export a model pack, and compare the exported runtime against the training runtime.

**Judge:** select a documented run, inspect the baseline, withhold GNSS, observe the estimate and uncertainty, restore GNSS, and inspect the exported report. A second client demonstrates that the same engine can be reused.

**Driver in the future Android app:** begin a trip, complete an initial alignment period, see sensor readiness, and receive uninterrupted but confidence-aware location estimates. A driver should not need to understand filter matrices or ML architecture.

## Differentiation to demonstrate

1. **A reusable engine with transparent evidence.** The same API powers a replay, a headless client, and later Android. Reports identify the model, inputs, outage schedule, and hardware.
2. **Motion estimates with calibrated confidence.** A learned model supplies a velocity-related estimate and uncertainty to a physical estimator. Improvements must survive held-out tests and comparisons with fixed uncertainty.
3. **Adaptation to the phone and mounting.** Reliable GNSS periods help estimate a small correction and detect mounting changes. This is a controlled adaptation mechanism, not unlimited online retraining.
4. **Road-aware inference with an explicit unmatched state.** Maps provide useful constraints when the road hypothesis is credible. The engine retains uncertainty at parallel roads, ramps, and unmapped places.
5. **An Indian-road validation program.** Mounted car and two-wheeler recordings, bumps, gradients, and different phones become evidence for deployment relevance. A speed-breaker detector becomes a navigation aid only when the landmark has an independently known position and reliable association.

Learned inertial odometry, adaptive filtering, and map matching already have substantial prior work. The proposal should claim an engineered integration and measured improvements in the chosen deployment setting, rather than invention of these ideas. See [the evidence register](10_EVIDENCE_AND_DECISIONS.md).

## Important product boundaries

- The first prototype supports a mounted phone in a forward-driving car. Handheld phones, pockets, motorcycles, reverse driving, and parking floors need additional models, states, or validation.
- GNSS outages and internet outages are different. Maps and inference can be offline while GNSS is available; hiding GNSS in replay simulates measurement loss without disabling the internet.
- A known initial position, heading, and velocity are part of the normal outage scenario. A cold start without any absolute-position source cannot produce a trustworthy latitude/longitude.
- Less than 10% distance-normalized drift is the supplied benchmark. It does not imply lane-level accuracy: a 100 m error over 1 km may satisfy that ratio while being unsuitable for lane guidance.
- A GNSS consistency gate identifies suspicious measurements; it does not certify detection of every jammer, spoofer, or gradual position attack.
- The final product uses local inference. Cloud services may train models or distribute packs, but a live cloud dependency would undermine the outage use case.

## What success means at each stage

**Screening prototype:** a trained model and packaged SDK produce a trajectory on held-out IO-VNBD data, with GNSS withheld from the estimator, baseline comparisons, and downloadable evidence. The observed benchmark pass rate is reported honestly, including failures.

**Product demonstrator:** the same estimation behavior runs in an Android application with measured phone latency, offline assets, GNSS recovery, and recorded local-road tests.

**External-sensor release:** an external IMU adapter, correct noise and sampling profile, timing evidence, and reference-based accuracy evaluation. Accepting a 200 Hz event stream demonstrates software compatibility; it does not establish FOG-grade positioning accuracy.
