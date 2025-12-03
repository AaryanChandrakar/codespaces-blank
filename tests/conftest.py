"""
Test utilities and fixtures.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def config_path():
    """Fixture for config path."""
    return "config/config.yaml"


@pytest.fixture
def sample_image_path():
    """Fixture for sample image path."""
    return Path("tests/sample_images/test_bottle.jpg")


@pytest.fixture
def mock_yolo_model():
    """Fixture for mocked YOLO model."""
    mock_model = MagicMock()
    mock_model.predict.return_value = []
    return mock_model
