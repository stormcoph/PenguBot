import ctypes
import sys
import math
import os

# Consolidate PyQt5 imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QGraphicsOpacityEffect)
from PyQt5.QtGui import (QColor, QPainter, QPainterPath, QRadialGradient, QIcon,
                         QLinearGradient, QFontDatabase, QFont)
from PyQt5.QtCore import (Qt, QTimer, QPoint, QRectF, QPropertyAnimation, QEasingCurve,
                          pyqtProperty, pyqtSlot, QSequentialAnimationGroup, QParallelAnimationGroup)

from .ConfigManager import ConfigManager
# Import the theme manager function from the correct path
from .widgets.colors import get_theme_manager
from .iconbutton import IconButton
from .widgets.Aimbot import AimbotWidget
from .widgets.AI import AIWidget
from .widgets.Visual import VisualWidget
from .widgets.Config import ConfigWidget
from .effects import SnowEffect, RainEffect, MatrixEffect, ParticlesEffect, StarfieldEffect, GradientWaveEffect


class EffectsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        # Initialize Theme Manager with Config Manager *before* creating widgets that might use it
        self.theme_manager = get_theme_manager(self.config_manager)

        # Now initialize widgets (they can safely call get_theme_manager())
        self.widgets = {
            'aimbot_setting': AimbotWidget(self, self.config_manager),
            'AI_setting': AIWidget(self, self.config_manager),
            'visual_setting': VisualWidget(self, self.config_manager),
            'config_setting': ConfigWidget(self, self.config_manager)
        }

        self._text_opacity = 1.0
        
        # Get initial effect setting
        self.current_effect_name = self.config_manager.get("Visual.background_effect", "Snow")
        # Handle legacy boolean setting if present
        if self.config_manager.get("Visual.snow_effect", True) is False and self.current_effect_name == "Snow":
             self.current_effect_name = "None"
             
        print(f"Initial effect setting: {self.current_effect_name}")

        self.effect_classes = {
            "Snow": SnowEffect,
            "Rain": RainEffect,
            "Matrix": MatrixEffect,
            "Particles": ParticlesEffect,
            "Starfield": StarfieldEffect,
            "Gradient Wave": GradientWaveEffect
        }
        self.current_effect = None
        self.initialize_effect(self.current_effect_name)

        # --- Create the pulsing animation using QSequentialAnimationGroup ---
        self.text_anim_group = QSequentialAnimationGroup(self)
        self.text_anim_group.setLoopCount(-1) # Loop indefinitely

        # Animation part 1: Fade out
        anim_out = QPropertyAnimation(self, b"textOpacity", self)
        anim_out.setDuration(1500) # Half of the original duration
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.5)
        anim_out.setEasingCurve(QEasingCurve.InOutSine)
        self.text_anim_group.addAnimation(anim_out)

        # Animation part 2: Fade in
        anim_in = QPropertyAnimation(self, b"textOpacity", self)
        anim_in.setDuration(1500) # Half of the original duration
        anim_in.setStartValue(0.5)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.InOutSine)
        self.text_anim_group.addAnimation(anim_in)

        # Start the animation group
        self.text_anim_group.start()
        # --- End of animation setup ---

        self.buttons = {}

        self.setMouseTracking(True)
        self.mouse_pos = QPoint(0, 0)
        self.mouse_radius = 50

        self.setup_buttons()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_effects)
        self.timer.start(16)

        # Connect theme changed signal to update styles
        self.theme_manager.themeChanged.connect(self.update_widget_styles)
        
        # Connect signal from VisualWidget for immediate effect updates
        self.widgets['visual_setting'].effectChanged.connect(self.set_effect)
        

    # Property for text opacity animation
    def get_text_opacity(self):
        return self._text_opacity

    def set_text_opacity(self, opacity):
        self._text_opacity = opacity
        self.update()  # Trigger a repaint

    textOpacity = pyqtProperty(float, get_text_opacity, set_text_opacity)

    def set_effect(self, effect_name):
        """Switch background effect immediately"""
        print(f"Effect switched to: {effect_name}")
        if effect_name == self.current_effect_name:
            return  # No change needed
        
        self.current_effect_name = effect_name
        self.initialize_effect(effect_name)
        self.update()

    def initialize_effect(self, effect_name):
        if effect_name in self.effect_classes:
            try:
                self.current_effect = self.effect_classes[effect_name](self.width(), self.height(), self.theme_manager)
            except Exception as e:
                print(f"Error initializing effect {effect_name}: {e}")
                self.current_effect = None
        else:
            self.current_effect = None

    def update_effects(self):
        try:
            if self.current_effect:
                self.current_effect.update(self.width(), self.height(), self.mouse_pos)
            self.update()
        except Exception as e:
            print(f"Error updating effect: {e}")

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
            if self.current_effect:
                self.current_effect.update(self.width(), self.height())
        except Exception as e:
            print(f"Error in resize event: {e}")

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()

    def setup_buttons(self):
        base_icon_path = os.path.join(os.path.dirname(__file__), "icons")

        button_configs = {
            'aimbot_setting': {
                'base': os.path.join(base_icon_path, 'aimbot_setting', 'selected.png'),
                'mask1': os.path.join(base_icon_path, 'aimbot_setting', 'mask1.png'),
                'position': (11, 7 + 10)
            },
            'AI_setting': {
                'base': os.path.join(base_icon_path, 'AI_setting', 'selected.png'),
                'mask1': os.path.join(base_icon_path, 'AI_setting', 'mask1.png'),
                'mask2': os.path.join(base_icon_path, 'AI_setting', 'mask2.png'),
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
        self.update_button_styles()

    def handle_button_click(self, button_name):
        for name, button in self.buttons.items():
            if name != button_name:
                button.setChecked(False)

        for widget in self.widgets.values():
            widget.setVisible(False)
            widget.setEnabled(False)

        if button_name in self.widgets:
            target_widget = self.widgets[button_name]
            target_widget.setVisible(True)
            target_widget.setEnabled(True)
            if hasattr(target_widget, '_update_styles'):
                target_widget._update_styles()
            
            # Entry Animation
            # 1. Opacity Fade-In
            opacity_effect = QGraphicsOpacityEffect(target_widget)
            target_widget.setGraphicsEffect(opacity_effect)
            
            anim_opacity = QPropertyAnimation(opacity_effect, b"opacity")
            anim_opacity.setDuration(300)
            anim_opacity.setStartValue(0.0)
            anim_opacity.setEndValue(1.0)
            anim_opacity.setEasingCurve(QEasingCurve.OutCubic)
            
            # 2. Slide Up (Geometry)
            # We need to keep the original position, so let's get it
            original_pos = QPoint(86, 7) # Hardcoded based on init, or we could read it
            start_pos = QPoint(86, 27) # Start slightly lower
            
            anim_pos = QPropertyAnimation(target_widget, b"pos")
            anim_pos.setDuration(300)
            anim_pos.setStartValue(start_pos)
            anim_pos.setEndValue(original_pos)
            anim_pos.setEasingCurve(QEasingCurve.OutCubic)
            
            # Group animations
            self.entry_anim_group = QParallelAnimationGroup(self)
            self.entry_anim_group.addAnimation(anim_opacity)
            self.entry_anim_group.addAnimation(anim_pos)
            self.entry_anim_group.start()

        print(f"Button clicked: {button_name}")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, self.theme_manager.get_color("BACKGROUND"))
            gradient.setColorAt(1, self.theme_manager.get_color("BACKGROUND_DARKER"))

            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 15, 15)
            painter.setClipPath(path)
            painter.fillPath(path, gradient)

            # Draw current effect
            if self.current_effect:
                self.current_effect.draw(painter)

            panel_color = self.theme_manager.get_color("PANEL_BACKGROUND")
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
            text_color = self.theme_manager.get_color("TEXT")
            text_color_with_opacity = QColor(text_color.red(), text_color.green(), text_color.blue())
            text_color_with_opacity.setAlphaF(self._text_opacity)
            painter.setPen(text_color_with_opacity)
            painter.drawText(9, 440 - 19, "PenguBot")

            painter.end()

        except Exception as e:
            print(f"Error in paint event: {e}")

    @pyqtSlot()
    def update_widget_styles(self):
        """Update styles of child widgets when theme changes."""
        print("EffectsWidget updating styles...") # Debug print
        self.update_button_styles()

        for widget in self.widgets.values():
            if hasattr(widget, '_update_styles'):
                 widget._update_styles()

        self.update()

    def update_button_styles(self):
         """Updates the theme colors for all icon buttons."""
         for button in self.buttons.values():
             if hasattr(button, 'update_theme_colors'):
                 button.update_theme_colors()


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

        self.central_widget = EffectsWidget(self)
        self.central_widget.resize(700, 440)
        self.setCentralWidget(self.central_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    myappid = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.setWindowIcon(QIcon("icons/config_setting/icon.ico")) # Consider making icon path relative/themed
    window.show()
    sys.exit(app.exec_())