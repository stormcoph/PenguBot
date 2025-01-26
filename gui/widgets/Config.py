from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from gui.widgets.colors import Colors
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean,
                                ScrollableSettingsWidget)
import glob
import os

class ConfigWidget(QWidget):
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
        self.layout.setSpacing(15)

        # Add your About-specific widgets here
        # Example widgets (replace with actual features):
        title = QLabel("About PenguBot")
        title.setStyleSheet(f"color: {Colors.TEXT.name()}; font-family: Roboto; font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)

        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        current_dir = os.path.dirname(__file__)
        models_dir = os.path.abspath(os.path.join(current_dir, "../../assets/config"))

        model_files = glob.glob(os.path.join(models_dir, "*.json"))
        model_filenames = [os.path.basename(f) for f in model_files]

        """model_dropdown = SettingsDropdown("Config", model_filenames)
        container_layout.addWidget(model_dropdown)
        self.config_manager.register_setting("config", "model", model_dropdown)
        container_layout.addStretch()"""

        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

        # Add more widgets specific to About functionality

    def setup_connections(self):
        # Connect your signals and slots here
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Add any custom painting code here
        pass