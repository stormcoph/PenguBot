from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from gui.widgets.colors import Colors
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean, ScrollableSettingsWidget,
                                  )
from win32api import GetSystemMetrics


class VisualWidget(QWidget):
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
        title = QLabel("Visual Configuration")
        title.setStyleSheet(f"color: {Colors.TEXT.name()}; font-family: Roboto; font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)

        # Create scroll area and its container widget
        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        # Add settings to the container

        fps = SettingsBoolean("Display FPS", True)
        container_layout.addWidget(fps)
        self.config_manager.register_setting("Visual", "fps", fps)

        fps_x = SettingsSlider("FPS X", 0, GetSystemMetrics(0), 0, allow_decimals=False)
        container_layout.addWidget(fps_x)
        self.config_manager.register_setting("Visual", "fps_x", fps_x)

        fps_y = SettingsSlider("FPS Y", 0, GetSystemMetrics(1), 0, allow_decimals=False)
        container_layout.addWidget(fps_y)
        self.config_manager.register_setting("Visual", "fps_y", fps_y)

        fov = SettingsBoolean("Display FOV", True)
        container_layout.addWidget(fov)
        self.config_manager.register_setting("Visual", "fov", fov)

        target = SettingsBoolean("Display Target", True)
        container_layout.addWidget(target)
        self.config_manager.register_setting("Visual", "target", target)


        # Add stretch to push all widgets to the top
        container_layout.addStretch()

        # Set the container as the scroll area's widget
        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        # Connect your signals and slots here
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Add any custom painting code here
        pass