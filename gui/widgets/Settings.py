from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QComboBox, QSlider, QPushButton, QLineEdit, QStyleOptionSlider, QStyle,
                             QScrollArea)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont
from gui.widgets.colors import Colors


class SettingsPanelMixin:
    """Mixin class to add the dark panel background to settings components"""

    def __init__(self):
        self._min_height = 48  # Default minimum height

    def setMinimumHeight(self, height):
        self._min_height = max(height, self._min_height)
        super().setMinimumHeight(self._min_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)

        # Use settings-specific background color
        background_color = Colors.SETTINGS_BACKGROUND
        painter.fillPath(path, background_color)
        
        # Draw border
        border_color = Colors.SECTION_BORDER
        border_color.setAlphaF(0.3)
        painter.setPen(border_color)
        painter.drawPath(path)

        super().paintEvent(event)


class ScrollableSettingsWidget(QScrollArea):
    """Base class for settings widgets that need scrolling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.viewport().setStyleSheet("background: transparent;")
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(122, 162, 247, 0.5);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)


class SettingsDropdown(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(str)

    def __init__(self, label, options, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(48)
        self.setup_ui(label, options)

    def setup_ui(self, label, options):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        label = QLabel(label)
        label.setStyleSheet(f"color: {Colors.TEXT.name()}; font-size: 16px;")
        layout.addWidget(label)

        layout.addStretch()

        self.combo = QComboBox()
        self.combo.addItems(options)
        self.combo.setFixedWidth(120)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.INPUT_BACKGROUND.name()};
                border: 1px solid {Colors.SECTION_BORDER.name()};
                color: {Colors.TEXT.name()};
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 30px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.SECONDARY.name()};
                color: {Colors.TEXT.name()};
                selection-background-color: {Colors.PRIMARY.name()};
                border: none;
                outline: none;
            }}
        """)
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self.combo)

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
        self._animation = QPropertyAnimation(self, b"value", self)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setDuration(200)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValueAnimated(val)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        val = self.pixelPosToRangeValue(event.pos())
        self.setValueAnimated(val)

    def setValueAnimated(self, value):
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.start()

    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
            pos = pos.x() - sliderLength // 2
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
            pos = pos.y() - sliderLength // 2

        return QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            pos - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown)


class SettingsSlider(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, label, min_value, max_value, default_value, allow_decimals=True, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(68)
        self.allow_decimals = allow_decimals
        self.multiplier = 1000 if allow_decimals else 1
        self.setup_ui(label, min_value, max_value, default_value)

    def setup_ui(self, label, min_value, max_value, default_value):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        top_row = QHBoxLayout()
        label = QLabel(label)
        label.setStyleSheet(f"color: {Colors.TEXT.name()}; font-size: 16px;")
        top_row.addWidget(label)

        top_row.addStretch()

        self.value_input = QLineEdit(self._format_value(default_value))
        self.value_input.setFixedWidth(80)
        self.value_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {Colors.TEXT.name()};
                border: none;
                font-family: Roboto;
                font-size: 16px;
            }}
        """)
        top_row.addWidget(self.value_input)
        layout.addLayout(top_row)

        self.slider = AnimatedSlider(Qt.Horizontal)
        self.slider.setMinimum(int(min_value * self.multiplier))
        self.slider.setMaximum(int(max_value * self.multiplier))
        self.slider.setValue(int(default_value * self.multiplier))
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Colors.INPUT_BACKGROUND.name()};
                border: 1px solid {Colors.SECTION_BORDER.name()};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {Colors.TOGGLE_ACTIVE.name()};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
                box-shadow: 0 0 10px {Colors.PRIMARY.name()};
            }}
            QSlider::sub-page:horizontal {{
                background: {Colors.TOGGLE_ACTIVE.name()};
                height: 4px;
                border-radius: 2px;
                box-shadow: 0 0 10px {Colors.PRIMARY.name()};
            }}
        """)
        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self._update_value_input)
        self.value_input.returnPressed.connect(self._update_slider)
        self.slider.valueChanged.connect(self._emit_value)

    def _format_value(self, value):
        if self.allow_decimals:
            return f"{value:.3f}"
        return str(int(value))

    def _update_value_input(self, value):
        displayed_value = value / self.multiplier if self.allow_decimals else value
        self.value_input.setText(self._format_value(displayed_value))

    def _update_slider(self):
        try:
            value = float(self.value_input.text())
            slider_value = int(value * self.multiplier if self.allow_decimals else value)
            self.slider.setValueAnimated(slider_value)
        except ValueError:
            self._update_value_input(self.slider.value() / self.multiplier)

    def _emit_value(self):
        value = self.get_value()
        self.valueChanged.emit(value)

    def get_value(self):
        return self.slider.value() / self.multiplier if self.allow_decimals else self.slider.value()

    def set_value(self, value):
        slider_value = int(value * self.multiplier) if self.allow_decimals else int(value)
        self.slider.setValue(slider_value)


class SettingsBoolean(SettingsPanelMixin, QWidget):
    valueChanged = pyqtSignal(bool)

    def __init__(self, label, default_value=False, parent=None):
        super().__init__()
        QWidget.__init__(self, parent)
        self.setMinimumHeight(48)
        self.setup_ui(label, default_value)

    def setup_ui(self, label, default_value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        label = QLabel(label)
        label.setStyleSheet(f"color: {Colors.TEXT.name()}; font-size: 16px;")
        layout.addWidget(label)

        layout.addStretch()

        self.toggle = ToggleButton(default_value)
        self.toggle.toggled.connect(self.valueChanged.emit)
        layout.addWidget(self.toggle)

    def get_value(self):
        return self.toggle.isChecked()

    def set_value(self, value):
        self.toggle.setChecked(value)


class ToggleButton(QPushButton):
    def __init__(self, default_value=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(default_value)
        self.setFixedSize(24, 24)
        self._glow_opacity = 1.0 if default_value else 0.0

        self.animation = QPropertyAnimation(self, b"glowOpacity")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.toggled.connect(self._handle_toggle)

    def _handle_toggle(self, checked):
        self.animation.setStartValue(self._glow_opacity)
        self.animation.setEndValue(1.0 if checked else 0.0)
        self.animation.start()

    @pyqtProperty(float)
    def glowOpacity(self):
        return self._glow_opacity

    @glowOpacity.setter
    def glowOpacity(self, value):
        self._glow_opacity = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(2, 2, 20, 20, 5, 5)

        if self.isChecked():
            glow_color = Colors.TOGGLE_ACTIVE
            glow_color.setAlphaF(2.6 * self._glow_opacity)
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_color)
            painter.drawPath(path)

            active_color = Colors.ACCENT
            active_color.setAlphaF(self._glow_opacity)
            painter.setBrush(active_color)
            painter.drawPath(path)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Colors.TOGGLE_INACTIVE)
            painter.drawPath(path)
