from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


@dataclass
class ReplaySession:
    """In-memory replay clock shared by Studio and the driver view."""

    sample_count: int = 0
    index: int = 0
    playing: bool = False
    rate: float = 1.0
    updated_at: float = 0.0

    def __post_init__(self) -> None:
        self.updated_at = time.monotonic()
        self._lock = threading.Lock()

    def _advance(self) -> None:
        now = time.monotonic()
        if self.playing and self.sample_count > 0:
            # Evaluation replays are recorded at 10 Hz.
            elapsed_samples = int((now - self.updated_at) * 10.0 * self.rate)
            if elapsed_samples:
                self.index = min(self.sample_count - 1, self.index + elapsed_samples)
                self.updated_at += elapsed_samples / (10.0 * self.rate)
                if self.index >= self.sample_count - 1:
                    self.playing = False
        else:
            self.updated_at = now

    def _snapshot_unlocked(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "playing": self.playing,
            "rate": self.rate,
            "sample_count": self.sample_count,
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._advance()
            return self._snapshot_unlocked()

    def control(self, action: str, value: float | int | None = None) -> dict[str, Any]:
        with self._lock:
            self._advance()
            if action == "play":
                if self.index >= max(0, self.sample_count - 1):
                    self.index = 0
                self.playing = True
            elif action == "pause":
                self.playing = False
            elif action == "restart":
                self.index = 0
                self.playing = False
            elif action == "seek":
                if value is None:
                    raise ValueError("seek requires an index")
                self.index = max(0, min(self.sample_count - 1, int(value)))
            elif action == "rate":
                if value is None or float(value) not in {0.5, 1.0, 2.0, 4.0}:
                    raise ValueError("rate must be 0.5, 1, 2, or 4")
                self.rate = float(value)
            else:
                raise ValueError(f"unknown replay action: {action}")
            self.updated_at = time.monotonic()
            return self._snapshot_unlocked()


def _read_json(path: Path, missing_message: str) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(404, missing_message)
    return json.loads(path.read_text(encoding="utf-8"))


def create_app(artifacts: Path, dataset: Path = Path("."),
               model: Path = Path("models/motion_p0")) -> FastAPI:
    static = Path(__file__).parent / "studio_static"
    demo_path = artifacts / "demo_replay.json"
    sample_count = 0
    if demo_path.exists():
        try:
            sample_count = len(json.loads(demo_path.read_text(encoding="utf-8")).get("samples", []))
        except (OSError, json.JSONDecodeError):
            sample_count = 0

    session = ReplaySession(sample_count=sample_count)
    runtime = None
    runtime_lock = threading.Lock()

    def get_runtime():
        nonlocal runtime
        with runtime_lock:
            if runtime is None:
                from .runtime import load_runtime
                try:
                    recording = json.loads(demo_path.read_text(encoding="utf-8"))
                    runtime = load_runtime(dataset, model, recording)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise HTTPException(503, f"SDK runtime unavailable: {exc}") from exc
            return runtime
    app = FastAPI(
        title="Continuum Studio",
        version="0.3.0",
        docs_url=None,
        redoc_url=None,
    )
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/mobile")
    def mobile():
        return FileResponse(static / "mobile.html")

    @app.get("/docs")
    def docs_portal():
        return FileResponse(static / "docs.html")

    @app.get("/api/demo")
    def demo():
        return JSONResponse(
            content=_read_json(demo_path, "Run `idr evaluate` before opening Studio")
        )

    @app.get("/api/summary")
    def summary():
        return JSONResponse(
            content=_read_json(
                artifacts / "summary.json",
                "Run `idr evaluate` before opening Studio",
            )
        )

    @app.get("/api/session")
    def get_session():
        return session.snapshot()

    # /api/session remains the legacy saved-trace player for the existing UI.
    # The new frontend must use /api/runtime exclusively for interactive output.
    @app.get("/api/runtime")
    def runtime_snapshot():
        return JSONResponse(get_runtime().snapshot(), headers={"Cache-Control": "no-store"})

    @app.post("/api/runtime/control")
    def runtime_control(payload: dict[str, Any] = Body(...)):
        try:
            return JSONResponse(
                get_runtime().control(payload.get("action"), payload.get("value")),
                headers={"Cache-Control": "no-store"},
            )
        except (ValueError, TypeError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/runtime/export")
    def runtime_export():
        return JSONResponse(get_runtime().snapshot(), headers={
            "Content-Disposition": 'attachment; filename="continuum-session.json"',
            "Cache-Control": "no-store",
        })

    @app.post("/api/session/control")
    def control_session(payload: dict[str, Any] = Body(...)):
        try:
            return session.control(str(payload.get("action", "")), payload.get("value"))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/health")
    def health():
        return {
            "status": "ready" if sample_count else "missing_artifacts",
            "replay_samples": sample_count,
            "artifacts": str(artifacts),
            "runtime_status": "initialized" if runtime is not None else "not_initialized",
            "legacy_ui": True,
        }

    return app


def run(artifacts: Path, host: str, port: int, dataset: Path = Path("."),
        model: Path = Path("models/motion_p0")) -> None:
    uvicorn.run(create_app(artifacts, dataset, model), host=host, port=port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve Continuum Studio")
    parser.add_argument("--artifacts", default="artifacts/evaluation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dataset", default=".")
    parser.add_argument("--model", default="models/motion_p0")
    args = parser.parse_args(argv)
    run(Path(args.artifacts), args.host, args.port, Path(args.dataset), Path(args.model))
    return 0
