import math
import random
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty

class Snowflake:
    def __init__(self, width, height):
        padding = 15
        self.pos = QPoint(
            random.randint(padding, width - padding),
            random.randint(-50, height)
        )
        self.speed = random.uniform(0.5, 4.0)
        self.amplitude = random.uniform(1.0, 4.0)
        self.size = random.uniform(1.5, 6.0)
        self.offset = random.uniform(0, 2 * math.pi)
        self.wave_speed = random.uniform(0.01, 0.04)
        self.opacity = random.uniform(0.3, 1.0)
        self.fade_speed = random.uniform(0.005, 0.02)
        self.fading_in = random.choice([True, False])
        self.depth = random.uniform(0.5, 1.5)

    def update(self, width, height):
        try:
            # Update vertical position with depth-based speed
            new_y = self.pos.y() + self.speed * self.depth

            # Update horizontal wave movement
            self.offset += self.wave_speed
            new_x = self.pos.x() + math.sin(self.offset) * (self.amplitude / self.depth)

            padding = 15
            if new_x < padding or new_x > width - padding:
                self.reset(width, height)
            else:
                self.pos.setX(int(new_x))

            if new_y > height - padding:
                self.reset(width, height)
            else:
                self.pos.setY(int(new_y))

            # Update opacity with smoother transitions
            if self.fading_in:
                self.opacity = min(1.0, self.opacity + self.fade_speed)
                if self.opacity >= 1.0:
                    self.fading_in = False
            else:
                self.opacity = max(0.3, self.opacity - self.fade_speed)
                if self.opacity <= 0.3:
                    self.fading_in = True

        except Exception as e:
            print(f"Error updating snowflake: {e}")
            self.reset(width, height)

    def reset(self, width, height):
        try:
            padding = 15
            self.pos = QPoint(
                random.randint(padding, width - padding),
                random.randint(-50, -10)
            )
            self.speed = random.uniform(0.5, 4.0)
            self.amplitude = random.uniform(1.0, 4.0)
            self.wave_speed = random.uniform(0.01, 0.04)
            self.opacity = random.uniform(0.3, 1.0)
            self.fade_speed = random.uniform(0.005, 0.02)
            self.fading_in = random.choice([True, False])
            self.depth = random.uniform(0.5, 1.5)
        except Exception as e:
            print(f"Error resetting snowflake: {e}")