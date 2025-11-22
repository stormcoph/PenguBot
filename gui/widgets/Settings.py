from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QComboBox, QSlider, QPushButton, QLineEdit, QStyleOptionSlider, QStyle,
                             QScrollArea)
# Ensure QPointF is imported here
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QPen # Added QPen
from .colors import get_theme_manager # Use theme manager


class SettingsPanelMixin:
    """Mixin class to add the dark panel background to settings components"""

    def __init__(self):
        self._min_height = 52  # Default minimum height (Increased)
        self.theme_manager = get_theme_manager() # Add theme manager instance

    def setMinimumHeight(self, height):
        self._min_height = max(height, self._min_height)
        # Use QWidget's setMinimumHeight if super() refers to QObject
        if hasattr(super(), 'setMinimumHeight'):
            super().setMinimumHeight(self._min_height)
        else:
             # Fallback for direct QWidget inheritance if mixin order changes
             QWidget.setMinimumHeight(self, self._min_height)


    def paintEvent(self, event):
        # This paintEvent is primarily for the background.
        # Subclasses should call super().paintEvent(event) if they override it
        # and want this background painting behavior.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)

        # Use settings-specific background color
        background_color = self.theme_manager.get_color("SETTINGS_BACKGROUND")
        painter.fillPath(path, background_color)

        # Let the default QWidget paint event run (important for stylesheets, etc.)
        # Check if superclass has paintEvent before calling
        if hasattr(super(), 'paintEvent'):
             super().paintEvent(event)


class ScrollableSettingsWidget(QScrollArea):
    """Base class for settings widgets that need scrolling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Make the scroll area itself transparent
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        # Make the viewport transparent so the parent widget's background shows through
        self.viewport().setStyleSheet("background: transparent;")
        self.update_styles() # Apply initial theme to scrollbar
        self.theme_manager.themeChanged.connect(self.update_styles) # Connect to theme changes

    def update_styles(self):
        """Update scrollbar style based on the current theme."""
        # Update the scrollbar stylesheet specifically
        self.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: transparent; /* Scrollbar track background */
                width: 8px; /* Slightly wider */
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme_manager.get_color("PRIMARY", alpha=128).name()};
                min-height: 25px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.theme_manager.get_color("PRIMARY").name()}; /* Slightly brighter/more opaque on hover */
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)


class SettingsDropdown(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(str)

    def __init__(self, label, options, parent=None):
        super().__init__() # Calls SettingsPanelMixin.__init__
        QWidget.__init__(self, parent) # Explicitly call QWidget init
        self.setMinimumHeight(70) # Increased height
        # theme_manager is inherited from SettingsPanelMixin
        self.setup_ui(label, options)
        self.theme_manager.themeChanged.connect(self.update_styles) # Connect to theme changes

    def setup_ui(self, label, options):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        self.label_widget = QLabel(label) # Store label reference
        layout.addWidget(self.label_widget)

        layout.addStretch()

        self.combo = QComboBox()
        self.combo.addItems(options)
        self.combo.setFixedWidth(120)
        self.update_styles() # Apply initial theme
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self.combo)

    def update_styles(self):
        """Update styles for the dropdown based on the current theme."""
        # Update label style
        self.label_widget.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-size: 16px;")

        # Update combo box style
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme_manager.get_color('SECONDARY').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()}; /* Add subtle border */
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 30px;
                font-size: 14px; /* Slightly smaller font */
            }}
            QComboBox:hover {{
                border: 1px solid {self.theme_manager.get_color('PRIMARY').name()};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px; /* Slightly wider arrow area */
                border-left-width: 1px;
                border-left-color: {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-left-style: solid; /* visually separate the arrow */
                border-top-right-radius: 5px; /* same radius */
                border-bottom-right-radius: 5px;
            }}
            QComboBox::down-arrow {{
                 /* Using a simple character for the arrow */
                 /* Consider using an SVG icon for better results if possible */
                 /* image: url(:/icons/down_arrow.svg); */
                 width: 10px; /* Adjust size as needed */
                 height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.theme_manager.get_color('SECONDARY').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                selection-background-color: {self.theme_manager.get_color('PRIMARY').name()};
                selection-color: {self.theme_manager.get_color('TEXT').name()}; /* Ensure text is readable on selection */
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                outline: none;
            }}
        """)
        # Update panel background (inherited)
        self.update()

    # Override paintEvent to ensure mixin's paintEvent is called correctly
    def paintEvent(self, event):
        # SettingsPanelMixin handles the background painting
        super().paintEvent(event)


    def _on_index_changed(self):
        self.valueChanged.emit(self.get_value())

    def get_value(self):
        return self.combo.currentText()

    def set_value(self, value):
        index = self.combo.findText(value)
        if index >= 0:
            self.combo.setCurrentIndex(index)


class AnimatedSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Note: This base slider doesn't need theme manager directly
        self._animation = QPropertyAnimation(self, b"value", self)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setDuration(200)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Correctly calculate value based on click position for horizontal sliders
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            available = self.style().pixelMetric(QStyle.PM_SliderSpaceAvailable, opt, self)
            x = event.pos().x()
            if opt.direction == Qt.RightToLeft:
                x = self.width() - x
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x - opt.rect.x(), available, opt.upsideDown)

            if val != self.value():
                self.setValueAnimated(val)
                event.accept()
                return # Prevent default handling which might interfere
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
         # Correctly calculate value based on drag position for horizontal sliders
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        available = self.style().pixelMetric(QStyle.PM_SliderSpaceAvailable, opt, self)
        x = event.pos().x()
        if opt.direction == Qt.RightToLeft:
            x = self.width() - x
        val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x - opt.rect.x(), available, opt.upsideDown)

        self.setValueAnimated(val) # Use animated set value
        # super().mouseMoveEvent(event) # Don't call super, we handled it


    def setValueAnimated(self, value):
        # Clamp value to range
        value = max(self.minimum(), min(self.maximum(), value))
        if value == self.value():
            return # No change needed
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.start()

    # Keep pixelPosToRangeValue for potential internal use, but mouse events are handled above
    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
            pos_val = pos.x() - sliderLength // 2
        else: # Vertical (not used here but for completeness)
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
            pos_val = pos.y() - sliderLength // 2

        return QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            pos_val - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown)


class SettingsSlider(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, label, min_value, max_value, default_value, allow_decimals=True, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(74) # Increased height
        # theme_manager is inherited from SettingsPanelMixin
        self.allow_decimals = allow_decimals
        self.multiplier = 1000 if allow_decimals else 1
        self.setup_ui(label, min_value, max_value, default_value)
        self.theme_manager.themeChanged.connect(self.update_styles) # Connect to theme changes

    def setup_ui(self, label, min_value, max_value, default_value):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6) # Add some spacing

        top_row = QHBoxLayout()
        self.label_widget = QLabel(label) # Store label reference
        top_row.addWidget(self.label_widget)

        top_row.addStretch()

        self.value_input = QLineEdit(self._format_value(default_value))
        self.value_input.setFixedWidth(80)
        self.value_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_row.addWidget(self.value_input)
        layout.addLayout(top_row)

        self.slider = AnimatedSlider(Qt.Horizontal)
        self.slider.setMinimum(int(min_value * self.multiplier))
        self.slider.setMaximum(int(max_value * self.multiplier))
        self.slider.setValue(int(default_value * self.multiplier))
        layout.addWidget(self.slider)

        self.update_styles() # Apply initial theme

        self.slider.valueChanged.connect(self._update_value_input)
        self.value_input.returnPressed.connect(self._update_slider)
        self.slider.valueChanged.connect(self._emit_value)

    def update_styles(self):
        """Update styles for the slider and input based on the current theme."""
        # Update label style
        self.label_widget.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-size: 16px;")

        # Update value input style
        self.value_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme_manager.get_color('INPUT_BACKGROUND').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-radius: 4px;
                font-family: Roboto;
                font-size: 16px;
                padding: 4px 8px; /* Slightly more padding */
            }}
            QLineEdit:hover {{
                 border: 1px solid {self.theme_manager.get_color('HOVER_HIGHLIGHT').name()};
            }}
            QLineEdit:focus {{
                 border: 1px solid {self.theme_manager.get_color('ACCENT').name()}; /* Use Accent for focus */
            }}
        """)

        # Update slider style
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.theme_manager.get_color('SECONDARY').name()};
                height: 6px; /* Slightly thicker groove */
                border-radius: 3px;
                margin: 0 5px; /* Adjust margin slightly */
            }}
            QSlider::handle:horizontal {{
                background: {self.theme_manager.get_color('ACCENT').name()};
                border: 1px solid {self.theme_manager.get_color('SECONDARY').name()}; /* Add border for definition */
                width: 18px; /* Slightly larger handle */
                height: 18px;
                margin: -7px 0; /* Adjust vertical centering */
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                 background: {self.theme_manager.get_color('PRIMARY').name()}; /* Use Primary on hover */
                 border: 1px solid {self.theme_manager.get_color('ACCENT').name()};
            }}
            QSlider::sub-page:horizontal {{
                background: {self.theme_manager.get_color('PRIMARY').name()};
                height: 6px; /* Match groove height */
                border-radius: 3px;
            }}
        """)
        # Update panel background (inherited)
        self.update()

    # Override paintEvent to ensure mixin's paintEvent is called correctly
    def paintEvent(self, event):
        super().paintEvent(event) # Calls SettingsPanelMixin.paintEvent

    def _format_value(self, value):
        if self.allow_decimals:
            # Format to 3 decimal places, but remove trailing zeros and the decimal point if it becomes integer
            formatted = f"{value:.3f}".rstrip('0').rstrip('.')
            return formatted if formatted != '-0' else '0' # Handle case of -0.000
        return str(int(value))

    def _update_value_input(self, value):
        displayed_value = value / self.multiplier
        self.value_input.setText(self._format_value(displayed_value))

    def _update_slider(self):
        try:
            value = float(self.value_input.text())
            slider_value = int(value * self.multiplier)
            # Clamp value to slider range before setting
            slider_value = max(self.slider.minimum(), min(self.slider.maximum(), slider_value))
            self.slider.setValueAnimated(slider_value)
        except ValueError:
            # If input is invalid, reset it to the current slider value
            self._update_value_input(self.slider.value())

    def _emit_value(self):
        value = self.get_value()
        self.valueChanged.emit(value)

    def get_value(self):
        return self.slider.value() / self.multiplier

    def set_value(self, value):
        slider_value = int(value * self.multiplier)
        self.slider.setValue(slider_value) # Use non-animated set for external updates


class SettingsBoolean(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(bool)

    def __init__(self, label, default_value=False, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(56) # Increased height
        # theme_manager is inherited from SettingsPanelMixin
        self.setup_ui(label, default_value)
        self.theme_manager.themeChanged.connect(self.update_styles) # Connect to theme changes

    def setup_ui(self, label, default_value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        self.label_widget = QLabel(label) # Store label reference
        layout.addWidget(self.label_widget)

        layout.addStretch()

        self.toggle = ToggleButton(default_value)
        self.toggle.toggled.connect(self.valueChanged.emit)
        layout.addWidget(self.toggle)

        self.update_styles() # Apply initial theme

    def update_styles(self):
        """Update styles for the boolean setting based on the current theme."""
        # Update label style
        self.label_widget.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-size: 16px;")

        # Update toggle button style
        self.toggle.update_styles()
        # Update panel background (inherited)
        self.update()

    # Override paintEvent to ensure mixin's paintEvent is called correctly
    def paintEvent(self, event):
        super().paintEvent(event) # Calls SettingsPanelMixin.paintEvent

    def get_value(self):
        # Use the toggle button's isChecked method
        return self.toggle.isChecked()

    def set_value(self, value):
        # Use the toggle button's setChecked method
        self.toggle.setChecked(bool(value))


class ToggleButton(QPushButton):
    def __init__(self, default_value=False, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.setCheckable(True)
        self.setChecked(default_value)
        self.setFixedSize(40, 24) # Make it wider like a typical toggle
        self.setCursor(Qt.PointingHandCursor) # Change cursor on hover
        self._glow_opacity = 1.0 if default_value else 0.0
        self._circle_pos = 18 if default_value else 2 # Position of the inner circle

        # Animation for circle position
        self.pos_animation = QPropertyAnimation(self, b"circlePosition")
        self.pos_animation.setDuration(150) # Faster animation
        self.pos_animation.setEasingCurve(QEasingCurve.InOutSine)

        # Animation for glow (optional, can be simplified)
        self.glow_animation = QPropertyAnimation(self, b"glowOpacity")
        self.glow_animation.setDuration(150)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)

        self.toggled.connect(self._handle_toggle)
        self.setStyleSheet("background: transparent; border: none;") # Remove default button styling
        self.update_styles() # Apply initial theme

    def update_styles(self):
        self.update() # Trigger repaint which uses themed colors

    def _handle_toggle(self, checked):
        self.pos_animation.setStartValue(self._circle_pos)
        self.pos_animation.setEndValue(18 if checked else 2)
        self.pos_animation.start()

        self.glow_animation.setStartValue(self._glow_opacity)
        self.glow_animation.setEndValue(1.0 if checked else 0.0)
        self.glow_animation.start()

    @pyqtProperty(float)
    def glowOpacity(self):
        return self._glow_opacity

    @glowOpacity.setter
    def glowOpacity(self, value):
        self._glow_opacity = value
        # self.update() # Repaint is triggered by circlePosition animation

    @pyqtProperty(int)
    def circlePosition(self):
        return self._circle_pos

    @circlePosition.setter
    def circlePosition(self, value):
        self._circle_pos = value
        self.update() # Repaint when circle position changes

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define dimensions
        rect = QRectF(0, 0, self.width(), self.height())
        pen_width = 1.5
        radius = rect.height() / 2 - pen_width

        # Background color based on state
        bg_color = self.theme_manager.get_color("TOGGLE_ACTIVE") if self.isChecked() else self.theme_manager.get_color("TOGGLE_INACTIVE")
        # Interpolate background color during animation
        inactive_color = self.theme_manager.get_color("TOGGLE_INACTIVE")
        active_color = self.theme_manager.get_color("TOGGLE_ACTIVE")
        interp_factor = (self._circle_pos - 2) / (18 - 2) # Normalize position to 0-1
        r = int(inactive_color.red() + (active_color.red() - inactive_color.red()) * interp_factor)
        g = int(inactive_color.green() + (active_color.green() - inactive_color.green()) * interp_factor)
        b = int(inactive_color.blue() + (active_color.blue() - inactive_color.blue()) * interp_factor)
        current_bg_color = QColor(r, g, b)

        painter.setBrush(current_bg_color)
        painter.setPen(Qt.NoPen) # No border for the background track
        painter.drawRoundedRect(rect, radius + pen_width, radius + pen_width)

        # Draw the handle (circle)
        handle_color = self.theme_manager.get_color("TEXT") # Use text color for handle
        handle_border_color = self.theme_manager.get_color("BACKGROUND") # Border matching background
        painter.setBrush(handle_color)
        painter.setPen(QPen(handle_border_color, 0.5)) # Add subtle border to handle

        circle_y = rect.center().y()
        circle_radius = radius - 1.5 # Slightly smaller circle to account for border
        # Use QPointF here
        painter.drawEllipse(QPointF(self._circle_pos + circle_radius, circle_y), circle_radius, circle_radius)


class KeybindButton(QPushButton):
    keybindChanged = pyqtSignal(int)

    def __init__(self, default_value=0, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.current_key = default_value
        self.is_listening = False
        self.setText(self._get_key_name(self.current_key))
        self.clicked.connect(self._toggle_listening)
        self.theme_manager.themeChanged.connect(self.update_styles)
        self.update_styles()

    def _get_key_name(self, vk_code):
        if vk_code == 0x01: return "Left Click"
        if vk_code == 0x02: return "Right Click"
        if vk_code == 0x04: return "Middle Click"
        if vk_code == 0x05: return "Mouse 4"
        if vk_code == 0x06: return "Mouse 5"
        if vk_code == 0x10: return "Shift"
        if vk_code == 0x11: return "Ctrl"
        if vk_code == 0x12: return "Alt"
        
        # Basic mapping for common keys
        if 0x41 <= vk_code <= 0x5A: return chr(vk_code) # A-Z
        if 0x30 <= vk_code <= 0x39: return chr(vk_code) # 0-9
        
        return f"Key {vk_code}"

    def _toggle_listening(self):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.setText("Press any key...")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme_manager.get_color('ACCENT').name()};
                    color: {self.theme_manager.get_color('TEXT').name()};
                    border: 1px solid {self.theme_manager.get_color('ACCENT').name()};
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-family: Roboto;
                    font-size: 14px;
                }}
            """)
        else:
            self.setText(self._get_key_name(self.current_key))
            self.update_styles()

    def update_styles(self):
        if self.is_listening: return
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme_manager.get_color('SECONDARY').name()};
                color: {self.theme_manager.get_color('TEXT').name()};
                border: 1px solid {self.theme_manager.get_color('SECTION_BORDER').name()};
                border-radius: 4px;
                padding: 5px 10px;
                font-family: Roboto;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border: 1px solid {self.theme_manager.get_color('PRIMARY').name()};
            }}
        """)

    def keyPressEvent(self, event):
        if self.is_listening:
            key = event.nativeVirtualKey()
            if key > 0:
                self.current_key = key
                self.keybindChanged.emit(key)
                self._toggle_listening()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.is_listening:
            button = event.button()
            vk = 0
            if button == Qt.LeftButton: vk = 0x01
            elif button == Qt.RightButton: vk = 0x02
            elif button == Qt.MiddleButton: vk = 0x04
            elif button == Qt.XButton1: vk = 0x05
            elif button == Qt.XButton2: vk = 0x06
            
            if vk > 0:
                self.current_key = vk
                self.keybindChanged.emit(vk)
                self._toggle_listening()
        else:
            super().mousePressEvent(event)

    def get_value(self):
        return self.current_key

    def set_value(self, value):
        self.current_key = int(value)
        if not self.is_listening:
            self.setText(self._get_key_name(self.current_key))


class SettingsKeybind(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, label, default_value=0x02, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(60)
        self.setup_ui(label, default_value)
        self.theme_manager.themeChanged.connect(self.update_styles)

    def setup_ui(self, label, default_value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        self.label_widget = QLabel(label)
        layout.addWidget(self.label_widget)

        layout.addStretch()

        self.keybind_btn = KeybindButton(default_value)
        self.keybind_btn.setFixedWidth(120)
        self.keybind_btn.keybindChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.keybind_btn)

        self.update_styles()

    def update_styles(self):
        self.label_widget.setStyleSheet(f"color: {self.theme_manager.get_color('TEXT').name()}; font-size: 16px;")
        self.keybind_btn.update_styles()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

    def get_value(self):
        return self.keybind_btn.get_value()

    def set_value(self, value):
        self.keybind_btn.set_value(value)
