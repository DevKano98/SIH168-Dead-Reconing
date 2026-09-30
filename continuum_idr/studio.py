from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


def create_app(artifacts: Path) -> FastAPI:
    static = Path(__file__).parent / "studio_static"
    app = FastAPI(title="Continuum Studio", version="0.1.0")
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/mobile")
    def mobile():
        return FileResponse(static / "mobile.html")

    @app.get("/api/demo")
    def demo():
        path = artifacts / "demo_replay.json"
        if not path.exists():
            raise HTTPException(404, "Run `idr evaluate` before opening Studio")
        return JSONResponse(content=__import__("json").loads(path.read_text(encoding="utf-8")))

    @app.get("/api/summary")
    def summary():
        path = artifacts / "summary.json"
        if not path.exists():
            raise HTTPException(404, "Run `idr evaluate` before opening Studio")
        return JSONResponse(content=__import__("json").loads(path.read_text(encoding="utf-8")))

    return app


def run(artifacts: Path, host: str, port: int) -> None:
    uvicorn.run(create_app(artifacts), host=host, port=port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve Continuum Studio")
    parser.add_argument("--artifacts", default="artifacts/evaluation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    run(Path(args.artifacts), args.host, args.port)
    return 0
