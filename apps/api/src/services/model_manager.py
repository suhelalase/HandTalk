"""Model management for ASL sign language recognition."""

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
from keras.models import load_model

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages loading and caching of the ASL model."""

    def __init__(self):
        self.models = {}
        self.model_paths = {
            "ASL": self._get_model_path("cnn8grps_rad1_model.h5"),
        }
        self._load_available_models()

    def _get_model_path(self, model_name: str) -> Optional[str]:
        """Get full path to model file."""
        # Check multiple possible locations
        api_root = Path(__file__).resolve().parents[2]  # z:/HandTalk/apps/api
        repo_root = Path(__file__).resolve().parents[4]  # z:/HandTalk

        env_path = os.getenv("HANDTALK_MODEL_PATH")
        possible_paths = [
            Path(env_path) if env_path else None,
            api_root / model_name,  # apps/api/
            api_root / "model.h5",  # Dockerfile copies here
            api_root / "models" / model_name,  # apps/api/models/
            repo_root / model_name,  # repo root
            repo_root / "model.h5",  # repo root
            repo_root / "models" / model_name,  # repo root models/
        ]

        for path in possible_paths:
            if path and path.exists():
                return str(path)

        return None

    def _load_available_models(self):
        """Load all available models."""
        for mode, model_path in self.model_paths.items():
            if model_path and os.path.exists(model_path):
                try:
                    self.models[mode] = load_model(model_path)
                    logger.info(f"✓ {mode} model loaded: {model_path}")
                except Exception as e:
                    logger.error(f"✗ Failed to load {mode} model: {e}")
            else:
                logger.warning(f"⚠ {mode} model not found at {model_path}")

    def get_model(self, mode: str = "ASL"):
        """Get ASL model (mode is accepted for backward compatibility)."""
        return self.models.get("ASL")

    def predict(self, skeleton_img: np.ndarray, mode: str = "ASL"):
        """
        Get prediction from appropriate model with full probability distribution.

        Args:
            skeleton_img: Hand skeleton image (400x400x3)
            mode: "ASL"

        Returns:
            tuple: (class_index, confidence, top2_confidence, probabilities)
        """
        model = self.get_model(mode)

        if model is None:
            logger.error(f"No model available for {mode}")
            return -1, 0.0, 0.0, None

        try:
            img = skeleton_img.reshape(1, 400, 400, 3)
            prob = np.array(model.predict(img, verbose=0)[0], dtype="float32")

            ch1 = int(np.argmax(prob, axis=0))
            top1 = float(prob[ch1])

            prob2 = prob.copy()
            prob2[ch1] = -1.0
            ch2 = int(np.argmax(prob2, axis=0))
            top2 = float(prob2[ch2])
            margin = top1 - top2

            return ch1, top1, margin, prob

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 7, 0.0, 0.0, np.zeros(8)

    def get_available_modes(self) -> list:
        """Get list of available modes."""
        return list(self.models.keys())

    def is_model_available(self, mode: str) -> bool:
        """Check if ASL model is available (mode is accepted for backward compatibility)."""
        return "ASL" in self.models


# Global model manager instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get or create global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
