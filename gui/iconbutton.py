from PyQt5.QtCore import pyqtProperty, QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QPainter, QPixmap, QColor
from PyQt5.QtWidgets import QPushButton

class IconButton(QPushButton):
    def __init__(self, normal_icon_path, selected_icon_path, parent=None):
        super().__init__(parent)
        self.normal_pixmap = QPixmap(normal_icon_path).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.selected_pixmap = QPixmap(selected_icon_path).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setCheckable(True)
        self.setFixedSize(64, 64)
        self._opacity = 0.0
        self._hover_opacity = 0.0
        self._scale = 1.0

        # Selection animation
        self.selection_animation = QPropertyAnimation(self, b"opacity")
        self.selection_animation.setDuration(500)
        self.selection_animation.setEasingCurve(QEasingCurve.InOutCubic)

        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"hoverOpacity")
        self.hover_animation.setDuration(500)
        self.hover_animation.setEasingCurve(QEasingCurve.InOutCubic)

        # Scale animation
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(500)
        self.scale_animation.setEasingCurve(QEasingCurve.InOutBack)

        self.toggled.connect(self._handle_toggle)

        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
        """)

    def enterEvent(self, event):
        self.hover_animation.setStartValue(self._hover_opacity)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()

        self.scale_animation.setStartValue(self._scale)
        self.scale_animation.setEndValue(1.05)
        self.scale_animation.start()

    def leaveEvent(self, event):
        self.hover_animation.setStartValue(self._hover_opacity)
        self.hover_animation.setEndValue(0.0)
        self.hover_animation.start()

        self.scale_animation.setStartValue(self._scale)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()

    def _handle_toggle(self, checked):
        self.selection_animation.setStartValue(0.0 if checked else 1.0)
        self.selection_animation.setEndValue(1.0 if checked else 0.0)
        self.selection_animation.start()

    def _reset_scale(self):
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()

    # Properties for selection animation
    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    # Properties for hover animation
    def get_hover_opacity(self):
        return self._hover_opacity

    def set_hover_opacity(self, opacity):
        self._hover_opacity = opacity
        self.update()

    hoverOpacity = pyqtProperty(float, get_hover_opacity, set_hover_opacity)

    # Properties for scale animation
    def get_scale(self):
        return self._scale

    def set_scale(self, scale):
        self._scale = scale
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Apply scaling transformation
        painter.translate(self.rect().center())
        painter.scale(self._scale, self._scale)
        painter.translate(-self.rect().center())

        # Draw shadow for hover effect
        if self._hover_opacity > 0:
            painter.setOpacity(self._hover_opacity * 0.3)
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 10, 10)

        # Draw hover glow
        if self._hover_opacity > 0:
            painter.setOpacity(self._hover_opacity * 0.1)
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), 15, 15)

        # Draw icons with selection opacity
        painter.setOpacity(1.0 - self._opacity)
        painter.drawPixmap(self.rect(), self.normal_pixmap)

        painter.setOpacity(self._opacity)
        painter.drawPixmap(self.rect(), self.selected_pixmap)