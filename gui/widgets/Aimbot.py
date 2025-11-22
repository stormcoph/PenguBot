from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from .colors import get_theme_manager # Use theme manager
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean, ScrollableSettingsWidget,
                                  SettingsKeybind)
from gui.widgets.Header import HeaderWidget


class AimbotWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager() # Get theme manager instance
        self.config_manager = config_manager
        self.setVisible(False)
        self.move(86, 7)
        self.resize(607, 426)

        # Initialize UI
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(0)

        # Header
        self.header = HeaderWidget("Combat Configuration")
        self.layout.addWidget(self.header)

        # Create scroll area and its container widget
        # ScrollableSettingsWidget now handles its own theme updates
        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        aimbot_label = QLabel("Aimbot Settings")
        aimbot_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold; margin-top: 10px;")
        container_layout.addWidget(aimbot_label)


        toggle = SettingsBoolean("Aimbot Toggle", True)
        container_layout.addWidget(toggle)
        self.config_manager.register_setting("Aimbot", "enabled", toggle)

        # Trigger Key
        trigger_key = SettingsKeybind("Trigger Key", 0x02) # Default Right Click
        container_layout.addWidget(trigger_key)
        self.config_manager.register_setting("Aimbot", "trigger_key", trigger_key)

        # Scout Macro Toggle
        scout_macro_toggle = SettingsBoolean("Scout Macro", False) # Default to False
        container_layout.addWidget(scout_macro_toggle)
        self.config_manager.register_setting("Aimbot", "scout_macro", scout_macro_toggle)

        speed = SettingsSlider("Speed", 0.001 , 0.5, 0.085, allow_decimals=True)
        container_layout.addWidget(speed)
        self.config_manager.register_setting("Aimbot", "speed", speed)

        fov_slider = SettingsSlider("FOV", 100, 640, 500, allow_decimals=False)
        container_layout.addWidget(fov_slider)
        self.config_manager.register_setting("Aimbot", "fov", fov_slider)

        #fps_slider = SettingsSlider("Capture FPS", 10, 200, 120, allow_decimals=False)
        #container_layout.addWidget(fps_slider)
        #self.config_manager.register_setting("Aimbot", "fps", fps_slider)

        targeting_mode = SettingsDropdown("Targeting Mode", ["Closest", "Confidence"])
        container_layout.addWidget(targeting_mode)
        self.config_manager.register_setting("Aimbot", "targeting_mode", targeting_mode)

        target_slider_1 = SettingsSlider("target height (1)", 0.01, 1.0, 0.25, allow_decimals=True)
        container_layout.addWidget(target_slider_1)
        self.config_manager.register_setting("Aimbot", "target_height_1", target_slider_1)

        target_slider_2 = SettingsSlider("target height (2)", 0.01, 1.0, 0.25, allow_decimals=True)
        container_layout.addWidget(target_slider_2)
        self.config_manager.register_setting("Aimbot", "target_height_2", target_slider_2)

        # recoil slider
        recoil_slider = SettingsSlider("Recoil", 0.01, 1.1, 0.03, allow_decimals=True)
        container_layout.addWidget(recoil_slider)
        self.config_manager.register_setting("Aimbot", "recoil", recoil_slider)

        # max recoil
        max_recoil_slider = SettingsSlider("Max Recoil", 1.0, 5.0, 2.0, allow_decimals=True)
        container_layout.addWidget(max_recoil_slider)
        self.config_manager.register_setting("Aimbot", "max_recoil", max_recoil_slider)

        # Add Triggerbot Section
        triggerbot_label = QLabel("Triggerbot Settings")
        triggerbot_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold; margin-top: 20px;")
        container_layout.addWidget(triggerbot_label)
        
        # Triggerbot Toggle
        triggerbot_toggle = SettingsBoolean("Triggerbot Toggle", False)
        container_layout.addWidget(triggerbot_toggle)
        self.config_manager.register_setting("Triggerbot", "enabled", triggerbot_toggle)
        
        # Triggerbot Delay
        trigger_delay = SettingsSlider("Trigger Delay (ms)", 0, 500, 100, allow_decimals=False)
        container_layout.addWidget(trigger_delay)
        self.config_manager.register_setting("Triggerbot", "delay", trigger_delay)
        
        # Triggerbot Confidence
        trigger_confidence = SettingsSlider("Confidence Threshold", 0.5, 1.0, 0.8, allow_decimals=True)
        container_layout.addWidget(trigger_confidence)
        self.config_manager.register_setting("Triggerbot", "confidence", trigger_confidence)
        
        # Triggerbot Mode
        trigger_mode = SettingsDropdown("Trigger Mode", ["Any Target", "High Confidence", "In Crosshair"])
        container_layout.addWidget(trigger_mode)
        self.config_manager.register_setting("Triggerbot", "mode", trigger_mode)
        
        # Trigger Hold Time
        trigger_hold = SettingsSlider("Hold Time (ms)", 10, 300, 50, allow_decimals=False)
        container_layout.addWidget(trigger_hold)
        self.config_manager.register_setting("Triggerbot", "hold_time", trigger_hold)

        # Add stretch to push all widgets to the top
        container_layout.addStretch()

        # Set the container as the scroll area's widget
        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        # Connect theme manager signal to update styles
        self.theme_manager.themeChanged.connect(self._update_styles)
        # Connect other signals as needed
        pass

    def _update_styles(self):
        """Update styles for this widget when the theme changes."""
        # print("AimbotWidget updating styles...") # Debug print
        
        # Header updates itself

        # Child settings widgets update themselves via their own connections/methods
        # Find the ScrollableSettingsWidget and tell it to update its scrollbar style
        scroll_area = self.findChild(ScrollableSettingsWidget)
        if scroll_area and hasattr(scroll_area, 'update_styles'):
            scroll_area.update_styles()
        self.update() # Trigger repaint if needed for this widget specifically

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)