from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPainter
from .colors import get_theme_manager # Use theme manager
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean,
                                ScrollableSettingsWidget)
import glob
import os


class AIWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager() # Get theme manager instance
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

        self.title = QLabel("AI Configuration") # Store as instance variable
        self._update_title_style() # Apply initial style
        self.layout.addWidget(self.title)

        scroll_area = ScrollableSettingsWidget(self)
        # ScrollableSettingsWidget now handles its own theme updates
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

        max_fps_capture = SettingsSlider("Max FPS Capture", 1, 200, 80, allow_decimals=False)
        container_layout.addWidget(max_fps_capture)
        self.config_manager.register_setting("AI", "max_fps_capture", max_fps_capture)
        container_layout.addStretch()

        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

    def setup_connections(self):
        # Connect theme manager signal to update styles
        self.theme_manager.themeChanged.connect(self._update_styles)
        pass

    def _update_title_style(self):
        """Updates the style of the title label."""
        if hasattr(self, 'title'): # Check if title exists
            self.title.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 24px; font-weight: bold;")

    def _update_styles(self):
        """Update styles for this widget when the theme changes."""
        print("AIWidget updating styles...") # Debug print
        self._update_title_style()
        # Child settings widgets update themselves
        # Find the ScrollableSettingsWidget and tell it to update its scrollbar style
        scroll_area = self.findChild(ScrollableSettingsWidget)
        if scroll_area and hasattr(scroll_area, 'update_styles'):
            scroll_area.update_styles()
        self.update() # Trigger repaint if needed

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Add any custom painting code here if needed, using self.theme_manager
        pass
