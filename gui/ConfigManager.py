import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PyQt5.QtCore import QTimer
import copy # Import copy for deep copying presets

class ConfigManager:
    SAVED_CONFIGS_KEY = "saved_configs" # Key to store presets in settings.json

    def __init__(self):
        self._config = {}
        self._cache = {}  # Add cache for frequently accessed values
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

    def _notify_observers(self) -> None:
        """Notify all observers of config change"""
        for callback in self.observers:
            try:
                callback()
            except Exception as e:
                print(f"Error in observer callback: {e}")

    @property
    def config(self) -> Dict[str, Any]:
        """Get current config, checking for updates first"""
        self.check_reload()
        return self._config

    def check_reload(self) -> None:
        """Reload config if file has been modified externally"""
        try:
            if self.file_path.exists():
                current_mtime = os.path.getmtime(self.file_path)
                if current_mtime > self.last_modified:
                    print(f"Config file modified externally. Reloading {self.file_path}") # Debug print
                    self.load()
                    self._cache.clear()  # Clear cache when config is reloaded
                    self._notify_observers() # Notify observers after reload
        except Exception as e:
            print(f"Error checking config reload: {e}")

    def load(self) -> None:
        """Load config from file"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    self._config = json.load(f)
                self.last_modified = os.path.getmtime(self.file_path)
                print(f"Config loaded successfully from {self.file_path}") # Debug print
            else:
                print(f"Config file not found at {self.file_path}. Initializing empty config.")
                self._config = {self.SAVED_CONFIGS_KEY: {}} # Initialize with empty presets dict
                self.last_modified = 0
                self.save() # Create the file if it doesn't exist
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from config file {self.file_path}: {e}. Initializing empty config.")
            self._config = {self.SAVED_CONFIGS_KEY: {}} # Initialize with empty presets dict
            self.last_modified = 0
        except Exception as e:
            print(f"Error loading config: {e}. Initializing empty config.")
            self._config = {self.SAVED_CONFIGS_KEY: {}} # Initialize with empty presets dict
            self.last_modified = 0

        # Ensure saved_configs key exists
        if self.SAVED_CONFIGS_KEY not in self._config:
            self._config[self.SAVED_CONFIGS_KEY] = {}


    def save(self) -> None:
        """Save config to file and update modification time"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            new_mtime = os.path.getmtime(self.file_path)
            # Only clear cache and notify if modification time actually changed
            # This prevents unnecessary notifications during rapid saves
            if new_mtime > self.last_modified:
                self.last_modified = new_mtime
                self._cache.clear()  # Clear cache when config is saved
                # Don't notify observers here directly, let specific actions (like apply_preset) do it
                # self._notify_observers()
            print(f"Config saved successfully to {self.file_path}") # Debug print
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a config value using dot-notation path (e.g. 'Visual.fps_x')"""
        # Check cache first
        if key_path in self._cache:
            return self._cache[key_path]

        # If not in cache, compute value
        keys = key_path.split('.')
        current = self.config # Use property to ensure latest config is checked
        for key in keys:
            # Prevent accessing the saved_configs section directly via get
            if key == self.SAVED_CONFIGS_KEY and len(keys) == 1:
                 print(f"Warning: Direct access to '{self.SAVED_CONFIGS_KEY}' via get() is discouraged.")
                 return default

            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # print(f"Key '{key}' not found in path '{key_path}'. Returning default: {default}") # Debug print
                return default

        # Cache the result
        self._cache[key_path] = current
        return current

    def register_setting(self, section: str, key: str, widget: Any) -> None:
        """Connect a UI widget to a config setting"""
        if section not in self._config:
            self._config[section] = {}

        # Connect widget changes to config updates
        # Use a default argument for value in lambda to capture current v
        widget.valueChanged.connect(lambda value, s=section, k=key: self._update_setting(s, k, value))

        # Initialize widget value from config
        self._initialize_widget_value(section, key, widget)

        # Register observer to update widget if config changes externally or via preset apply
        self.register_observer(lambda s=section, k=key, w=widget: self._initialize_widget_value(s, k, w))


    def _initialize_widget_value(self, section: str, key: str, widget: Any) -> None:
        """Sets the widget's value based on the current config."""
        current_value = self.get(f"{section}.{key}", None) # Use get method
        if current_value is not None:
            # Check if widget's current value is different before setting
            # This prevents potential signal loops if setting the value triggers valueChanged
            try:
                if widget.get_value() != current_value:
                    widget.set_value(current_value)
            except Exception as e:
                 print(f"Error setting widget value for {section}.{key} from config: {e}. Using widget default.")
                 # If setting fails, update config with widget's default
                 self._update_setting(section, key, widget.get_value(), save_now=False) # Avoid immediate save if part of larger load/apply
                 self.save() # Save after potential update
        else:
            # If setting doesn't exist in config, get default from widget and save it
            print(f"Setting {section}.{key} not found in config. Initializing from widget default.") # Debug print
            self._update_setting(section, key, widget.get_value(), save_now=True) # Save immediately


    def _update_setting(self, section: str, key: str, value: Any, save_now: bool = True) -> None:
        """Update a setting and optionally trigger save"""
        # Ensure the section exists before trying to assign to it
        if section not in self._config:
            self._config[section] = {}

        # Only update and potentially save if the value actually changed
        if key not in self._config[section] or self._config[section][key] != value:
             print(f"Updating config: {section}.{key} = {value}") # Debug print
             self._config[section][key] = value
             # Clear specific cache entry
             cache_key = f"{section}.{key}"
             if cache_key in self._cache:
                 del self._cache[cache_key]
             if save_now:
                 self.save()

    # --- Preset Management Methods ---

    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Returns the dictionary of saved presets {title: {description: str, config: dict}}."""
        return self._config.get(self.SAVED_CONFIGS_KEY, {})

    def save_preset(self, title: str, description: str = "") -> bool:
        """Saves the current configuration (excluding presets) as a new preset."""
        if not title:
            print("Error: Preset title cannot be empty.")
            return False

        presets = self.get_presets()
        # Create a deep copy of the current config, excluding the presets section itself
        current_config_copy = copy.deepcopy({k: v for k, v in self._config.items() if k != self.SAVED_CONFIGS_KEY})

        presets[title] = {
            "description": description,
            "config": current_config_copy
        }
        self._config[self.SAVED_CONFIGS_KEY] = presets
        self.save()
        print(f"Preset '{title}' saved.")
        return True

    def apply_preset(self, title: str) -> bool:
        """Applies a saved preset configuration."""
        presets = self.get_presets()
        if title not in presets:
            print(f"Error: Preset '{title}' not found.")
            return False

        preset_data = presets[title].get("config", {})
        if not preset_data:
             print(f"Error: Preset '{title}' has no configuration data.")
             return False

        print(f"Applying preset '{title}'...")
        # Create a deep copy to avoid modifying the stored preset directly
        config_to_apply = copy.deepcopy(preset_data)

        # Update the main config, preserving the saved_configs section
        saved_configs_backup = copy.deepcopy(self.get_presets()) # Keep the presets safe
        self._config.clear() # Clear current config
        self._config.update(config_to_apply) # Apply preset config
        self._config[self.SAVED_CONFIGS_KEY] = saved_configs_backup # Restore presets

        self._cache.clear() # Clear cache as many values changed
        self.save() # Save the newly applied config
        self._notify_observers() # Notify UI elements to update
        print(f"Preset '{title}' applied successfully.")
        return True

    def delete_preset(self, title: str) -> bool:
        """Deletes a saved preset."""
        presets = self.get_presets()
        if title not in presets:
            print(f"Error: Preset '{title}' not found for deletion.")
            return False

        del presets[title]
        self._config[self.SAVED_CONFIGS_KEY] = presets
        self.save()
        print(f"Preset '{title}' deleted.")
        return True

    def get_preset_details(self, title: str) -> Optional[Tuple[str, str]]:
        """Gets the title and description of a specific preset."""
        preset = self.get_presets().get(title)
        if preset:
            return title, preset.get("description", "")
        return None