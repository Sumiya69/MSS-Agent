
"""
Configuration utilities for the data validation agent.
"""
import yaml
from typing import Dict, Any
import os
from pathlib import Path

class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_path} not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def email_config(self) -> Dict[str, Any]:
        """Get email configuration."""
        return self.get('email', {})
    
    @property
    def business_unit_config(self) -> Dict[str, Any]:
        """Get business unit configuration."""
        return self.get('business_unit', {})
    
    @property
    def validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        return self.get('validation', {})
    
    @property
    def file_upload_config(self) -> Dict[str, Any]:
        """Get file upload configuration."""
        return self.get('file_upload', {})
    
    @property
    def notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self.get('notification', {})

# Global config instance
config = Config()
