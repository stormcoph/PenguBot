from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from gui.widgets.colors import Colors
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean,
                                ScrollableSettingsWidget)
import glob
import os


class AIWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setVisible(False)
        self.move(86, 7)
        self.resize(607, 426)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(0)

        title = QLabel("AI Configuration")
        title.setStyleSheet(f"color: {Colors.TEXT.name()}; font-family: Roboto; font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)

        scroll_area = ScrollableSettingsWidget(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        # Get model files using absolute path
        current_dir = os.path.dirname(__file__)  # Gets directory of this file (gui/widgets/)
        models_dir = os.path.abspath(os.path.join(current_dir, "../../assets/models"))

        print(f"Looking for models in: {models_dir}")  # Debug print

        model_files = glob.glob(os.path.join(models_dir, "*.engine"))
        model_filenames = [os.path.basename(f) for f in model_files]

        print(f"Found models: {model_filenames}")  # Debug print

        confidence_slider = SettingsSlider("Confidence", 0.01, 1.0, 0.75, allow_decimals=True)
        container_layout.addWidget(confidence_slider)
        self.config_manager.register_setting("AI", "confidence", confidence_slider)

        nms_slider = SettingsSlider("NMS IOU Threshold", 0.01, 1.0, 0.8, allow_decimals=True)
        container_layout.addWidget(nms_slider)
        self.config_manager.register_setting("AI", "nms_iou_threshold", nms_slider)

        model_dropdown = SettingsDropdown("Model", model_filenames)
        container_layout.addWidget(model_dropdown)
        self.config_manager.register_setting("AI", "model", model_dropdown)
        container_layout.addStretch()

        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)