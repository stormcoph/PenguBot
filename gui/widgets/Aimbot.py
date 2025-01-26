from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from gui.widgets.colors import Colors
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean, ScrollableSettingsWidget,
                                  )


class AimbotWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
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

        # Title
        title = QLabel("Aimbot Configuration")
        title.setStyleSheet(f"color: {Colors.TEXT.name()}; font-family: Roboto; font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)

        # Create scroll area and its container widget
        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)



        toggle = SettingsBoolean("Aimbot Toggle", True)
        container_layout.addWidget(toggle)
        self.config_manager.register_setting("Aimbot", "enabled", toggle)

        speed = SettingsSlider("Speed", 0.001 , 0.5, 0.085, allow_decimals=True)
        container_layout.addWidget(speed)
        self.config_manager.register_setting("Aimbot", "speed", speed)

        fov_slider = SettingsSlider("FOV", 100, 640, 500, allow_decimals=False)
        container_layout.addWidget(fov_slider)
        self.config_manager.register_setting("Aimbot", "fov", fov_slider)

        target_slider_1 = SettingsSlider("target height (1)", 0.01, 1.0, 0.25, allow_decimals=True)
        container_layout.addWidget(target_slider_1)
        self.config_manager.register_setting("Aimbot", "target_height_1", target_slider_1)

        target_slider_2 = SettingsSlider("target height (2)", 0.01, 1.0, 0.25, allow_decimals=True)
        container_layout.addWidget(target_slider_2)
        self.config_manager.register_setting("Aimbot", "target_height_2", target_slider_2)

        # Add stretch to push all widgets to the top
        container_layout.addStretch()

        # Set the container as the scroll area's widget
        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)