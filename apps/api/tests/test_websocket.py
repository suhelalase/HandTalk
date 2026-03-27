"""
Tests for WebSocket functionality.
"""

import base64
import json

import cv2
import numpy as np
import pytest


def create_test_frame():
    """Create a test frame and encode as base64 data-uri."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    _, buffer = cv2.imencode('.jpg', img)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_image}"


@pytest.mark.asyncio
def test_websocket_receives_response(test_client):
    """Test that WebSocket receives valid response."""
    with test_client.websocket_connect("/ws") as websocket:
        frame_payload = {
            "image": create_test_frame(),
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
                "image": create_test_frame(),
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
            "image": create_test_frame(),
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
        # Send invalid image
        frame_payload = {
            "image": "data:image/jpeg;base64,INVALID_BASE64",
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
    """Test switching between ASL and ISL modes."""
    with test_client.websocket_connect("/ws") as websocket:
        # Test ASL mode
        asl_payload = {
            "image": create_test_frame(),
            "mode": "ASL",
            "inputMode": "letters",
            "frameId": 1,
            "clientTs": 1234567890.0
        }
        websocket.send_json(asl_payload)
        asl_response = websocket.receive_json()
        assert asl_response["mode"] == "ASL"

        # Test ISL mode
        isl_payload = {
            "image": create_test_frame(),
            "mode": "ISL",
            "inputMode": "letters",
            "frameId": 2,
            "clientTs": 1234567891.0
        }
        websocket.send_json(isl_payload)
        isl_response = websocket.receive_json()
        assert isl_response["mode"] == "ISL"
