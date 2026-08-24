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


def test_deployed_frontend_origin_is_allowed():
    # Test OPTIONS preflight request for /health
    headers_health = {
        "Origin": "https://rag-voice-pipeline-mpkl.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    response_health = client.options("/health", headers=headers_health)
    assert response_health.status_code == 200
    assert response_health.headers.get("access-control-allow-origin") == "https://rag-voice-pipeline-mpkl.vercel.app"
    assert "GET" in response_health.headers.get("access-control-allow-methods", "")

    # Test OPTIONS preflight request for /query
    headers_query = {
        "Origin": "https://rag-voice-pipeline-mpkl.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response_query = client.options("/query", headers=headers_query)
    assert response_query.status_code == 200
    assert response_query.headers.get("access-control-allow-origin") == "https://rag-voice-pipeline-mpkl.vercel.app"
    assert "POST" in response_query.headers.get("access-control-allow-methods", "")

