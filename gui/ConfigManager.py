import json
import os
from pathlib import Path
from typing import Any
from PyQt5.QtCore import QTimer

class ConfigManager:
    def __init__(self):
        self._config = {}
        self.file_path = Path(__file__).parent.parent / "assets" / "config" / "settings.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_modified = 0
        self.observers = []
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_reload)
        self.check_timer.start(500)
        self.load()

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    @property
    def config(self) -> dict[str, Any]:
        """Get current config, checking for updates first"""
        self.check_reload()
        return self._config

    def __init__(self):
        self._config = {}
        self.file_path = Path(__file__).parent.parent / "assets" / "config" / "settings.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_modified = 0
        self.observers = []
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_reload)
        self.check_timer.start(500)
        self.load()

    def register_observer(self, callback: callable) -> None:
        """Register a callback to be notified of config changes"""
        self.observers.append(callback)

    def check_reload(self) -> None:
        """Reload config if file has been modified externally"""
        try:
            if self.file_path.exists():
                current_mtime = os.path.getmtime(self.file_path)
                if current_mtime > self.last_modified:
                    self.load()
                    # Notify all observers of config change
                    for callback in self.observers:
                        callback()
        except Exception as e:
            print(f"Error checking config reload: {e}")

    def load(self) -> None:
        """Load config from file if it has changed"""
        try:
            if self.file_path.exists():
                current_mtime = os.path.getmtime(self.file_path)
                if current_mtime > self.last_modified:
                    with open(self.file_path, 'r') as f:
                        self._config = json.load(f)
                    self.last_modified = current_mtime
        except Exception as e:
            print(f"Error loading config: {e}")

    def save(self) -> None:
        """Save config to file and update modification time"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            self.last_modified = os.path.getmtime(self.file_path)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a config value using dot-notation path (e.g. 'Visual.fps_x')"""
        keys = key_path.split('.')
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def register_setting(self, section: str, key: str, widget: Any) -> None:
        """Connect a UI widget to a config setting"""
        if section not in self._config:
            self._config[section] = {}

        # Connect widget changes to config updates
        widget.valueChanged.connect(lambda v, s=section, k=key: self._update_setting(s, k, v))

        # Initialize widget value
        if section in self._config and key in self._config[section]:
            widget.set_value(self._config[section][key])
        else:
            self._config[section][key] = widget.get_value()
            self.save()

    def _update_setting(self, section: str, key: str, value: Any) -> None:
        """Update a setting and trigger save"""
        self._config[section][key] = value
        self.save()
