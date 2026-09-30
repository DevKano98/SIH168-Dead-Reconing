# Antigravity handoff: Continuum Studio

Build a professional, production-quality frontend for the existing Continuum IDR research SDK. Work in this repository. The backend is implemented; connect to it, do not simulate estimator output. Preserve unrelated work. Read `CURRENT_STATUS.md`, `docs/RUNTIME_API.md`, and the actual backend contracts first.

## Product and evidence boundary

Continuum estimates vehicle motion when GPS is unavailable. This demonstration streams recorded IO-VNBD IMU/GNSS measurements through a running Python SDK. Every interactive navigation state is computed during the session. This is NOT live phone sensing and NOT validated GPS-free navigation. Accuracy currently misses the target; present that honestly.

The existing frontend in `continuum_idr/studio_static/` is a legacy saved-trace player. Replace its interaction logic and improve its design. `/api/session` and `/api/demo` are legacy endpoints, not interactive output. Never use them for the new live experiment. Do not change the estimator, trained models, raw dataset, evaluation artifacts, or backend API without first explaining a concrete blocker.

## Visual direction

Design a serious navigation/developer-tool product: restrained, readable, precise. Use a coherent neutral palette with one blue accent; amber only for GPS withholding/warnings and green only for genuinely healthy states. Strong typography, generous spacing, clear information hierarchy, polished responsive layouts. Avoid neon gradients, glass effects everywhere, oversized decorative statistics, emoji icons, tiny labels, and an overloaded dashboard. Use consistent SVG icons and accessible focus states. No fake testimonials, performance claims, satellite counts, battery values, or fabricated maps.

Use the existing FastAPI static serving setup unless there is a clear benefit to a frontend framework. If introducing a build, include pinned dependencies, documented commands, and serve the built app from the existing server. No paid API key should be necessary to run the demo locally.

## Screens

1. **Studio `/`**: prominent trajectory workspace, compact session controls, clear navigation-state inspector, input/output provenance, and a collapsible session event log. Primary workflow: Start → Disable GPS → observe newly estimated motion → Restore GPS → Pause/review/export. Show current error and uncertainty as different quantities. Display source run/model, processed IMU count, delivered/withheld GPS counts, elapsed source time, rate, and completion. Keep backend connection status separate from GPS input status and engine tracking mode.
2. **Driver `/mobile`**: polished mobile-first readout synchronized to the SAME runtime session. Estimated speed, heading, mode, uncertainty, and GPS input status; clearly labelled recorded-sensor demo. Never invent turns or navigation instructions. It may expose shared controls, but explain that they affect Studio too.
3. **Evidence**: a separate tab/section for the saved benchmark fetched from `/api/summary`. Label it historical evaluation, NOT the current manual experiment. Present current failures and methodological limits without hiding them. No comparison baseline exists for the interactive session: don't fabricate one.
4. **Developer docs `/docs`**: professional SDK portal with sidebar, search, code copying, architecture diagrams, quickstart, units/timing, actual API contracts, integration flow, and limitations. Distinguish the Python SDK, local experiment HTTP API, and unverified Android integration source. Verify Python examples against actual signatures. Link `docs/RUNTIME_API.md` content in the portal. No claims of a published certified SDK.

## Exact backend integration

Run from repository root:

```powershell
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --dataset . --model models/motion_p0 --host 127.0.0.1 --port 8000
```

- `GET /api/runtime`: lazily initializes the SDK session and returns its snapshot. The first request may take a few seconds. Initially paused, GPS enabled, with one captured state following causal warm-up.
- `POST /api/runtime/control`: JSON `{ "action": "play" }`, `pause`, or `restart`; `{ "action": "gnss", "value": false }` disables GPS, true restores; `{ "action": "rate", "value": 2 }` accepts 0.5/1/2/4; `{ "action": "step", "value": 100 }` processes 1–100 next samples while paused. Every success returns a full snapshot.
- `GET /api/runtime/export`: download the actual session JSON. Pause first if the user wants a final stationary snapshot.
- `GET /api/summary`: historical benchmark only.
- `GET /api/health`: service/legacy artifact information; `status: ready` alone does NOT certify runtime initialization. A successful `/api/runtime` request is authoritative.
- `/openapi.json`: machine-readable routes (the control payload is a generic dictionary; follow the detailed contract in `docs/RUNTIME_API.md`).

Important snapshot fields:

```text
session_id, revision, execution="interactive_sdk",
input_source="recorded_iovnbd_sensors", run_id, model_id,
playing, rate, gnss_enabled, completed, index, sample_count,
duration_s, warmup_samples, counters, config, current, metrics,
samples[], events[], reference_note
```

`current` and each `samples[]` row contain:

```text
index, source_index, time_s, elapsed_s,
gnss_enabled, gnss_available, gnss_delivered, gnss_withheld,
east_m, north_m, reference_east_m, reference_north_m, error_m,
state { timestamp_s, sequence, tracking_mode, east_m, north_m,
        latitude_deg, longitude_deg, speed_mps, heading_deg,
        horizontal_uncertainty_m, last_accepted_gnss_age_s,
        alignment_status, health_flags[], last_gnss_decision, ... }
```

Use the row-level east/north coordinates for comparing estimate and reference; the nested SDK state has its own local coordinate origin. Plot only processed history; no future predictions. GPS `gnss_enabled` is the current switch setting, whereas `current.gnss_enabled` describes the last processed sample. They can differ immediately after toggling while paused.

## Correct interaction requirements

- Poll serially at roughly 200–300 ms, scheduling the next request after the previous completes. Do not overlap poll/control requests in a client; serialize controls, suspend polling during commands, and show pending states. Polling drives bounded processing batches using recorded timestamps. There is no WebSocket and no independent background worker. Catch-up can take several polls.
- On initial loading, 400/503/network errors, show a useful message and retry affordance. Never fall back silently to saved traces, invented telemetry, or a local animation clock. A disconnected badge must remain visible until a successful request. Disable unavailable controls.
- One shared in-memory session exists per server process. Both pages see the same experiment; there are no per-user sessions or persistence. Restart resets history, event log, rate, GPS switch, and session ID. Refreshing a browser does not restart it.
- No seeking is supported. Use a read-only progress bar, pause, bounded step-forward, and restart. Do not wire old jump-to-outage/recovery buttons. There is no automatic scheduled outage: the GPS switch is manual. Disable Play at completion until Restart.
- Disabling GPS blocks subsequent fixes, not IMU. It does not rewrite the last state or instantly change the SDK mode. The dataset has sparse fixes and a 12-second timeout. Restoring GPS only admits future newly recorded fixes, and the estimator can reject them. Do not imply immediate successful recovery or bypass gating.
- Never map null values to zero: `Number(null)` is not a valid telemetry conversion. Show unavailable values as an em dash.
- The trajectory is a **local metric plot, not a geographic street map**. Label it clearly. Do not draw the evaluation route as a fake road. Fit/center both processed estimate and reference; support pan/zoom if useful, respect layer toggles, keep the vehicle visible, use a scale bar and honest uncertainty visualization. If uncertainty is visually capped, disclose the cap; the numeric uncertainty remains authoritative.
- Reference is interpolated phone GNSS for offline scoring, not survey ground truth. It is not an estimator input while GPS is disabled. Speed is m/s in the API, display km/h with ×3.6; heading is degrees clockwise from north. Differentiate GPS delivery from acceptance.
- No run-selection control unless supported by the backend; this version uses one representative held-out recording selected by the saved artifact's scenario metadata.
- Protect rendered strings: use textContent or framework escaping, not unsanitized innerHTML.

## Acceptance checklist

Verify against the real running server, not mocks alone:

1. Start: source time, IMU count, and newly computed states advance.
2. Disable GPS: IMU count continues, delivered count stops, withheld count rises only when a new fix occurs. Eventually SDK may enter DEAD_RECKONING.
3. Restore: delivered count resumes at a future recorded fix; acceptance/recovery follows the actual state.
4. Pause: no advancing source time. Step: real backend processing. Restart: new session ID, reset controls/history.
5. Studio and Driver show the same source index and state after polling settles.
6. Export contains the current session's states, settings, counters, and control events.
7. Saved benchmark remains distinct from current manual-session metrics.
8. Verify no-network/missing-data/error states, keyboard controls, readable contrast, reduced motion, and layouts at 390 px, 768 px, and 1440 px.
9. Run existing backend tests and frontend checks. Deliver a brief file/change summary, launch instructions, screenshots, and any remaining limitations. Do not claim visual or functional verification you did not perform.
