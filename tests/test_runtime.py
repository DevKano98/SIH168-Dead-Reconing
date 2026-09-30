from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from continuum_idr.data import PairedRunData, RunPair
from continuum_idr.model import MotionPrediction
from continuum_idr.runtime import RuntimeSession
from continuum_idr.studio import create_app


class MotionModel:
    sample_rate_hz = 10.0
    window_samples = 20
    model_id = "test-motion"

    def predict(self, window):
        return MotionPrediction(10.0, 0.5, 0.0)


def recording(count=250):
    t = np.arange(count) / 10
    gravity = np.tile([0, 0, 9.80665], (count, 1))
    return PairedRunData(
        RunPair("test", "E", Path("phone"), Path("vehicle"), count, count),
        t, gravity.copy(), gravity, np.zeros((count, 3)),
        np.full(count, 52.4), -1.5 + t * 0.0001,
        np.full(count, 10.0), np.full(count, 90.0), np.full(count, 3.0),
        np.full(count, 52.4), np.full(count, -1.5), np.full(count, 10.0), np.full(count, 90.0))


def test_disable_withholds_real_inputs_and_restores(monkeypatch):
    session = RuntimeSession(recording(), MotionModel(), 0, 249)
    accepted_calls = []
    original = session.engine.on_gnss
    monkeypatch.setattr(session.engine, "on_gnss", lambda fix: (accepted_calls.append(fix), original(fix))[1])
    first = session.snapshot()
    session.control("gnss", False)
    session.control("step", 100)
    outage = session.control("step", 50)
    assert accepted_calls == []
    assert outage["counters"]["gnss_delivered"] == first["counters"]["gnss_delivered"]
    assert outage["counters"]["gnss_withheld"] == 150
    assert outage["counters"]["imu_processed"] == first["counters"]["imu_processed"] + 150
    assert outage["current"]["state"]["tracking_mode"] == "DEAD_RECKONING"
    assert outage["current"]["east_m"] != first["current"]["east_m"]
    session.control("gnss", True)
    restored = session.control("step", 2)
    assert len(accepted_calls) == 2
    assert restored["current"]["gnss_delivered"] is True
    assert restored["counters"]["gnss_withheld"] == 150
    reset = session.control("restart")
    assert reset["session_id"] != first["session_id"]
    assert reset["index"] == 0 and reset["gnss_enabled"] and not reset["playing"]
    assert reset["current"] == first["current"]


def test_withheld_reference_changes_do_not_change_inference():
    original = recording()
    altered = deepcopy(original)
    altered.phone_lat[1:] += 1
    altered.phone_speed_raw[1:] = 55
    altered.phone_course_deg[1:] = 270
    a = RuntimeSession(original, MotionModel(), 0, 249)
    b = RuntimeSession(altered, MotionModel(), 0, 249)
    for session in (a, b):
        session.control("gnss", False)
        session.control("step", 100)
    assert a.snapshot()["current"]["state"] == b.snapshot()["current"]["state"]
    assert a.snapshot()["current"]["error_m"] != b.snapshot()["current"]["error_m"]


def test_clock_uses_recorded_timestamps_pause_rate_and_completion():
    now = [0.0]
    run = recording(6)
    run.time_s = np.array([0., 0.1, 0.4, 0.8, 1.0, 1.5])
    session = RuntimeSession(run, MotionModel(), 0, 5, clock=lambda: now[0])
    session.control("play")
    now[0] = 0.3
    assert session.snapshot()["index"] == 1
    session.control("pause")
    now[0] = 100
    assert session.snapshot()["index"] == 1
    session.control("rate", 2)
    session.control("play")
    now[0] += 0.2
    assert session.snapshot()["index"] == 2
    now[0] += 1
    final = session.snapshot()
    assert final["completed"] and not final["playing"]
    assert len(final["samples"]) == 6
    with pytest.raises(ValueError, match="completed"):
        session.control("play")


def test_restoring_does_not_replay_suppressed_fixes():
    run = recording(30)
    run.phone_lon = np.repeat(run.phone_lon[::10], 10)
    session = RuntimeSession(run, MotionModel(), 0, 29)
    session.control("gnss", False)
    session.control("step", 12)
    session.control("gnss", True)
    assert not session.control("step", 1)["current"]["gnss_delivered"]
    assert session.control("step", 7)["current"]["gnss_delivered"]
    assert session.snapshot()["counters"]["gnss_delivered"] == 2


@pytest.mark.parametrize("action,value", [("seek", 10), ("gnss", "false"), ("gnss", 0),
    ("rate", True), ("rate", []), ("step", 0), ("step", 101), ("step", 1.5)])
def test_invalid_controls_do_not_mutate(action, value):
    session = RuntimeSession(recording(), MotionModel(), 0, 249)
    before = session.snapshot()
    with pytest.raises(ValueError):
        session.control(action, value)
    assert session.snapshot() == before


def test_runtime_real_artifacts_and_export():
    client = TestClient(create_app(Path("artifacts/evaluation")))
    initial_response = client.get("/api/runtime")
    assert initial_response.status_code == 200, initial_response.text
    initial = initial_response.json()
    assert initial["execution"] == "interactive_sdk"
    assert len(initial["samples"]) == 1
    assert initial["warmup_samples"] > 0
    assert client.post("/api/runtime/control", json={"action": "gnss", "value": False}).status_code == 200
    outage = client.post("/api/runtime/control", json={"action": "step", "value": 100}).json()
    assert outage["counters"]["gnss_withheld"] > 0
    assert outage["counters"]["gnss_delivered"] == initial["counters"]["gnss_delivered"]
    assert outage["current"]["state"] != initial["current"]["state"]
    export = client.get("/api/runtime/export")
    assert "attachment" in export.headers["content-disposition"]
    assert export.json() == outage
    assert client.post("/api/runtime/control", json={"action": "seek", "value": 10}).status_code == 400
    assert client.post("/api/runtime/control", json={"action": []}).status_code == 400
    assert client.get("/api/health").json()["runtime_status"] == "initialized"
    # Same raw interval with GPS enabled must not reproduce the disabled output.
    client.post("/api/runtime/control", json={"action": "restart"})
    aided = client.post("/api/runtime/control", json={"action": "step", "value": 100}).json()
    assert aided["counters"]["gnss_withheld"] == 0
    assert aided["current"]["state"] != outage["current"]["state"]
    # Run to completion to exercise real output serialization across the interval.
    while not aided["completed"]:
        response = client.post("/api/runtime/control", json={"action": "step", "value": 100})
        assert response.status_code == 200, response.text
        aided = response.json()
    assert len(aided["samples"]) == aided["sample_count"]
    assert all(b["time_s"] > a["time_s"] for a, b in zip(aided["samples"], aided["samples"][1:]))


def test_missing_runtime_dependencies_return_actionable_error(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/api/runtime")
    assert response.status_code == 503
    assert "SDK runtime unavailable" in response.json()["detail"]
