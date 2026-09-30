# Interactive SDK runtime API (Studio 0.3)

This API runs `IDREngine` on raw recorded IO-VNBD sensor measurements. It does not
read saved prediction states. The Continuum Studio frontend (`index.html`, `app.js`,
`mobile.html`, `mobile.js`) is connected to `/api/runtime` and `/api/runtime/control`
for interactive session control and driver telemetry streaming. Live on-device phone
sensing is implemented separately in the Android application (`android/`).

## Start

```powershell
python -m continuum_idr.cli studio --dataset . --model models/motion_p0 --artifacts artifacts/evaluation --port 8000
```

Restart an already running server to load new backend code. Run a single process
on localhost: this is a shared local experiment without authentication, durable
storage, or cross-worker synchronization. Do not expose it publicly.

The raw dataset and trusted local model bundle must be present. The representative
run and interval are selected from `demo_replay.json` metadata, not its saved
outputs. Only held-out model runs are accepted. This version supports one selected
interval, manual GPS control, and no seek or run-selection endpoint.

## Endpoints

| Request | Meaning |
| --- | --- |
| GET `/api/runtime` | Initialize if necessary, advance due samples, return snapshot |
| POST `/api/runtime/control` | Apply a control and return snapshot |
| GET `/api/runtime/export` | Advance due samples and download snapshot JSON |
| GET `/api/summary` | Historical benchmark, unrelated to current manual controls |
| GET `/api/session`, `/api/demo` | Legacy saved-trace UI only; not runtime output |

Control body is `{ "action": "...", "value": ... }`:

| Action | Value | Effect |
| --- | --- | --- |
| play | omitted | Resume processing; completed sessions require restart |
| pause | omitted | Pause after catching up a bounded batch |
| restart | omitted | Fresh engine/warm-up, paused, GPS on, 1x, new session ID |
| gnss | JSON boolean | Deliver or withhold subsequent newly recorded fixes |
| rate | 0.5, 1, 2, 4 | Source-time playback multiplier |
| step | integer 1–100 | Process next samples while paused; clamp at end |

Invalid actions/values return HTTP 400 with `detail`. Missing or invalid runtime
dependencies return 503 with `detail`; initialization may be retried after repair.
Malformed JSON/body types are rejected by FastAPI. There is no silent replay fallback.

## Snapshot

- `session_id` changes on restart; `revision` increases for processing and controls.
- `execution` is `interactive_sdk`; `input_source` is `recorded_iovnbd_sensors`.
- `run_id`, `model_id`, `config` identify the actual run, loaded model and engine settings.
- `playing`, `rate`, `gnss_enabled`, `completed` are current controls/session status.
- `index` is zero-based within captured history; `sample_count` is the full interval size.
- `duration_s` is total source-time duration. `current.elapsed_s` is processed elapsed time.
- `warmup_samples` is the number processed before capture; `counters` include warm-up.
- `counters.imu_processed`, `gnss_delivered`, `gnss_withheld` count actual input events.
- `current` is the most recent row; `samples` contains only freshly computed captured history.
- Rows include source index/time, elapsed time, GPS enable/availability/delivery/withholding,
  SDK `state.to_dict()`, common-frame `east_m`/`north_m`, reference coordinates and `error_m`.
- SDK state includes tracking mode, position, speed in m/s, heading degrees clockwise
  from north, uncertainty in metres, last GNSS age/decision, alignment and health flags.
- `metrics.current_error_m` and `max_error_m` cover captured history only, not a scored
  benchmark outage. No current-session baseline or drift pass/fail is calculated.
- `events` records action, `after_source_index`, source timestamp, resulting GPS switch/rate.
  A control takes effect after that source index. History rows are not rewritten on toggles.
- `reference_note` states the scoring limitation. Coordinates can be null before initialization.

The row-level estimate and reference coordinates share a local origin. Nested SDK
state coordinates use the engine's own origin; do not mix these two frames.

## Timing and GPS semantics

GET/control requests advance at most 100 samples toward the recorded timestamp
corresponding to elapsed monotonic wall time and playback rate. All IMU samples
are processed in order. Several polls may be required after a long absence; the
reported index is actual progress, never a pretend wall-clock position. Controls
re-anchor at the processed source time; paused wall time is discarded. There is no
autonomous worker when no requests arrive. Poll serially and serialize controls
with polling to prevent stale client responses.

GPS is on initially; the historical outage is not applied automatically. Off blocks
`on_gnss` calls while `on_imu` continues. On admits only future newly recorded fixes,
not withheld backlog. Availability follows changed phone coordinates, as in the
evaluator. Sparse fixes justify the 12-second timeout. A restored fix may be rejected
by the SDK; delivery does not imply acceptance or instant recovery.

Reference coordinates are interpolated from phone GNSS, including future fixes,
for offline scoring only. They are never passed to the estimator. This is not
survey ground truth. The model and measured accuracy are unchanged by this feature.

## Headless smoke test

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/runtime
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/control -Method Post -ContentType application/json -Body '{"action":"gnss","value":false}'
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/control -Method Post -ContentType application/json -Body '{"action":"step","value":100}'
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/control -Method Post -ContentType application/json -Body '{"action":"gnss","value":true}'
Invoke-RestMethod http://127.0.0.1:8000/api/runtime/control -Method Post -ContentType application/json -Body '{"action":"step","value":100}'
```

Pause before exporting if a stable snapshot is desired. Export is a download; it
does not overwrite evaluation artifacts. Restart clears the previous session in
memory, so export first if it must be retained.
