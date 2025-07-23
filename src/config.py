"""
Configuration management for EFX allocation algorithm.
Loads settings from config.json file.
"""
import json
import os
from typing import Dict, Any

class Config:
    """Manages configuration settings for the EFX algorithm."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration loader.        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file '{self.config_file}' not found. Using default values.")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file '{self.config_file}': {e}")
            print("Using default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file loading fails."""
        return {
            "algorithm": {
                "normalization": {"target": 1},
                "phase_1a": {
                    "tie_tolerance": 0.001,
                    "max_sacrifice_threshold": 0.2,
                    "top_options_to_consider": 3
                },
                "phase_1b": {
                    "tie_tolerance": 0.001,
                    "relative_tie_tolerance": 0.05
                },
                "champion_graph": {
                    "max_cycle_length": 4,
                    "envy_threshold": 0.01
                }
            },
            "testing": {
                "valuation_range": {"min": 1, "max": 10},
                "perturbation": {
                    "base_epsilon": 0.0001
                }
            }
        }
    
    def get(self, path: str, default=None):
        """
        Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'algorithm.phase_1a.tie_tolerance')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"Configuration path '{path}' not found")
    
    def reload(self):
        """Reload configuration from file."""
        self._config = self._load_config()
        print(f"Configuration reloaded from '{self.config_file}'")
    
    def save(self, config_data: Dict[str, Any] = None):
        """
        Save current or provided configuration to file.
        
        Args:
            config_data: Configuration to save (uses current if None)
        """
        data_to_save = config_data if config_data is not None else self._config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        print(f"Configuration saved to '{self.config_file}'")
    
    def update(self, path: str, value):
        """
        Update configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'algorithm.phase_1a.tie_tolerance')
            value: New value to set
        """
        keys = path.split('.')
        config_ref = self._config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the final value
        config_ref[keys[-1]] = value
        print(f"Updated {path} = {value}")
    
    def show_current_config(self):
        """Display current configuration in a readable format."""
        print("=" * 60)
        print("CURRENT CONFIGURATION")
        print("=" * 60)
        self._print_config_recursive(self._config, "")
        print("=" * 60)
    
    def _print_config_recursive(self, config_dict: Dict[str, Any], prefix: str):
        """Recursively print configuration with proper indentation."""
        for key, value in config_dict.items():
            if key == "comments":
                continue  # Skip comment fields
            
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                print(f"{current_path}:")
                self._print_config_recursive(value, current_path)
            else:
                print(f"  {current_path} = {value}")

# Global configuration instance
config = Config()
