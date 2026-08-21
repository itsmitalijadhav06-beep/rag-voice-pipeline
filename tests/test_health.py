"""
Basic tests for base application setup and health check API.
"""

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_latency_endpoint():
    response = client.get("/analytics/latency")
    assert response.status_code == 200
    data = response.json()
    assert "p50_ms" in data
    assert "p70_ms" in data
    assert "p100_ms" in data
