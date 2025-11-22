import math
import random
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt5.QtGui import QColor, QPainter, QRadialGradient, QLinearGradient, QPen, QBrush, QFont

class BaseEffect:
    def __init__(self, width, height, theme_manager):
        self.width = width
        self.height = height
        self.theme_manager = theme_manager

    def update(self, width, height):
        self.width = width
        self.height = height

    def draw(self, painter):
        pass

    def reset(self):
        pass

class SnowEffect(BaseEffect):
    class Snowflake:
        def __init__(self, width, height):
            self.reset(width, height, initial=True)

        def reset(self, width, height, initial=False):
            padding = 15
            x = random.randint(padding, width - padding)
            y = random.randint(-50, height) if initial else random.randint(-50, -10)
            self.pos = QPoint(x, y)
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
            self.pos.setY(int(self.pos.y() + self.speed * self.depth))
            self.offset += self.wave_speed
            self.pos.setX(int(self.pos.x() + math.sin(self.offset) * (self.amplitude / self.depth)))

            # Opacity
            if self.fading_in:
                self.opacity = min(1.0, self.opacity + self.fade_speed)
                if self.opacity >= 1.0: self.fading_in = False
            else:
                self.opacity = max(0.3, self.opacity - self.fade_speed)
                if self.opacity <= 0.3: self.fading_in = True

            padding = 15
            if (self.pos.x() < padding or self.pos.x() > width - padding or 
                self.pos.y() > height - padding):
                self.reset(width, height)

    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.snowflakes = [self.Snowflake(width, height) for _ in range(75)]
        self.mouse_pos = QPoint(0, 0)
        self.mouse_radius = 50

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        if mouse_pos:
            self.mouse_pos = mouse_pos
        
        for flake in self.snowflakes:
            # Mouse interaction
            dx = self.mouse_pos.x() - flake.pos.x()
            dy = self.mouse_pos.y() - flake.pos.y()
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < self.mouse_radius and dist > 0:
                factor = (self.mouse_radius - dist) / self.mouse_radius
                flake.pos.setX(int(flake.pos.x() - dx * factor * 0.1))
                flake.pos.setY(int(flake.pos.y() - dy * factor * 0.1))
            
            flake.update(width, height)

    def draw(self, painter):
        for flake in self.snowflakes:
            base_color = self.theme_manager.get_color("SNOWFLAKE")
            # If theme manager returns a QColor, use it, otherwise default to white
            if not isinstance(base_color, QColor):
                 base_color = QColor(255, 255, 255)

            color = QColor(base_color)
            color.setAlphaF(flake.opacity)
            
            # Simple glow logic from original
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            size = max(0.1, flake.size * flake.depth)
            painter.drawEllipse(flake.pos, int(size), int(size))

class RainEffect(BaseEffect):
    class Drop:
        def __init__(self, width, height):
            self.reset(width, height, initial=True)
        
        def reset(self, width, height, initial=False):
            self.x = random.randint(0, width)
            self.y = random.randint(-height, height) if initial else random.randint(-100, -10)
            self.z = random.uniform(0.5, 1.5) # Depth
            self.length = random.randint(10, 20) * self.z
            self.speed = random.uniform(10, 20) * self.z
            self.opacity = random.uniform(0.2, 0.6)

        def update(self, width, height):
            self.y += self.speed
            if self.y > height:
                self.reset(width, height)

    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.drops = [self.Drop(width, height) for _ in range(100)]

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        for drop in self.drops:
            drop.update(width, height)

    def draw(self, painter):
        color = self.theme_manager.get_color("TEXT") # Use text color for rain, or maybe a specific rain color
        if not isinstance(color, QColor): color = QColor(200, 200, 255)
        
        for drop in self.drops:
            c = QColor(color)
            c.setAlphaF(drop.opacity)
            painter.setPen(QPen(c, 1 * drop.z))
            painter.drawLine(int(drop.x), int(drop.y), int(drop.x), int(drop.y + drop.length))

class MatrixEffect(BaseEffect):
    class Stream:
        def __init__(self, x, height, font_size):
            self.x = x
            self.y = random.randint(-height, 0)
            self.speed = random.uniform(2, 5)
            self.chars = [chr(0x30A0 + i) for i in range(96)] # Katakana
            self.stream = []
            self.font_size = font_size
            self.generate_stream(height)

        def generate_stream(self, height):
            count = random.randint(5, 20)
            for i in range(count):
                self.stream.append({
                    'char': random.choice(self.chars),
                    'alpha': 1.0 - (i / count) # Fade out tail
                })

        def update(self, height):
            self.y += self.speed
            if random.random() < 0.05: # Randomly change head character
                if self.stream:
                    self.stream[0]['char'] = random.choice(self.chars)
            
            if self.y - len(self.stream) * self.font_size > height:
                self.y = random.randint(-100, 0)
                self.speed = random.uniform(2, 5)

    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.font_size = 14
        self.cols = int(width / self.font_size)
        self.streams = [self.Stream(i * self.font_size, height, self.font_size) for i in range(self.cols)]
        self.font = QFont("Consolas", self.font_size) # Monospace font

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        # Resize check
        if int(width / self.font_size) != len(self.streams):
            self.cols = int(width / self.font_size)
            self.streams = [self.Stream(i * self.font_size, height, self.font_size) for i in range(self.cols)]
        
        for stream in self.streams:
            stream.update(height)

    def draw(self, painter):
        painter.setFont(self.font)
        color = self.theme_manager.get_color("PRIMARY") # Matrix color usually green, but use theme primary
        
        for stream in self.streams:
            y = stream.y
            for char_data in stream.stream:
                c = QColor(color)
                c.setAlphaF(char_data['alpha'] * 0.8)
                painter.setPen(c)
                painter.drawText(int(stream.x), int(y), char_data['char'])
                y -= self.font_size

class ParticlesEffect(BaseEffect):
    class Particle:
        def __init__(self, width, height):
            self.pos = QPointF(random.random() * width, random.random() * height)
            self.vel = QPointF(random.uniform(-1, 1), random.uniform(-1, 1))
            self.size = random.uniform(2, 4)

        def update(self, width, height):
            self.pos += self.vel
            if self.pos.x() < 0 or self.pos.x() > width: self.vel.setX(-self.vel.x())
            if self.pos.y() < 0 or self.pos.y() > height: self.vel.setY(-self.vel.y())

    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.particles = [self.Particle(width, height) for _ in range(40)]
        self.connect_dist = 100

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        for p in self.particles:
            p.update(width, height)
            # Mouse repulsion
            if mouse_pos:
                dx = p.pos.x() - mouse_pos.x()
                dy = p.pos.y() - mouse_pos.y()
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 100:
                    p.vel += QPointF(dx, dy) * 0.001

    def draw(self, painter):
        color = self.theme_manager.get_color("ACCENT")
        pen = QPen(color)
        pen.setWidth(1)
        
        # Draw connections
        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i+1:]:
                dx = p1.pos.x() - p2.pos.x()
                dy = p1.pos.y() - p2.pos.y()
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < self.connect_dist:
                    alpha = 1.0 - (dist / self.connect_dist)
                    c = QColor(color)
                    c.setAlphaF(alpha * 0.5)
                    painter.setPen(QPen(c, 1))
                    painter.drawLine(p1.pos, p2.pos)
        
        # Draw particles
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        for p in self.particles:
            painter.drawEllipse(p.pos, p.size, p.size)

class StarfieldEffect(BaseEffect):
    class Star:
        def __init__(self, width, height):
            self.reset(width, height)
        
        def reset(self, width, height):
            self.x = random.randint(-width, width)
            self.y = random.randint(-height, height)
            self.z = random.randint(1, width)
            self.pz = self.z

        def update(self, width, height, speed):
            self.z -= speed
            if self.z < 1:
                self.reset(width, height)
                self.pz = self.z
            
    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.stars = [self.Star(width, height) for _ in range(200)]
        self.speed = 10

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        for star in self.stars:
            star.update(width, height, self.speed)

    def draw(self, painter):
        cx, cy = self.width / 2, self.height / 2
        color = self.theme_manager.get_color("TEXT")
        painter.setPen(color)
        
        for star in self.stars:
            sx = (star.x / star.z) * self.width + cx
            sy = (star.y / star.z) * self.height + cy
            
            r = (1 - star.z / self.width) * 3
            
            if 0 <= sx <= self.width and 0 <= sy <= self.height:
                painter.drawEllipse(QPointF(sx, sy), r, r)
                
                # Trail
                px = (star.x / star.pz) * self.width + cx
                py = (star.y / star.pz) * self.height + cy
                star.pz = star.z
                
                c = QColor(color)
                c.setAlphaF(0.5)
                painter.setPen(c)
                painter.drawLine(QPointF(px, py), QPointF(sx, sy))

class GradientWaveEffect(BaseEffect):
    def __init__(self, width, height, theme_manager):
        super().__init__(width, height, theme_manager)
        self.offset = 0
        self.speed = 0.02

    def update(self, width, height, mouse_pos=None):
        super().update(width, height)
        self.offset += self.speed
        if self.offset > 1: self.offset -= 1

    def draw(self, painter):
        # Create a large radial gradient that moves
        c1 = self.theme_manager.get_color("PRIMARY")
        c2 = self.theme_manager.get_color("SECONDARY")
        c3 = self.theme_manager.get_color("BACKGROUND")
        
        # Animated positions
        x = self.width * (0.5 + 0.3 * math.sin(self.offset * 2 * math.pi))
        y = self.height * (0.5 + 0.3 * math.cos(self.offset * 2 * math.pi))
        
        gradient = QRadialGradient(x, y, self.width * 0.8)
        gradient.setColorAt(0, QColor(c1.red(), c1.green(), c1.blue(), 100))
        gradient.setColorAt(0.5, QColor(c2.red(), c2.green(), c2.blue(), 50))
        gradient.setColorAt(1, QColor(c3.red(), c3.green(), c3.blue(), 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width, self.height)
