from pathlib import Path
from fastapi.testclient import TestClient

from continuum_idr.studio import create_app


def test_studio_endpoints_with_artifacts():
    artifacts_dir = Path("artifacts/evaluation")
    app = create_app(artifacts_dir)
    client = TestClient(app)

    # 1. Test index page
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Continuum Studio" in res_index.text

    # 2. Test /api/summary
    res_summary = client.get("/api/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert "total_outages_evaluated" in summary_data
    assert "by_distance" in summary_data

    # 3. Test /api/demo
    res_demo = client.get("/api/demo")
    assert res_demo.status_code == 200
    demo_data = res_demo.json()
    assert "outage" in demo_data
    assert "samples" in demo_data
    assert len(demo_data["samples"]) > 0


def test_studio_missing_artifacts_returns_404(tmp_path):
    empty_dir = tmp_path / "empty_artifacts"
    empty_dir.mkdir()
    app = create_app(empty_dir)
    client = TestClient(app)

    res_demo = client.get("/api/demo")
    assert res_demo.status_code == 404
    assert "Run `idr evaluate`" in res_demo.json()["detail"]

    res_summary = client.get("/api/summary")
    assert res_summary.status_code == 404
    assert "Run `idr evaluate`" in res_summary.json()["detail"]
