"""
Configuration Management

Loads and manages application configuration from JSON file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """
    Application configuration manager.
    
    Loads configuration from JSON file with fallback to template.
    """
    
    def __init__(self, config_path: Path | None = None, template_path: Path | None = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config file (default: src/app/config/app_config.json)
            template_path: Path to template file (default: src/app/config/config_template.json)
        """
        if config_path is None:
            # Default to src/app/config/app_config.json
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "src" / "app" / "config" / "app_config.json"
        
        if template_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            template_path = project_root / "src" / "app" / "config" / "config_template.json"
        
        self.config_path = Path(config_path)
        self.template_path = Path(template_path)
        self._config: dict[str, Any] = {}
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create from template."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}. Using template.")
                self._create_from_template()
        else:
            # Create config from template
            self._create_from_template()
    
    def _create_from_template(self):
        """Create config file from template."""
        if self.template_path.exists():
            try:
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                
                # Save to config path
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2)
            except Exception as e:
                print(f"Error creating config from template: {e}")
                self._config = {}
        else:
            # No template, use defaults
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        project_root = Path(__file__).parent.parent.parent.parent
        return {
            "directories": {
                "input": str(project_root / "input"),
                "output": str(project_root / "output")
            },
            "cache": {
                "enabled": True,
                "max_size_gb": 2,
                "ttl_seconds": 3600
            },
            "watchdog": {
                "enabled": True,
                "polling_interval": 1.0
            },
            "logging": {
                "level": "INFO",
                "rotation_size_mb": 50,
                "retention_days": 30
            },
            "ui": {
                "auto_sample_threshold_rows": 5000,
                "auto_sample_threshold_cols": 100,
                "preview_percentage": 10
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "directories.input")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "directories.input")
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)
    
    def to_dict(self) -> dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()


# Global config instance
_config_instance: Optional["Config"] = None


def get_config() -> Config:
    """
    Get or create global configuration instance.
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

