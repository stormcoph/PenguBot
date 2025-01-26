from PyQt5.QtCore import pyqtProperty, QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QPushButton
from gui.widgets.colors import Colors
from gui.icons.MaskManager import MaskManager


class IconButton(QPushButton):
    def __init__(self, base_path, mask1_path, mask2_path=None, parent=None):
        super().__init__(parent)

        # Create MaskManager instances for selected and unselected states
        self.selected_mask_manager = MaskManager(
            base_path,
            mask1_path,
            mask2_path,
            width=64,
            height=64,
            color1=Colors.SELECTED_ELEMENT_1.name(),  # Use first selected color
            color2=Colors.SELECTED_ELEMENT_2.name() if mask2_path else None  # Use second selected color if dual mask
        )

        self.unselected_mask_manager = MaskManager(
            base_path,
            mask1_path,
            mask2_path,
            width=64,
            height=64,
            color1=Colors.UNSELECTED_ELEMENT_1.name(),  # Use first unselected color
            color2=Colors.UNSELECTED_ELEMENT_2.name() if mask2_path else None
            # Use second unselected color if dual mask
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
            painter.setBrush(QColor(Colors.BUTTON_SHADOW))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 10, 10)

        # Draw hover glow
        if self._hover_opacity > 0:
            painter.setOpacity(self._hover_opacity * 0.1)
            painter.setBrush(QColor(Colors.UI_ELEMENT))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), 15, 15)

        # Draw the appropriate mask manager image based on selection state
        painter.setOpacity(1.0 - self._opacity)
        unselected_image = self.unselected_mask_manager.get_result_image()
        painter.drawImage(self.rect(), unselected_image)

        painter.setOpacity(self._opacity)
        selected_image = self.selected_mask_manager.get_result_image()
        painter.drawImage(self.rect(), selected_image)