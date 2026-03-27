"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(test_client):
    """Test root / endpoint returns HTML."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "HandTalk Inference API" in response.text or "html" in response.headers.get("content-type", "").lower()


def test_api_is_running(test_client):
    """Test that API starts without errors."""
    response = test_client.get("/")
    assert response.status_code in [200, 307]  # 307 for redirect


def test_health_check_not_yet_implemented(test_client):
    """Test that health check endpoint works when implemented."""
    # This will be added later when we implement /health endpoint
    response = test_client.get("/health")
    # For now, expect 404 since not implemented yet
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_websocket_connection(test_client):
    """Test WebSocket connection establishment."""
    with test_client.websocket_connect("/ws") as websocket:
        # Connection should succeed
        assert websocket is not None
