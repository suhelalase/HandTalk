"""
Pytest configuration and fixtures for backend tests.
"""

import base64
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image


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
    img = Image.new("RGB", (640, 480), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    base64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"


@pytest.fixture
def sample_frame_payload():
    """Create a sample WebSocket frame payload."""
    return {
        "landmarks": [[100 + i * 5, 100 + i * 3, 0.0] for i in range(21)],
        "mode": "ASL",
        "inputMode": "letters",
        "frameId": 1,
        "clientTs": 1234567890.123,
    }


@pytest.fixture
def mock_landmarks():
    """Create mock hand landmarks (21 points)."""
    landmarks = []
    for i in range(21):
        landmarks.append([100 + i * 5, 100 + i * 3, 0.0])
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
