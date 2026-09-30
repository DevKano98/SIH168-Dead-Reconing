# 7. The prototype to build and the video to show

## The recommended prototype

Build **Continuum IDR SDK + Continuum Studio**, a local replay application backed by the actual SDK and a trained model. A held-out IO-VNBD drive supplies phone IMU and GNSS. A controller deliberately withholds GNSS from the SDK while an isolated evaluator retains the reference trajectory.

The vehicle marker continues from estimated motion. The viewer sees the difference between the estimate, the reference, and simple baselines, including the measured error. Restoring GNSS exercises recovery in the same running estimator. A separate terminal client demonstrates the SDK without Studio.

This is a substantial screening prototype: data preparation, model training, runtime integration, a usable interface, and quantitative evidence. It does not yet demonstrate an Android application running inference locally or real underground reference accuracy.

## What must exist before recording

| Deliverable | What the viewer can verify |
| --- | --- |
| Importable SDK package | A second client calls the engine independently of the UI |
| Trained model and model card | Actual checkpoint/export and declared train/test split |
| Reviewed run manifest | The displayed run is held out and passed synchronization/unit checks |
| Replay controller | GNSS packets are visibly withheld while IMU packets continue |
| Studio | Map/trajectory, status, speed, uncertainty, and event timeline |
| Results bundle | Position plots and metrics generated from stored predictions |
| Reproduction instructions | The same experiment can be replayed by another person |

## Screens

### Screen A: Experiment setup

Show a compact setup panel containing dataset/run ID, parent session, split, model ID, sensor profile, and execution device. The device label should explicitly say `Laptop CPU` in P0. Add a reviewed-data status and a link to the model card.

Controls: choose run, choose a saved outage scenario, load model, start replay. Reject an unreviewed model/profile combination with a specific message. Do not quietly fall back to an unrelated model and continue displaying its name.

Display whether road constraints are active. A background road map alone is labeled **map display only**. P0 may use a local geographic trajectory view if packaged road assets are not ready.

### Screen B: Replay workspace

```text
CONTINUUM STUDIO              Run: <held-out run>     Device: Laptop CPU
Model: <version>              GNSS: accepted / withheld / recovering

+------------------------------------------------+------------------------+
|                                                | SDK state              |
|    Main map / local trajectory view             | Mode: ...              |
|                                                | Estimated speed: ...   |
|    blue: SDK estimate                           | Last accepted GNSS: ...|
|    gray: reference, evaluator only              | Uncertainty: ...       |
|    dashed orange: last-speed baseline           | Alignment: ...         |
|    red marker: GNSS-only hold                   | Map: off / matched / ? |
|                                                +------------------------+
|    uncertainty ellipse                         | Replay evaluation      |
|                                                | Error to reference: ...|
|                                                | Outage distance: ...   |
|                                                | Endpoint drift: ...    |
+------------------------------------------------+------------------------+
| [Play/Pause] [1x/2x] [Simulate GNSS outage] [Restore GNSS] [Reset]         |
| Timeline: warm-up | GNSS withheld | recovery                            |
| Speed and position-error plots; GNSS acceptance/rejection events        |
+------------------------------------------------------------------------+
```

Use labels as well as colors. Make the moving estimate the strongest visual element; keep debugging details in a collapsible panel. Preserve map scale during the blackout so zoom changes do not hide drift.

The evaluator-only reference can be shown for comparison but must not enter the SDK. A persistent label explains that separation. The true-error panel disappears for live recordings without an independent reference; estimated uncertainty remains.

The outage control suppresses every GNSS channel at the adapter boundary, including speed and course. The event log shows the last delivered fix and continuing IMU counts. The button does not merely hide a map layer.

Seeking or resetting replay rebuilds estimator state by replaying earlier events or restoring an explicitly versioned checkpoint. Dragging the timeline must not initialize the engine from the hidden reference at the seek position.

### Screen C: Results

Show the actual trajectory plot, error-versus-time plot, and comparison table for the displayed experiment. Include aggregate results over the full frozen test schedule, the number of parent journeys, the number of outages, excluded windows, and failures.

Columns: method, endpoint error, maximum outage error, drift percentage, pass/fail against the declared target, and runtime. Use `Not measured` rather than a made-up number until results exist.

Buttons export a results bundle and open the model card. These exports must contain the same experiment ID shown in the video.

### Screen D: SDK integration

Show the short API example from [the SDK specification](04_SDK_SPECIFICATION.md) beside an actual terminal running a headless client. The terminal prints time, mode, speed, position, and uncertainty, then writes a trajectory file matching Studio's output.

This screen answers “Is it an SDK or only a dashboard?” The answer is visible: two clients share one package and produce the same result. A second replay adapter can demonstrate the event contract, but it must not be described as validation on an external sensor unless actual external data were used.

## Demo scenarios

| Scenario | Purpose | Required evidence |
| --- | --- | --- |
| Normal aided segment | Establish the last accepted state and show the model running | Accepted GNSS and active IMU counters |
| Saved 30–60 s outage | Show the main dead-reckoning behavior | GNSS withholding log and reference error trace |
| Turn during outage | Show heading estimation when the selected run supports it | Unconstrained estimated path against reference |
| GNSS restoration | Show consistency checks and return to aided tracking | First returned/accepted fix markers and correction trace |
| Headless replay | Demonstrate SDK reusability | Matching trajectory output from another client |
| Bad-fix injection, after P1 | Show a specific GNSS-quality response | Injected offset, rejection decision, clean-fix false-rejection report |
| Mount movement or landmark, after validation | Demonstrate a measured extension | Independent annotation, detection and recovery metrics |

Choose the primary video run after defining a representative-selection rule. Freeze it with the experiment manifest. A poor result is still a valid development finding; it must not be replaced with a reference-following animation.

## Three-minute storyboard

| Time | On screen | Suggested narration |
| --- | --- | --- |
| 0:00–0:15 | Title, tunnel/underpass illustration, SDK input/output graphic | “When satellite fixes disappear, applications need another way to estimate vehicle motion.” |
| 0:15–0:35 | Studio setup: dataset, held-out run, model, Laptop CPU | “Continuum is a reusable navigation engine. This prototype runs a trained model on held-out IO-VNBD phone measurements.” |
| 0:35–0:55 | Normal replay; IMU/GNSS counters | “The engine estimates the state continuously while accepting GNSS fixes.” |
| 0:55–1:30 | Press Simulate GNSS outage; marker, uncertainty, measured error | “GNSS inputs, including speed and course, are now withheld. IMU processing continues. The gray route is available only to the evaluator.” |
| 1:30–1:50 | Restore GNSS and show recovery markers | “Returning fixes are checked before correction. The estimator continues without a restart.” |
| 1:50–2:15 | Actual plot and aggregate benchmark table | “These are the measured results on the frozen test set, including failures and the comparison with simple baselines.” |
| 2:15–2:40 | SDK integration screen and running terminal | “This second client uses the same sensor API and engine. The dashboard is one integration of the SDK.” |
| 2:40–3:00 | Delivered artifacts and next-release diagram | “The prototype includes the model, engine, evaluation tools and results. Next we embed it on Android and validate local-road and external-sensor profiles.” |

If a 60-second outage is shown at 2x speed, keep the playback-speed and elapsed-outage indicators visible. Do not present accelerated playback as latency measurement.

## Screenshots for the proposal

Capture one architecture diagram, one setup view proving the run/model identity, one mid-outage map with uncertainty and evaluation labels, one reference-versus-predicted trajectory, one baseline table, and one SDK integration view. Prefer readable evidence over many tiny charts.

The model and generated plots must accompany the proposal as required by the supplied statement. A video of a marker alone does not satisfy that requirement.

## Phone and offline demonstration choices

A phone-to-laptop stream is an optional bridge after replay works. Display `Sensors: phone; inference: laptop`. Browser motion access has secure-context and permission requirements and device-dependent behavior, so it is not a reliable substitute for the final native sensor adapter. [W3C Device Orientation and Motion](https://www.w3.org/TR/orientation-event/)

For the final on-device demonstration, run the model and estimator in the Android process and disconnect the laptop. Show measured device latency. GNSS masking in the app remains a software experiment, not proof of actual tunnel accuracy.

Package local application assets and a legitimately obtained regional map pack for an offline claim. Standard OpenStreetMap public raster tiles are not an offline bulk-download source; use permitted extracts/self-produced or appropriately licensed assets. [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/)

## Recording checklist

- The model file exists, loads, and is identified by hash/version.
- The displayed run is not in training; pairing and units are reviewed.
- The SDK cannot access withheld GNSS or the evaluator's reference.
- Studio and the headless client produce matching results.
- Every displayed metric comes from the saved experiment.
- The reference is called a reference, with its accuracy limitations documented.
- The GNSS-only hold marker is described as a simple baseline, not a reconstruction of a commercial app.
- Map display and active map constraints are distinguished.
- Execution device and playback rate are visible.
- The video shows actual recovery, aggregate results, and at least one limitation.
- A saved replay and local assets are available for a repeatable presentation.

## Claims to use

Use: “We built a preliminary SDK that estimates continuous motion through simulated GNSS outages on held-out IO-VNBD data; this experiment measures its drift.”

Use only after evidence exists: “On this named test schedule, this proportion of outages met the 10% threshold,” and “On this named phone, the measured output rate and latency were these values.”

Do not substitute “lane-level everywhere,” “works on all phones,” “zero drift,” “spoof-proof,” or “200 Hz accurate positioning” for those measured statements.
