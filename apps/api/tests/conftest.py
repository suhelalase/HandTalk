"""
Pytest configuration and fixtures for backend tests.
"""

import base64
import io
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def test_client():
    """FastAPI test client fixture."""
    # Import here to avoid import issues
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from main import app
    return TestClient(app)


@pytest.fixture
def sample_image_frame():
    """Create a sample test image frame (w/ hand detected)."""
    # Create a simple white image with some features
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    # Draw some contours to simulate a hand
    cv2.circle(img, (320, 240), 50, (0, 0, 0), -1)
    cv2.circle(img, (340, 220), 10, (255, 0, 0), -1)
    cv2.circle(img, (300, 220), 10, (255, 0, 0), -1)

    # Encode to base64 JPEG
    _, buffer = cv2.imencode('.jpg', img)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_image}"


@pytest.fixture
def sample_frame_payload():
    """Create a sample WebSocket frame payload."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    _, buffer = cv2.imencode('.jpg', img)
    base64_image = base64.b64encode(buffer).decode('utf-8')

    return {
        "image": f"data:image/jpeg;base64,{base64_image}",
        "mode": "ASL",
        "inputMode": "letters",
        "frameId": 1,
        "clientTs": 1234567890.123
    }


@pytest.fixture
def mock_landmarks():
    """Create mock hand landmarks (21 points)."""
    landmarks = []
    for i in range(21):
        landmarks.append([100 + i*5, 100 + i*3])
    return landmarks


@pytest.fixture
def test_model_path():
    """Get path to test model."""
    return Path(__file__).resolve().parents[2] / "cnn8grps_rad1_model.h5"


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Setup test environment with temporary directories."""
    # Set test environment variables
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DEBUG", "True")
    return tmp_path
