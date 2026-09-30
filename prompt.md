# Antigravity Handoff Prompt: Finish the Continuum IDR SIH Prototype

You are taking over an existing Windows/Python project. Work directly in:

```text
D:\iovnbd\IO-VNBD
```

Your task is to **finish the working P0 prototype for an SIH proposal and prototype video**. Do not stop after reviewing the repository or writing a plan. Inspect the existing implementation, fix it, run it, generate current evidence, and leave the project in a state that the owner can demonstrate with a short command sequence.

## 1. Product objective

The project is **Continuum IDR**, an AI/ML assisted intelligent dead reckoning engine for vehicle navigation during GNSS outages.

The prototype must demonstrate this story:

1. A vehicle has valid GNSS and IMU input.
2. GNSS becomes unavailable in a simulated tunnel or urban canyon.
3. The engine continues estimating position from smartphone IMU and a learned motion model.
4. The interface shows tracking mode, estimated path, reference path, uncertainty, and measured drift.
5. GNSS returns and the estimate recovers smoothly.
6. The same core is exposed as a small SDK rather than being coupled to the UI.

The SIH benchmark is positional drift below 10% of distance travelled during a GNSS denied interval. Treat that as a target to measure honestly, not a result to invent.

## 2. Current implementation

The repository already contains:

- `continuum_idr/types.py`: typed IMU, GNSS, navigation state, and configuration objects.
- `continuum_idr/features.py`: causal 2 second IMU window features.
- `continuum_idr/model.py`: persisted motion model bundle and inference.
- `continuum_idr/engine.py`: planar EKF style SDK with GNSS gating, outage tracking, recovery, and uncertainty.
- `continuum_idr/data.py`: IO-VNBD synchronized pair discovery, audit, and loading.
- `continuum_idr/training.py`: scikit-learn speed and stopped-state training.
- `continuum_idr/evaluation.py`: masked GNSS outage construction, replay, baselines, metrics, and plot/artifact generation.
- `continuum_idr/cli.py`: `audit`, `train`, `evaluate`, `replay`, and `studio` commands.
- `continuum_idr/studio.py` and `continuum_idr/studio_static/`: local FastAPI demonstration interface.
- `tests/`: unit tests for coordinates, features, and the engine.
- `DATASET_CATALOG.md`: detailed dataset inventory and caveats.
- `PROJECT_DOCUMENTATION.md` and `docs/idr/`: product, architecture, SDK, data, evaluation, video, and roadmap documents.
- `models/motion_p0/`: a newly trained model bundle.
- `artifacts/audit/pairs.json`: dataset audit output.
- `artifacts/evaluation/`: evaluation output, but it is stale and must be regenerated.

The supported command sequence is intended to be:

```powershell
python -m pip install -e .
python -m continuum_idr.cli audit --dataset .
python -m continuum_idr.cli train --dataset . --output models/motion_p0
python -m continuum_idr.cli evaluate --dataset . --model models/motion_p0 --output artifacts/evaluation
python -m continuum_idr.cli replay --dataset . --model models/motion_p0
python -m continuum_idr.cli studio --artifacts artifacts/evaluation
```

## 3. Known authoritative state

The newest model manifest is already present and appears complete. Verify it before using it.

Current model split:

- Train: Driver A and Driver E runs except the complete `Vtb*` family.
- Validation: Driver B.
- Test: the complete held-out `Vtb*` family.
- Only equal-row synchronized smartphone/vehicle pairs are eligible.

Current model manifest metrics:

- Validation speed MAE: about `3.163 m/s`.
- Validation speed RMSE: about `4.173 m/s`.
- Held-out Vtb speed MAE: about `5.287 m/s`.
- Held-out Vtb speed RMSE: about `6.829 m/s`.
- Training windows: `34,037`.
- Validation windows: `10,596`.
- Test windows: `11,408`.

The files currently in `artifacts/evaluation/` are **stale**. Their summary says `iovnbd-driver-d-p0` and evaluates Driver D/Y1. Do not present those values. Regenerate all evaluation artifacts using the current manifest's held-out `Vtb*` runs.

Dataset audit previously found:

- 72 synchronized candidate pairs.
- 63 equal-length pairs.
- 9 unequal-length pairs.
- Driver distribution: A=6, B=1, D=1, E=64.

## 4. Important data findings

Preserve these decisions unless evidence from the files proves a better solution:

1. Equal row counts do not prove the phone and vehicle timestamps are aligned. Driver D/Y1 diverges badly by row index and its phone GNSS is sparse, so it is unsuitable as the formal P0 test reference.
2. Use the phone GNSS position as the time-aligned finite-accuracy reference for masked outage evaluation. It must be completely withheld from the engine during each simulated outage.
3. The phone GPS speed column is labelled as km/h in the raw file but observed values behave like m/s. Confirm units from data before changing conversions.
4. `S-A4.csv` has a semantic column shift after a blank column and should stay quarantined unless a robust schema-specific parser is added.
5. The phone mounted vehicle yaw signal in the current implementation uses the second gyroscope channel with negative sign. This was selected from validation evidence; verify against validation data, never by tuning on held-out Vtb results.
6. IO-VNBD smartphone IMU is only 10 Hz. Do not claim that it validates 50–200 Hz operation, motorcycles, Indian roads, phone-in-pocket use, or external FOG IMUs.

## 5. Non-negotiable evaluation rules

- Never train on the `Vtb*` test family.
- Never tune parameters by repeatedly inspecting and optimizing Vtb test scores.
- Any tuning must use training data or Driver B validation data.
- During an outage, suppress all GNSS fields from the engine. Reference GNSS may be used only after inference to score the estimate.
- Do not use future reference points, vehicle speed, or outage endpoint information as inference inputs.
- Report failures and limitations plainly.
- Keep baseline comparisons: frozen position and last-speed-plus-gyro, alongside Continuum IDR.
- Keep metrics per outage: duration, reference distance, entry error, endpoint error, maximum error, drift percentage, and below-10-percent result.
- Prefer several 50 m, 500 m, and 1 km windows when the run has enough valid reference distance.
- Long gaps or implausible jumps in phone GNSS must be detected and excluded or flagged. Do not allow a nominal 50 m window to span many minutes and then treat it as a realistic tunnel test.

## 6. Required work, in order

### Phase A: establish a trustworthy baseline

1. Inspect `models/motion_p0/manifest.json` and confirm all model files load.
2. Run `python -m pytest` and `python -m compileall continuum_idr`.
3. Run the audit command and compare it with the counts above.
4. Run the held-out evaluation with the current Vtb manifest.
5. Inspect every generated outage for:
   - plausible duration for its distance;
   - enough valid GNSS reference samples;
   - no coordinate-frame offset;
   - correct outage entry/recovery timing;
   - finite and physically plausible metrics.
6. Fix evaluator defects before considering model changes.

### Phase B: make the evaluation defensible

Review `continuum_idr/evaluation.py` closely. Add or fix:

- reference quality gates for maximum time gap, speed, and position jump;
- an explicit minimum number of valid reference fixes;
- a reasonable maximum outage duration based on distance;
- consistent local coordinate origins between engine output and reference;
- clear separation of warm-up, outage, and recovery periods;
- deterministic window selection;
- a reason field for skipped candidate windows;
- aggregation by distance bucket and by run;
- 50th and 95th percentile endpoint error and drift;
- below-10-percent pass rate;
- comparisons with both baselines.

Generate:

```text
artifacts/evaluation/summary.json
artifacts/evaluation/metrics_per_outage.csv
artifacts/evaluation/demo_replay.json
artifacts/evaluation/trajectory.png
artifacts/evaluation/error_vs_time.png
artifacts/evaluation/RESULTS.md
```

`RESULTS.md` must explain the split, number of runs/windows, metrics by distance, baseline comparison, test conditions, skipped-window reasons, and limitations. It must be generated from actual artifacts rather than manually invented values.

### Phase C: improve the core only if evidence warrants it

First diagnose error sources using train/validation data:

- speed bias by speed bin;
- stop/crawl classification errors;
- yaw sign/axis and unit errors;
- excessive uncertainty growth or overconfident covariance;
- GNSS gating behavior at acquisition and recovery;
- heading initialization and warm-up behavior;
- timestamp `dt` clipping and dropped rows.

Then implement the smallest justified improvements. Reasonable candidates include:

- validation-fitted speed calibration by speed bin;
- a causal smoothing filter on model speed;
- zero-velocity updates when the stopped classifier is confidently active;
- robust heading initialization from consecutive good GNSS fixes;
- gradual GNSS re-entry rather than an estimate jump;
- covariance inflation during outages;
- an explicit sensor quality indicator.

Do not add complexity merely to make the architecture sound impressive. Keep inference causal and test leakage free.

If the full system does not meet 10% on the held-out data, preserve the honest result and show where it improves over baselines. The prototype video can demonstrate function without claiming benchmark success.

### Phase D: finish Continuum Studio for the video

The Studio must use the newly generated artifacts and run fully offline at `http://127.0.0.1:8000`.

It should visibly provide:

- project title and a short one-sentence explanation;
- play, pause, restart, and timeline controls;
- a visible GNSS outage region or Kill GPS action;
- current mode: GNSS aided, dead reckoning, or recovering;
- live speed, elapsed outage time, travelled outage distance, uncertainty, and measured reference error;
- reference path, Continuum estimate, frozen baseline, and last-speed baseline with a legend;
- a growing uncertainty circle or band;
- obvious tunnel entry and GNSS recovery events;
- final endpoint error, drift percentage, baseline comparison, and pass/target status;
- a results panel sourced from `summary.json`;
- clear wording that the route is a recorded IO-VNBD replay with a simulated GNSS blackout.

Make the page readable at 1920×1080 screen recording resolution. Avoid online map dependencies. Use the existing local HTML, CSS, JavaScript, and FastAPI stack.

If multiple valid demo windows exist, choose a representative one using a documented rule. Do not cherry-pick the best result. A median-result 500 m window is a good default. Let the user select other generated outages if practical.

### Phase E: SDK and CLI completion

Ensure the public usage remains simple:

```python
engine = IDREngine(config, motion_model)
engine.on_gnss(fix)
engine.on_imu(sample)
state = engine.get_state()
```

Verify:

- inference does not depend on vehicle CAN or reference data;
- invalid/uninitialized state is explicit;
- timestamps must be monotonic or are safely rejected;
- a GNSS outage does not crash the engine;
- bad GNSS fixes are gated;
- good GNSS recovery converges smoothly;
- state contains position, speed, heading, uncertainty, mode, and quality information;
- CLI errors are actionable when artifacts/models are missing.

Add meaningful tests for evaluator quality gates, outage masking, leakage prevention, GNSS rejection, and recovery. Avoid tests that only mirror implementation lines.

### Phase F: documentation and operator workflow

Update `README.md` so a new user can:

1. verify Python and install the package;
2. audit the data;
3. train or reuse the supplied model;
4. evaluate it;
5. launch Studio;
6. record the demo;
7. understand what is implemented and what remains roadmap work.

Add a concise `PROJECT_STATUS.md` containing:

- implemented features;
- actual latest model and evaluation results;
- commands verified on this machine;
- known limitations;
- exact next steps for Android/on-device deployment and Indian-road data collection.

Keep existing detailed documents synchronized with the actual implementation. Remove statements that imply map matching, phone streaming, Android deployment, external IMU validation, or benchmark success if those features are still only planned.

## 7. Scope for this prototype

The required deliverable is a polished, reproducible desktop replay prototype and SDK evidence package suitable for the SIH proposal video.

The following are roadmap items unless they can be added without destabilizing the core:

- Android application;
- TensorFlow Lite export;
- browser sensor streaming from a physical phone;
- live OpenStreetMap download;
- HMM map matching;
- speed-breaker landmark learning;
- motorcycle/auto-rickshaw models;
- Indian-road field validation;
- external 200 Hz IMU validation.

Do not label a roadmap item as implemented.

## 8. Repository safety

- The workspace contains large original dataset files and extracted folders. Do not delete, move, rename, recompress, or rewrite them.
- Preserve user-authored documentation and dataset catalog work.
- The Git status may show many apparent deletions plus untracked copies because of the repository/index state. Do not use `git reset`, `git clean`, broad checkout, or mass deletion to “fix” it.
- Make focused source edits only.
- Do not commit generated model binaries or multi-megabyte replay artifacts unless the repository policy explicitly calls for it. They still need to exist locally for the demonstration.
- Never expose personal paths or secrets in generated public documentation beyond the local setup instructions.

## 9. Definition of done

The task is complete only when all of the following are true:

- `python -m pytest` passes.
- `python -m compileall continuum_idr` passes.
- Audit, train, evaluate, and replay commands complete successfully.
- Evaluation artifacts were regenerated after the current Vtb model and identify the current experiment, not Driver D/Y1.
- Evaluation windows pass reference-quality sanity checks.
- `RESULTS.md` contains real current results and limitations.
- Studio launches and its API/static files load without errors.
- The dashboard replays at least one valid outage end to end and displays recovery.
- The UI values agree with the underlying replay JSON and CSV.
- README commands were run as written.
- `PROJECT_STATUS.md` gives an accurate handoff.
- No claim exceeds the evidence.

## 10. Final response expected from you

After completing the work, report:

1. what you changed;
2. the exact verification commands and whether each passed;
3. the final model and held-out outage metrics;
4. the path to the generated results and Studio artifacts;
5. the one command to launch the demo;
6. remaining limitations and the next practical milestone.

Be autonomous. Resolve routine implementation choices yourself. Ask the owner only if a required external dependency, missing data, or irreversible action blocks progress.
