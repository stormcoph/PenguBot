from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton)
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QBrush, QPen, QPainterPath
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from .colors import get_theme_manager # Use the theme manager
from gui.widgets.Settings import (SettingsDropdown, SettingsSlider, SettingsBoolean, ScrollableSettingsWidget)
from gui.widgets.Header import HeaderWidget
from win32api import GetSystemMetrics

# --- Theme Preview Widget ---
class ThemePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40) # Increased height slightly
        self.theme_name = get_theme_manager().active_theme_name # Start with current theme

    def set_theme_to_preview(self, theme_name):
        if theme_name != self.theme_name:
            self.theme_name = theme_name
            self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Get theme manager instance
        tm = get_theme_manager()
        theme_dict = tm._themes.get(self.theme_name, tm._themes["Default"]) # Fallback to default

        # Define colors for the gradient preview
        colors_to_use = ["BACKGROUND", "PRIMARY", "ACCENT", "TEXT"]
        qcolors = [QColor(theme_dict.get(name, "#FFFFFF")) for name in colors_to_use]

        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        num_colors = len(qcolors)
        for i, color in enumerate(qcolors):
            gradient.setColorAt(i / (num_colors - 1) if num_colors > 1 else 0, color)

        # Draw rounded rect with gradient
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)
        painter.setClipPath(path)
        
        painter.fillPath(path, QBrush(gradient))
        
        # Add a subtle border
        border_color = QColor(theme_dict.get("SECTION_BORDER", "#555555"))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 8, 8)

# --- Main Visual Widget ---

class VisualWidget(QWidget):
    # Add a signal for background effect changes
    effectChanged = pyqtSignal(str)
    
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

        # Get Theme Manager instance
        self.theme_manager = get_theme_manager()

        # Header
        self.header = HeaderWidget("Visual Configuration")
        self.layout.addWidget(self.header)

        # --- Theme Selection Section ---
        theme_section_layout = QVBoxLayout()
        theme_section_layout.setSpacing(10)
        theme_section_layout.setContentsMargins(0, 15, 0, 15) # Add some vertical spacing

        theme_label = QLabel("Color Theme")
        theme_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold;")
        theme_section_layout.addWidget(theme_label)

        theme_controls_layout = QHBoxLayout()
        theme_controls_layout.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.available_themes)
        self.theme_combo.setCurrentText(self.theme_manager.active_theme_name)
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-radius: 4px;
                padding: 5px;
                background-color: {self.theme_manager.get_color('INPUT_BACKGROUND').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                min-width: 150px; /* Ensure it's wide enough */
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                background-color: {self.theme_manager.get_color('INPUT_BACKGROUND').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                selection-background-color: {self.theme_manager.get_color('HOVER_HIGHLIGHT').name()};
            }}
        """)
        theme_controls_layout.addWidget(self.theme_combo, 1) # Allow combo box to stretch

        self.theme_preview = ThemePreviewWidget()
        theme_controls_layout.addWidget(self.theme_preview, 2) # Give preview more space

        apply_button = QPushButton("Apply Theme")
        apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme_manager.get_color('PRIMARY').name()};
                color: {self.theme_manager.get_color('BACKGROUND').name()};
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme_manager.get_color('HOVER_HIGHLIGHT').name()};
            }}
            QPushButton:pressed {{
                background-color: {self.theme_manager.get_color('SECONDARY').name()};
            }}
        """)
        theme_controls_layout.addWidget(apply_button)

        theme_section_layout.addLayout(theme_controls_layout)
        self.layout.addLayout(theme_section_layout) # Add theme section to main layout

        # --- Other Settings Section ---
        settings_label = QLabel("Display Settings")
        settings_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(settings_label)

        # Create scroll area and its container widget
        scroll_area = ScrollableSettingsWidget(self) # Keep scroll area for other settings
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(0, 20, 0, 20)

        # Background effect dropdown
        self.effect_dropdown = SettingsDropdown("Background Effect", ["None", "Snow", "Rain", "Matrix", "Particles", "Starfield", "Gradient Wave"])
        container_layout.addWidget(self.effect_dropdown)
        self.config_manager.register_setting("Visual", "background_effect", self.effect_dropdown)
        # Connect the dropdown directly to our signal
        self.effect_dropdown.valueChanged.connect(self.effectChanged.emit)

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
        # Connect theme selection signals
        self.theme_combo.currentTextChanged.connect(self.theme_preview.set_theme_to_preview)
        self.findChild(QPushButton, None, Qt.FindChildrenRecursively).clicked.connect(self.apply_theme) # Find the apply button

        # Connect theme manager signal to update styles if theme changes externally
        self.theme_manager.themeChanged.connect(self._update_styles)

    def apply_theme(self):
        selected_theme = self.theme_combo.currentText()
        self.theme_manager.set_active_theme(selected_theme)
        # The themeChanged signal will trigger style updates via _update_styles

    def _update_styles(self):
        """Update styles for this widget when the theme changes."""
        # print("VisualWidget updating styles...") # Debug print
        
        # Header updates itself via theme manager connection

        # Update labels
        theme_label = self.findChild(QLabel, "Color Theme") # Assuming object name is set or find by text
        if theme_label:
             theme_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold;")
        settings_label = self.findChild(QLabel, "Display Settings")
        if settings_label:
             settings_label.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-family: Roboto; font-size: 16px; font-weight: bold; margin-top: 10px;")

        # Update ComboBox style
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-radius: 4px;
                padding: 5px;
                background-color: {self.theme_manager.get_color('INPUT_BACKGROUND').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}
             QComboBox QAbstractItemView {{
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                background-color: {self.theme_manager.get_color('INPUT_BACKGROUND').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                selection-background-color: {self.theme_manager.get_color('HOVER_HIGHLIGHT').name()};
            }}
        """)

        # Update Button style
        apply_button = self.findChild(QPushButton, None, Qt.FindChildrenRecursively) # Find the apply button again
        if apply_button:
            apply_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme_manager.get_color('PRIMARY').name()};
                    color: {self.theme_manager.get_color('BACKGROUND').name()};
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.theme_manager.get_color('HOVER_HIGHLIGHT').name()};
                }}
                QPushButton:pressed {{
                    background-color: {self.theme_manager.get_color('SECONDARY').name()};
                }}
            """)

        self.update() # Trigger repaint of the widget itself if needed

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Add any custom painting code here
        pass