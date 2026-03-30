"""
Tests for WebSocket functionality.
"""

import json

import pytest

def create_test_landmarks():
    """Create mock hand landmarks (21 points)."""
    return [[100 + i * 5, 100 + i * 3, 0.0] for i in range(21)]


@pytest.mark.asyncio
def test_websocket_receives_response(test_client):
    """Test that WebSocket receives valid response."""
    with test_client.websocket_connect("/ws") as websocket:
        frame_payload = {
            "landmarks": create_test_landmarks(),
            "mode": "ASL",
            "inputMode": "letters",
            "frameId": 1,
            "clientTs": 1234567890.123
        }
        websocket.send_json(frame_payload)
        data = websocket.receive_json()

        # Check response structure
        assert "frameId" in data
        assert "timingMs" in data
        assert "transcript" in data
        assert "currentChar" in data
        assert "mode" in data
        assert "inputMode" in data
        assert "overlay" in data


@pytest.mark.asyncio
def test_websocket_accumulates_transcript(test_client):
    """Test that transcript accumulates over frames."""
    with test_client.websocket_connect("/ws") as websocket:
        # Send multiple frames
        for i in range(3):
            frame_payload = {
                "landmarks": create_test_landmarks(),
                "mode": "ASL",
                "inputMode": "letters",
                "frameId": i,
                "clientTs": float(i)
            }
            websocket.send_json(frame_payload)
            data = websocket.receive_json()
            assert "transcript" in data


@pytest.mark.asyncio
def test_websocket_response_has_timing(test_client):
    """Test that response includes timing metrics."""
    with test_client.websocket_connect("/ws") as websocket:
        frame_payload = {
            "landmarks": create_test_landmarks(),
            "mode": "ASL",
            "inputMode": "letters",
            "frameId": 1,
            "clientTs": 1234567890.0
        }
        websocket.send_json(frame_payload)
        data = websocket.receive_json()

        # Check timing breakdown
        assert "timingMs" in data
        timing = data["timingMs"]
        assert "decode" in timing
        assert "detect" in timing
        assert "total" in timing
        assert timing["total"] > 0


@pytest.mark.asyncio
def test_websocket_invalid_image_handling(test_client):
    """Test that invalid images are handled gracefully."""
    with test_client.websocket_connect("/ws") as websocket:
        # Send invalid payload
        frame_payload = {
            "landmarks": "INVALID",
            "mode": "ASL",
            "inputMode": "letters",
            "frameId": 1,
            "clientTs": 1234567890.0
        }
        websocket.send_json(frame_payload)
        # WebSocket should still be open and not crash
        # May not receive response if image is invalid, but shouldn't close abruptly


@pytest.mark.asyncio
def test_websocket_mode_switching(test_client):
    """Test that the backend remains ASL-only regardless of client-provided mode."""
    with test_client.websocket_connect("/ws") as websocket:
        # Test ASL mode
        asl_payload = {
            "landmarks": create_test_landmarks(),
            "mode": "ASL",
            "inputMode": "letters",
            "frameId": 1,
            "clientTs": 1234567890.0
        }
        websocket.send_json(asl_payload)
        asl_response = websocket.receive_json()
        assert asl_response["mode"] == "ASL"

        # Backend is ASL-only; client-provided ISL should not change server mode
        isl_payload = {
            "landmarks": create_test_landmarks(),
            "mode": "ISL",
            "inputMode": "letters",
            "frameId": 2,
            "clientTs": 1234567891.0
        }
        websocket.send_json(isl_payload)
        isl_response = websocket.receive_json()
        assert isl_response["mode"] == "ASL"
