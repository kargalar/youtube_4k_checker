"""
Configuration management service
Handles application settings and configuration
"""
import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages application configuration and settings"""
    
    DEFAULT_CONFIG = {
        # YouTube API settings
        'youtube': {
            'api_key': '',
            'max_results': 50,
            'timeout': 10
        },
        
        # 4K Checker settings
        'checker': {
            'max_workers': 6,
            'timeout': 10,
            'verify_ssl': False,
            'retry_attempts': 2
        },
        
        # Thumbnail settings
        'thumbnails': {
            'cache_dir': 'thumbnails',
            'max_cache_size': 100,
            'thumbnail_size': [50, 50],
            'preload_enabled': True
        },
        
        # UI settings
        'ui': {
            'theme': 'dark',
            'window_size': [1000, 700],
            'window_position': None,
            'auto_check_4k': True,
            'show_thumbnails': True
        },
        
        # Advanced settings
        'advanced': {
            'debug_mode': False,
            'log_level': 'INFO',
            'auto_save_results': True,
            'export_format': 'json'
        }
    }
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Use default config on error
    
    def _merge_config(self, loaded_config):
        """Merge loaded config with defaults"""
        def merge_dict(default, loaded):
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = merge_dict(self.DEFAULT_CONFIG, loaded_config)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value by dot-separated path
        Example: get('youtube.api_key')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-separated path
        Example: set('youtube.api_key', 'your_api_key')
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set final value
        config_ref[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]):
        """Set entire configuration section"""
        self.config[section] = values
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
    
    def reset_section(self, section: str):
        """Reset specific section to defaults"""
        if section in self.DEFAULT_CONFIG:
            self.config[section] = self.DEFAULT_CONFIG[section].copy()
    
    def export_config(self, filepath: str):
        """Export configuration to file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, filepath: str):
        """Import configuration from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                self._merge_config(imported_config)
                self.save_config()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        issues = []
        
        # Check YouTube API key
        api_key = self.get('youtube.api_key')
        if not api_key or api_key.strip() == '':
            issues.append("YouTube API key is not set")
        
        # Check numeric values
        numeric_checks = [
            ('youtube.max_results', 1, 50),
            ('checker.max_workers', 1, 20),
            ('checker.timeout', 5, 60),
            ('thumbnails.max_cache_size', 10, 1000)
        ]
        
        for key, min_val, max_val in numeric_checks:
            value = self.get(key)
            if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                issues.append(f"{key} should be between {min_val} and {max_val}")
        
        # Check paths
        cache_dir = self.get('thumbnails.cache_dir')
        if not isinstance(cache_dir, str) or cache_dir.strip() == '':
            issues.append("Thumbnail cache directory path is invalid")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def get_env_vars(self) -> Dict[str, Optional[str]]:
        """Get relevant environment variables"""
        return {
            'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
            'YOUTUBE_CLIENT_SECRET': os.getenv('YOUTUBE_CLIENT_SECRET'),
            'YOUTUBE_CLIENT_ID': os.getenv('YOUTUBE_CLIENT_ID')
        }
    
    def setup_from_env(self):
        """Setup configuration from environment variables"""
        env_vars = self.get_env_vars()
        
        if env_vars['YOUTUBE_API_KEY']:
            self.set('youtube.api_key', env_vars['YOUTUBE_API_KEY'])
        
        # Add other environment variable mappings as needed
    
    def __str__(self):
        """String representation of config"""
        return json.dumps(self.config, indent=2, default=str)
