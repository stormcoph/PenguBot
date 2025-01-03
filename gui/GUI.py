import ctypes
import sys
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QLabel, QVBoxLayout, QWidget)
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QRadialGradient, QPixmap, QIcon, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from snowflake import Snowflake
from colors import Colors
from iconbutton import IconButton


class SnowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background: #1A1B26;
            border-radius: 25px;
        """)

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
        button_configs = {
            'aimbot_setting': (11, 7 + 10),
            'AI_setting': (11, 7 + 64 + 10 + 9),
            'visual_setting': (11, 7+64+64+10+7+10),
            'about_setting': (11, 440 - 7 - 64 - 10 -11 - 10)
        }

        for name, (x, y) in button_configs.items():
            normal_path = f"icons/{name}/unselected.png"
            selected_path = f"icons/{name}/selected.png"

            button = IconButton(normal_path, selected_path, self)
            button.move(x, y)
            button.clicked.connect(lambda checked, n=name: self.handle_button_click(n))
            self.buttons[name] = button

    def handle_button_click(self, button_name):
        # Uncheck all other buttons
        for name, button in self.buttons.items():
            if name != button_name:
                button.setChecked(False)
        # Handle the specific button click
        print(f"Button clicked: {button_name}")
        # Add your specific button handling logic here

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Create gradient background
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor("#1A1B26"))
            gradient.setColorAt(1, QColor("#16171F"))  # Slightly darker shade

            # Draw background with rounded corners
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 15, 15)
            painter.setClipPath(path)
            painter.fillPath(path, gradient)

            if self.snowflakes:
                for snowflake in self.snowflakes:
                    if not isinstance(snowflake.pos, QPoint):
                        continue

                    # Calculate distance to mouse
                    dx = self.mouse_pos.x() - snowflake.pos.x()
                    dy = self.mouse_pos.y() - snowflake.pos.y()
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Add glow effect when near mouse
                    glow_radius = snowflake.size * 2
                    if distance < self.mouse_radius:
                        glow_factor = (self.mouse_radius - distance) / self.mouse_radius
                        glow_radius = snowflake.size * (2 + glow_factor * 2)

                    gradient = QRadialGradient(snowflake.pos, glow_radius)
                    color = QColor(255, 255, 255, int(255 * snowflake.opacity))

                    # Add subtle blue tint to the glow
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

            # Draw rectangles
            rectColor = QColor("#0B0C12")
            rectColor.setAlphaF(0.92)

            left_rect = QPainterPath()
            left_rect.addRoundedRect(QRectF(7, 7, 72, self.height() - 14), 15, 15)
            painter.fillPath(left_rect, rectColor)

            right_rect = QPainterPath()
            right_rect.addRoundedRect(QRectF(86, 7, 607, self.height() - 14), 15, 15)
            painter.fillPath(right_rect, rectColor)

            # Draw "PenguBot" text
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            text_color = QColor("#C0CAF5")
            text_color.setAlphaF(self._text_opacity)  # Apply the pulsing opacity
            painter.setPen(text_color)
            painter.drawText(9, 440 - 19, "PenguBot")

            painter.end()

        except Exception as e:
            print(f"Error in paint event: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PenguBot")
        self.setMinimumSize(700, 440)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.central_widget = SnowWidget(self)
        self.central_widget.resize(700, 440)
        self.setCentralWidget(self.central_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    myappid = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.setWindowIcon(QIcon("icons/about_setting/selected.ico"))
    window.show()
    sys.exit(app.exec_())