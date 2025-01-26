import ctypes
import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget)
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QRadialGradient, QIcon, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty

from .ConfigManager import ConfigManager
from gui.widgets.colors import Colors
from .snowflake import Snowflake
from .iconbutton import IconButton
from PyQt5.QtGui import QFontDatabase, QFont
from .widgets.Aimbot import AimbotWidget
from .widgets.AI import AIWidget
from .widgets.Visual import VisualWidget
from .widgets.Config import ConfigWidget
import os


class SnowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()  # Keep this line

        # First (correct) widgets initialization
        self.widgets = {
            'aimbot_setting': AimbotWidget(self, self.config_manager),
            'AI_setting': AIWidget(self, self.config_manager),
            'visual_setting': VisualWidget(self, self.config_manager),
            'config_setting': ConfigWidget(self, self.config_manager)
        }

        self._text_opacity = 1.0

        # Create the pulsing animation
        self.text_animation = QPropertyAnimation(self, b"textOpacity")
        self.text_animation.setDuration(3000)  # 1.5 seconds for one pulse cycle
        self.text_animation.setStartValue(1.0)
        self.text_animation.setEndValue(0.5)
        self.text_animation.setLoopCount(-1)  # Infinite loop
        self.text_animation.setEasingCurve(QEasingCurve.InOutSine)

        # Make it bounce back and forth
        self.text_animation.finished.connect(self._reverse_animation)

        # Start the animation
        self.text_animation.start()

        self.snow_count = 75
        self.snowflakes = []
        self.buttons = {}

        self.setMouseTracking(True)
        self.mouse_pos = QPoint(0, 0)
        self.mouse_radius = 50

        self.setup_buttons()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_snowflakes)
        self.timer.start(16)

        # Add AimbotWidget
        """self.aimbot_widget = AimbotWidget(self)
        self.aimbot_widget.move(14+72, 0)  # Position the widget at (123, 42)
        self.aimbot_widget.resize(200, 50)  # Ensure the widget is large enough
        self.aimbot_widget.setVisible(False)  # Initially hidden
        self.aimbot_widget.setEnabled(False)"""  # Initially non-interactive

    def _reverse_animation(self):
        # Reverse the animation direction
        self.text_animation.setStartValue(self.text_animation.endValue())
        self.text_animation.setEndValue(1.0 if self.text_animation.endValue() == 0.5 else 0.5)
        self.text_animation.start()

    # Property for text opacity animation
    def get_text_opacity(self):
        return self._text_opacity

    def set_text_opacity(self, opacity):
        self._text_opacity = opacity
        self.update()  # Trigger a repaint

    textOpacity = pyqtProperty(float, get_text_opacity, set_text_opacity)

    def update_snowflakes(self):
        try:
            if self.snowflakes:
                for snowflake in self.snowflakes:
                    dx = self.mouse_pos.x() - snowflake.pos.x()
                    dy = self.mouse_pos.y() - snowflake.pos.y()
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < self.mouse_radius and distance > 0:
                        factor = (self.mouse_radius - distance) / self.mouse_radius
                        new_x = snowflake.pos.x() - dx * factor * 0.1
                        new_y = snowflake.pos.y() - dy * factor * 0.1

                        if 0 <= new_x <= self.width():
                            snowflake.pos.setX(int(new_x))
                        if -50 <= new_y <= self.height():
                            snowflake.pos.setY(int(new_y))

                    snowflake.update(self.width(), self.height())
                self.update()
        except Exception as e:
            print(f"Error updating snow: {e}")

    def initialize_snowflakes(self):
        try:
            if not self.snowflakes:
                for _ in range(self.snow_count):
                    self.snowflakes.append(Snowflake(self.width(), self.height()))
        except Exception as e:
            print(f"Error initializing snowflakes: {e}")

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
            if not self.snowflakes:
                self.initialize_snowflakes()
        except Exception as e:
            print(f"Error in resize event: {e}")

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()

    def setup_buttons(self):
        base_icon_path = os.path.join(os.path.dirname(__file__), "icons")  # Add this line

        button_configs = {
            'aimbot_setting': {
                'base': os.path.join(base_icon_path, 'aimbot_setting', 'selected.png'),  # Updated
                'mask1': os.path.join(base_icon_path, 'aimbot_setting', 'mask1.png'),  # Updated
                'position': (11, 7 + 10)
            },
            'AI_setting': {
                'base': os.path.join(base_icon_path, 'AI_setting', 'selected.png'),  # Updated
                'mask1': os.path.join(base_icon_path, 'AI_setting', 'mask1.png'),  # Updated
                'mask2': os.path.join(base_icon_path, 'AI_setting', 'mask2.png'),  # Updated
                'position': (11, 7 + 64 + 10 + 9)
            },
            'visual_setting': {
                'base': os.path.join(base_icon_path, 'visual_setting/selected.png'),
                'mask1': os.path.join(base_icon_path, 'visual_setting/mask1.png'),
                'mask2': os.path.join(base_icon_path, 'visual_setting/mask2.png'),
                'position': (11, 7 + 64 + 64 + 10 + 7 + 10)
            },
            'config_setting': {
                'base': os.path.join(base_icon_path, 'config_setting/selected.png'),
                'mask1': os.path.join(base_icon_path, 'config_setting/mask1.png'),
                'mask2': os.path.join(base_icon_path, 'config_setting/mask2.png'),
                'position': (11, 440 - 7 - 64 - 10 - 11 - 10)
            }
        }

        for name, config in button_configs.items():
            # For single mask buttons (aimbot_setting), mask2 will be None
            mask2_path = config.get('mask2', None)

            button = IconButton(
                config['base'],
                config['mask1'],
                mask2_path,
                self
            )
            button.move(*config['position'])
            button.clicked.connect(lambda checked, n=name: self.handle_button_click(n))
            self.buttons[name] = button

    def handle_button_click(self, button_name):
        # Uncheck all other buttons
        for name, button in self.buttons.items():
            if name != button_name:
                button.setChecked(False)

        # Hide all widgets
        for widget in self.widgets.values():
            widget.setVisible(False)
            widget.setEnabled(False)

        # Show the selected widget
        if button_name in self.widgets:
            self.widgets[button_name].setVisible(True)
            self.widgets[button_name].setEnabled(True)

        print(f"Button clicked: {button_name}")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(Colors.BACKGROUND))
            gradient.setColorAt(1, Colors.BACKGROUND_DARKER)

            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 15, 15)
            painter.setClipPath(path)
            painter.fillPath(path, gradient)

            if self.snowflakes:
                for snowflake in self.snowflakes:
                    if not isinstance(snowflake.pos, QPoint):
                        continue

                    dx = self.mouse_pos.x() - snowflake.pos.x()
                    dy = self.mouse_pos.y() - snowflake.pos.y()
                    distance = math.sqrt(dx * dx + dy * dy)

                    glow_radius = snowflake.size * 2
                    if distance < self.mouse_radius:
                        glow_factor = (self.mouse_radius - distance) / self.mouse_radius
                        glow_radius = snowflake.size * (2 + glow_factor * 2)

                    gradient = QRadialGradient(snowflake.pos, glow_radius)
                    base_color = Colors.SNOWFLAKE
                    color = QColor(base_color.red(), base_color.green(), base_color.blue(),
                                   int(255 * snowflake.opacity))

                    if distance < self.mouse_radius:
                        glow_color = QColor(200, 225, 255, int(255 * snowflake.opacity * glow_factor * 0.5))
                        gradient.setColorAt(0, color)
                        gradient.setColorAt(0.5, glow_color)
                        gradient.setColorAt(1, QColor(0, 0, 0, 0))
                    else:
                        gradient.setColorAt(0, color)
                        gradient.setColorAt(1, QColor(0, 0, 0, 0))

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(gradient)

                    size = max(0.1, snowflake.size * snowflake.depth)
                    painter.drawEllipse(snowflake.pos, size, size)

            panel_color = Colors.PANEL_BACKGROUND
            rectColor = QColor(panel_color.red(), panel_color.green(), panel_color.blue())
            rectColor.setAlphaF(0.92)

            left_rect = QPainterPath()
            left_rect.addRoundedRect(QRectF(7, 7, 72, self.height() - 14), 15, 15)
            painter.fillPath(left_rect, rectColor)

            right_rect = QPainterPath()
            right_rect.addRoundedRect(QRectF(86, 7, 607, self.height() - 14), 15, 15)
            painter.fillPath(right_rect, rectColor)

            font = QFont("Roboto", 12)
            font.setWeight(QFont.Medium)
            painter.setFont(font)
            font.setPointSize(12)
            text_color = Colors.TEXT
            text_color_with_opacity = QColor(text_color.red(), text_color.green(), text_color.blue())
            text_color_with_opacity.setAlphaF(self._text_opacity)
            painter.setPen(text_color_with_opacity)
            painter.drawText(9, 440 - 19, "PenguBot")

            painter.end()

        except Exception as e:
            print(f"Error in paint event: {e}")


def load_fonts():
    """Load and register the Roboto font family"""
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts', 'Roboto')
    font_files = {
        'Thin': 'Roboto-Thin.ttf',
        'Light': 'Roboto-Light.ttf',
        'Regular': 'Roboto-Regular.ttf',
        'Medium': 'Roboto-Medium.ttf',
        'Bold': 'Roboto-Bold.ttf',
        'Black': 'Roboto-Black.ttf'
    }

    loaded_fonts = {}
    for weight, filename in font_files.items():
        font_path = os.path.join(font_dir, filename)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                loaded_fonts[weight] = font_id
                print(f"Loaded Roboto {weight}")
            else:
                print(f"Failed to load Roboto {weight}")

    return loaded_fonts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PenguBot")
        self.setMinimumSize(700, 440)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Load fonts before creating widgets
        self.loaded_fonts = load_fonts()

        # Set default application font
        default_font = QFont("Roboto")
        default_font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(default_font)

        self.central_widget = SnowWidget(self)
        self.central_widget.resize(700, 440)
        self.setCentralWidget(self.central_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    myappid = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.setWindowIcon(QIcon("icons/config_setting/icon.ico"))
    window.show()
    sys.exit(app.exec_())