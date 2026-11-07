import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "classes" in data
    assert "device" in data

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Face Mask Detection" in response.json()["message"]

def test_analytics_endpoint():
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_detections" in data
    assert "compliance_rate" in data
    assert "pie_chart" in data
    assert "hourly_trend" in data

def test_history_endpoint():
    response = client.get("/api/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)

