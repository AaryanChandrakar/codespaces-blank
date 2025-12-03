"""
Configuration loader module for managing project settings from YAML.
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the config.yaml file.
    
    Returns:
        Dictionary containing configuration settings.
    
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is malformed.
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Retrieve nested configuration values using dot notation.
    
    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path to value (e.g., "training.epochs").
        default: Default value if key not found.
    
    Returns:
        Configuration value or default.
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    
    return value


def create_directories(config: Dict[str, Any]) -> None:
    """
    Create all necessary directories from config paths.
    
    Args:
        config: Configuration dictionary.
    """
    dirs_to_create = [
        config.get("project", {}).get("raw_dir"),
        config.get("project", {}).get("processed_dir"),
        config.get("project", {}).get("models_dir"),
        config.get("project", {}).get("outputs_dir"),
        config.get("project", {}).get("metrics_dir"),
    ]
    
    for dir_path in dirs_to_create:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
