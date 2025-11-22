from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty

# Define Theme Dictionaries (Hex Strings)
DEFAULT_THEME = {
    "BACKGROUND": "#1A1B26",
    "PRIMARY": "#7AA2F7",
    "SECONDARY": "#414868",
    "ACCENT": "#BB9AF7",
    "TEXT": "#C0CAF5",
    "ERROR": "#F7768E",
    "SIDEBAR_BACKGROUND": "#0F141A",
    "BACKGROUND_DARKER": "#16171F",
    "PANEL_BACKGROUND": "#0B0C12", # Alpha will be handled in paintEvent
    "AIM_INDICATOR": "#FF0000", # Alpha will be handled where used
    "FPS_GRADIENT_START": "#7AA2F7", # Matches PRIMARY
    "FPS_GRADIENT_MIDDLE": "#BB9AF7", # Matches ACCENT
    "FPS_GRADIENT_END": "#7AA2F7", # Matches PRIMARY
    "BUTTON_SHADOW": "#000000", # Alpha handled where used
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#FFFFFF",
    "UNSELECTED_ELEMENT_1": "#414868", # Matches SECONDARY
    "UNSELECTED_ELEMENT_2": "#9F83D8", # Slightly Darker than ACCENT
    "SELECTED_ELEMENT_1": "#7AA2F7", # Matches PRIMARY
    "SELECTED_ELEMENT_2": "#BB9AF7", # Matches ACCENT
    "HOVER_HIGHLIGHT": "#545B89", # Slightly lighter than SECONDARY
    "ACTIVE_ELEMENT": "#7AA2F7", # Matches PRIMARY
    "SETTINGS_BACKGROUND": "#13151D",
    "SECTION_HEADER": "#7AA2F7", # Matches PRIMARY
    "SECTION_BORDER": "#414868", # Matches SECONDARY
    "INPUT_BACKGROUND": "#16171F",
    "INPUT_HIGHLIGHT": "#2A2D3A",
    "TOGGLE_ACTIVE": "#7AA2F7",
    "TOGGLE_INACTIVE": "#545B89"
}

OCEAN_THEME = {
    "BACKGROUND": "#0F2D3D",
    "PRIMARY": "#4ECDC4",
    "SECONDARY": "#2A6073",
    "ACCENT": "#7FDBDA",
    "TEXT": "#E0FBFC",
    "ERROR": "#FF6B6B",
    "SIDEBAR_BACKGROUND": "#08202D",
    "BACKGROUND_DARKER": "#0C2634",
    "PANEL_BACKGROUND": "#071B25",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#4ECDC4",
    "FPS_GRADIENT_MIDDLE": "#7FDBDA",
    "FPS_GRADIENT_END": "#4ECDC4",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#E0FBFC",
    "UNSELECTED_ELEMENT_1": "#2A6073",
    "UNSELECTED_ELEMENT_2": "#3D8B99",
    "SELECTED_ELEMENT_1": "#4ECDC4",
    "SELECTED_ELEMENT_2": "#7FDBDA",
    "HOVER_HIGHLIGHT": "#3A7A8A",
    "ACTIVE_ELEMENT": "#4ECDC4",
    "SETTINGS_BACKGROUND": "#0A2330",
    "SECTION_HEADER": "#4ECDC4",
    "SECTION_BORDER": "#2A6073",
    "INPUT_BACKGROUND": "#0C2634",
    "INPUT_HIGHLIGHT": "#1D4355",
    "TOGGLE_ACTIVE": "#4ECDC4",
    "TOGGLE_INACTIVE": "#3A7A8A"
}

RUBY_THEME = {
    "BACKGROUND": "#261A1D",
    "PRIMARY": "#D44D5C",
    "SECONDARY": "#58353A",
    "ACCENT": "#E5A4A8",
    "TEXT": "#F0E4E5",
    "ERROR": "#FF3A4B",
    "SIDEBAR_BACKGROUND": "#1E1518",
    "BACKGROUND_DARKER": "#201619",
    "PANEL_BACKGROUND": "#181214",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#D44D5C",
    "FPS_GRADIENT_MIDDLE": "#E5A4A8",
    "FPS_GRADIENT_END": "#D44D5C",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#F5EAEB",
    "UNSELECTED_ELEMENT_1": "#58353A",
    "UNSELECTED_ELEMENT_2": "#A85F67",
    "SELECTED_ELEMENT_1": "#D44D5C",
    "SELECTED_ELEMENT_2": "#E5A4A8",
    "HOVER_HIGHLIGHT": "#6D4549",
    "ACTIVE_ELEMENT": "#D44D5C",
    "SETTINGS_BACKGROUND": "#1D1619",
    "SECTION_HEADER": "#D44D5C",
    "SECTION_BORDER": "#58353A",
    "INPUT_BACKGROUND": "#201619",
    "INPUT_HIGHLIGHT": "#352527",
    "TOGGLE_ACTIVE": "#D44D5C",
    "TOGGLE_INACTIVE": "#6D4549"
}

SAPPHIRE_THEME = {
    "BACKGROUND": "#1A1D26",
    "PRIMARY": "#4D7BD4",
    "SECONDARY": "#354458",
    "ACCENT": "#A4BCE5",
    "TEXT": "#E4E8F0",
    "ERROR": "#FF3A4B",
    "SIDEBAR_BACKGROUND": "#15181E",
    "BACKGROUND_DARKER": "#161920",
    "PANEL_BACKGROUND": "#121418",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#4D7BD4",
    "FPS_GRADIENT_MIDDLE": "#A4BCE5",
    "FPS_GRADIENT_END": "#4D7BD4",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#EAF0F5",
    "UNSELECTED_ELEMENT_1": "#354458",
    "UNSELECTED_ELEMENT_2": "#5F78A8",
    "SELECTED_ELEMENT_1": "#4D7BD4",
    "SELECTED_ELEMENT_2": "#A4BCE5",
    "HOVER_HIGHLIGHT": "#455A6D",
    "ACTIVE_ELEMENT": "#4D7BD4",
    "SETTINGS_BACKGROUND": "#16191D",
    "SECTION_HEADER": "#4D7BD4",
    "SECTION_BORDER": "#354458",
    "INPUT_BACKGROUND": "#161920",
    "INPUT_HIGHLIGHT": "#252935",
    "TOGGLE_ACTIVE": "#4D7BD4",
    "TOGGLE_INACTIVE": "#455A6D"
}

EMERALD_THEME = {
    "BACKGROUND": "#1A261E",
    "PRIMARY": "#4DB063",
    "SECONDARY": "#355840",
    "ACCENT": "#A4E5B3",
    "TEXT": "#E4F0E8",
    "ERROR": "#FF3A4B",
    "SIDEBAR_BACKGROUND": "#151E17",
    "BACKGROUND_DARKER": "#162019",
    "PANEL_BACKGROUND": "#121814",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#4DB063",
    "FPS_GRADIENT_MIDDLE": "#A4E5B3",
    "FPS_GRADIENT_END": "#4DB063",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#EAF5ED",
    "UNSELECTED_ELEMENT_1": "#355840",
    "UNSELECTED_ELEMENT_2": "#5FA871",
    "SELECTED_ELEMENT_1": "#4DB063",
    "SELECTED_ELEMENT_2": "#A4E5B3",
    "HOVER_HIGHLIGHT": "#456D4E",
    "ACTIVE_ELEMENT": "#4DB063",
    "SETTINGS_BACKGROUND": "#161D19",
    "SECTION_HEADER": "#4DB063",
    "SECTION_BORDER": "#355840",
    "INPUT_BACKGROUND": "#162019",
    "INPUT_HIGHLIGHT": "#253528",
    "TOGGLE_ACTIVE": "#4DB063",
    "TOGGLE_INACTIVE": "#456D4E"
}

BLACK_PEARL_THEME = {
    "BACKGROUND": "#1A1D1F",
    "PRIMARY": "#4D7D84",
    "SECONDARY": "#353B3D",
    "ACCENT": "#738F97",
    "TEXT": "#E4E8EA",
    "ERROR": "#FF3A4B",
    "SIDEBAR_BACKGROUND": "#15181A",
    "BACKGROUND_DARKER": "#161819",
    "PANEL_BACKGROUND": "#121415",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#4D7D84",
    "FPS_GRADIENT_MIDDLE": "#738F97",
    "FPS_GRADIENT_END": "#4D7D84",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#EAF0F2",
    "UNSELECTED_ELEMENT_1": "#353B3D",
    "UNSELECTED_ELEMENT_2": "#5F767A",
    "SELECTED_ELEMENT_1": "#4D7D84",
    "SELECTED_ELEMENT_2": "#738F97",
    "HOVER_HIGHLIGHT": "#454C4F",
    "ACTIVE_ELEMENT": "#4D7D84",
    "SETTINGS_BACKGROUND": "#161A1C",
    "SECTION_HEADER": "#4D7D84",
    "SECTION_BORDER": "#353B3D",
    "INPUT_BACKGROUND": "#161819",
    "INPUT_HIGHLIGHT": "#252829",
    "TOGGLE_ACTIVE": "#4D7D84",
    "TOGGLE_INACTIVE": "#454C4F"
}

TIGER_TOOTH_THEME = {
    "BACKGROUND": "#262215",
    "PRIMARY": "#D49A3F",
    "SECONDARY": "#584A2D",
    "ACCENT": "#E5CA8A",
    "TEXT": "#F0EBE0",
    "ERROR": "#FF3A4B",
    "SIDEBAR_BACKGROUND": "#1E1B11",
    "BACKGROUND_DARKER": "#201C13",
    "PANEL_BACKGROUND": "#18160F",
    "AIM_INDICATOR": "#FF0000",
    "FPS_GRADIENT_START": "#D49A3F",
    "FPS_GRADIENT_MIDDLE": "#E5CA8A",
    "FPS_GRADIENT_END": "#D49A3F",
    "BUTTON_SHADOW": "#000000",
    "UI_ELEMENT": "#FFFFFF",
    "SNOWFLAKE": "#F5F1EA",
    "UNSELECTED_ELEMENT_1": "#584A2D",
    "UNSELECTED_ELEMENT_2": "#A89160",
    "SELECTED_ELEMENT_1": "#D49A3F",
    "SELECTED_ELEMENT_2": "#E5CA8A",
    "HOVER_HIGHLIGHT": "#6D5C3A",
    "ACTIVE_ELEMENT": "#D49A3F",
    "SETTINGS_BACKGROUND": "#1D1914",
    "SECTION_HEADER": "#D49A3F",
    "SECTION_BORDER": "#584A2D",
    "INPUT_BACKGROUND": "#201C13",
    "INPUT_HIGHLIGHT": "#352E21",
    "TOGGLE_ACTIVE": "#D49A3F",
    "TOGGLE_INACTIVE": "#6D5C3A"
}

# Add more themes here if needed

AVAILABLE_THEMES = {
    "Default": DEFAULT_THEME,
    "Ocean": OCEAN_THEME,
    "Ruby": RUBY_THEME,
    "Sapphire": SAPPHIRE_THEME,
    "Emerald": EMERALD_THEME,
    "Black Pearl": BLACK_PEARL_THEME,
    "Tiger Tooth": TIGER_TOOTH_THEME,
}

class ThemeManager(QObject):
    themeChanged = pyqtSignal()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ThemeManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_manager=None):
        if self._initialized:
            return
        super().__init__()
        self._config_manager = config_manager
        self._themes = AVAILABLE_THEMES
        self._active_theme_name = "Default" # Default theme
        self._active_theme_dict = self._themes[self._active_theme_name]

        if self._config_manager:
            # Load theme from config if available
            saved_theme = self._config_manager.get("Theme.active", "Default")
            if saved_theme in self._themes:
                self.set_active_theme(saved_theme, save_config=False) # Don't save on initial load
            else:
                print(f"Warning: Saved theme '{saved_theme}' not found. Using Default.")
                self.set_active_theme("Default", save_config=True) # Save default if saved one was invalid

            # Register observer to update theme if changed externally (e.g., manual JSON edit)
            self._config_manager.register_observer(self._config_changed_externally)

        self._initialized = True

    def _config_changed_externally(self):
        """Called when ConfigManager detects external file changes."""
        if not self._config_manager: return
        saved_theme = self._config_manager.get("Theme.active", "Default")
        if saved_theme != self._active_theme_name and saved_theme in self._themes:
            print(f"Theme changed externally to: {saved_theme}")
            self.set_active_theme(saved_theme, save_config=False) # Already saved externally

    @property
    def available_themes(self):
        return list(self._themes.keys())

    @pyqtProperty(str, notify=themeChanged)
    def active_theme_name(self):
        return self._active_theme_name

    def set_active_theme(self, theme_name: str, save_config: bool = True):
        if theme_name in self._themes and theme_name != self._active_theme_name:
            print(f"Setting active theme to: {theme_name}")
            self._active_theme_name = theme_name
            self._active_theme_dict = self._themes[theme_name]

            if save_config and self._config_manager:
                # Use _update_setting directly if possible, otherwise set and save
                if hasattr(self._config_manager, '_update_setting'):
                     self._config_manager._update_setting("Theme", "active", theme_name)
                else:
                     # Fallback if _update_setting is not accessible or changes
                     if "Theme" not in self._config_manager._config:
                         self._config_manager._config["Theme"] = {}
                     self._config_manager._config["Theme"]["active"] = theme_name
                     self._config_manager.save()

            self.themeChanged.emit()
        elif theme_name not in self._themes:
            print(f"Error: Theme '{theme_name}' not found.")

    def get_color(self, name: str, alpha: int = 255) -> QColor:
        """Gets a QColor from the active theme by its semantic name."""
        hex_color = self._active_theme_dict.get(name, "#FFFFFF") # Default to white if name not found
        color = QColor(hex_color)
        if alpha != 255:
            color.setAlpha(alpha)
        return color

# Global instance (Singleton pattern)
# Pass config_manager during app initialization
theme_manager = ThemeManager()

# Convenience function to access the manager easily and ensure proper initialization
def get_theme_manager(config_manager=None) -> ThemeManager:
    global theme_manager # Access the global instance created at module level

    # Ensure the singleton instance exists (it should, due to module-level creation)
    if theme_manager is None:
        # This case should ideally not happen if the module is imported correctly
        theme_manager = ThemeManager()
        print("Warning: Global theme_manager was None, re-created.") # Add warning

    # If a config_manager is provided and the theme_manager hasn't been fully initialized yet
    # (which includes associating the config_manager and loading the initial theme).
    if config_manager and not theme_manager._initialized:
        # Call __init__ only if not already initialized.
        # The __init__ itself handles the config_manager assignment, theme loading, and setting _initialized = True.
        # Pass the config_manager here.
        # print("Initializing theme_manager via get_theme_manager...") # Debug print
        theme_manager.__init__(config_manager=config_manager)

    # Optional: If already initialized but somehow missing config_manager (might indicate logic error elsewhere)
    elif config_manager and not theme_manager._config_manager:
         print("Warning: theme_manager was initialized but missing config_manager. Re-associating.") # Add warning
         theme_manager._config_manager = config_manager
         # Manually load theme and register observer again if re-associating
         saved_theme = theme_manager._config_manager.get("Theme.active", "Default")
         if saved_theme in theme_manager._themes:
             theme_manager.set_active_theme(saved_theme, save_config=False)
         else:
             theme_manager.set_active_theme("Default", save_config=True)
         # Ensure observer is registered if we are re-associating.
         # The register_observer method should ideally handle preventing duplicates.
         # Remove the incorrect attempt to disconnect a non-existent signal.
         # try:
         #     # Attempt to disconnect first to prevent duplicates if receiver exists
         #     theme_manager._config_manager.settings_changed.disconnect(theme_manager._config_changed_externally)
         # except TypeError: # Raised if not connected
         #     pass # No need to disconnect if not connected
         # except AttributeError: # Handle if the attribute doesn't exist
         #      print("Warning: ConfigManager does not have settings_changed signal for disconnection.")
         #      pass
         theme_manager._config_manager.register_observer(theme_manager._config_changed_externally)


    return theme_manager
