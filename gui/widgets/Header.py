from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .colors import get_theme_manager

class HeaderWidget(QWidget):
    def __init__(self, title_text, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.setup_ui(title_text)
        self.theme_manager.themeChanged.connect(self.update_styles)

    def setup_ui(self, title_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)

        # Title Label
        self.title_label = QLabel(title_text)
        font = QFont("Roboto", 24, QFont.Bold)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)

        # Separator Line
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setFixedHeight(2)
        layout.addWidget(self.line)

        self.update_styles()

    def update_styles(self):
        text_color = self.theme_manager.get_color("TEXT").name()
        accent_color = self.theme_manager.get_color("ACCENT").name()
        
        self.title_label.setStyleSheet(f"color: {text_color};")
        self.line.setStyleSheet(f"background-color: {accent_color}; border: none;")
