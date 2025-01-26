from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget


class MaskManager(QWidget):
    def __init__(self, base_image_path, mask1_path, mask2_path=None, width=None, height=None, color1=None, color2=None):
        super().__init__()

        # Load base images
        self.base_image = QImage(base_image_path)
        self.mask1 = QImage(mask1_path)
        self.mask2 = QImage(mask2_path) if mask2_path else None
        self.using_two_masks = mask2_path is not None

        # Resize if width and height are provided
        if width and height:
            self.base_image = self.base_image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.mask1 = self.mask1.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.using_two_masks:
                self.mask2 = self.mask2.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Initialize result image
        self.result = QImage(self.base_image.size(), QImage.Format_ARGB32)

        # Set default colors or use provided colors
        self.color1 = QColor(color1) if color1 else QColor(255, 0, 0)  # Default red
        self.color2 = QColor(color2) if color2 and self.using_two_masks else None  # Only set color2 if using two masks

        # Initial color update
        self.update_colors()

    def set_color1(self, color):
        """Set first color and update the image"""
        self.color1 = QColor(color)
        self.update_colors()

    def set_color2(self, color):
        """Set second color and update the image"""
        if self.using_two_masks:
            self.color2 = QColor(color)
            self.update_colors()

    def get_result_image(self):
        """Return the resulting QImage"""
        return self.result

    def update_colors(self):
        """Update the image with current colors"""
        self.result.fill(Qt.transparent)

        # If using two masks, fill with color2 first
        if self.using_two_masks and self.color2:
            self.result.fill(self.color2)

        # Apply color1 with mask1
        colored_mask1 = QImage(self.base_image.size(), QImage.Format_ARGB32)
        colored_mask1.fill(self.color1)

        painter = QPainter(self.result)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply mask1
        mask1_painter = QPainter(colored_mask1)
        mask1_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        mask1_painter.drawImage(0, 0, self.mask1)
        mask1_painter.end()

        painter.drawImage(0, 0, colored_mask1)

        # Apply the base image mask
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawImage(0, 0, self.base_image)

        painter.end()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.result)