import time
import bettercam
import cv2
from win32api import GetSystemMetrics
from ObjectDetector import FastObjectDetector
from gui.widgets.colors import Colors
from mouse_mover import MouseMover
import win32api
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF
from queue import Queue, Empty, Full
import threading
import json
from pathlib import Path
from gui.ConfigManager import ConfigManager

# Initialize config manager at module level
settings_manager = ConfigManager()

# Screen dimensions
REGION_WIDTH = 500
REGION_HEIGHT = REGION_WIDTH
LEFT = (GetSystemMetrics(0) - REGION_WIDTH) // 2
TOP = (GetSystemMetrics(1) - REGION_HEIGHT) // 2
RIGHT = LEFT + REGION_WIDTH
BOTTOM = TOP + REGION_HEIGHT

multiplier = 0.12

key_states = {
    0x31: False,  # Key '1'
    0x32: False,  # Key '2'
}



class FOVOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FOV Overlay")
        self.setGeometry(LEFT, TOP, REGION_WIDTH, REGION_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("fov", True):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Use PRIMARY color with transparency
        border_color = QColor(Colors.PRIMARY)
        border_color.setAlpha(80)
        painter.setPen(QPen(border_color, 1))  # Changed to 1px width

        # Draw full size rectangle with proper 1px borders
        painter.drawRect(0, 0, REGION_WIDTH, REGION_HEIGHT)

class FPSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Window setup that only needs to happen once
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Position tracking
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(500)  # Check position every 500ms
        
        # FPS display setup
        self.fps = 0.0
        self.gradient_offset = 0
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self.update_gradient)
        self.gradient_timer.start(50)
        
        # Initial position update
        self.update_position()

    def update_position(self):
        """Update window position from current config"""
        visual_config = settings_manager.config.get("Visual", {})
        new_x = int(visual_config.get("fps_x", 604.0))
        new_y = int(visual_config.get("fps_y", 503.0))
        
        # Only move if position changed
        if (self.x(), self.y()) != (new_x, new_y):
            self.move(new_x, new_y)

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("fps", True):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_fps(painter)

    def draw_fps(self, painter):
        gradient = QLinearGradient(QPointF(0, 0), QPointF(200, 0))
        gradient.setColorAt(0, QColor(Colors.FPS_GRADIENT_START))
        gradient.setColorAt(0.5, QColor(Colors.FPS_GRADIENT_MIDDLE))
        gradient.setColorAt(1, QColor(Colors.FPS_GRADIENT_END))
        gradient.setSpread(QLinearGradient.ReflectSpread)
        gradient.setStart(QPointF(self.gradient_offset, 0))
        gradient.setFinalStop(QPointF(self.gradient_offset + 200, 0))

        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)
        fps_text = f"FPS: {self.fps:.1f}"
        text_x = REGION_WIDTH - 120
        text_y = 16
        painter.setPen(QPen(gradient, 2))
        painter.drawText(text_x, text_y, fps_text)

    def update_gradient(self):
        self.gradient_offset = (self.gradient_offset + 5) % 200
        self.update()

    def update_fps(self, fps):
        self.fps = float(fps)
        self.update()


class DetectionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detection Overlay")
        self.setGeometry(LEFT, TOP, REGION_WIDTH, REGION_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.circle_positions = []

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("target", False):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circles
        painter.setPen(QPen(QColor(Colors.AIM_INDICATOR), 7))
        for pos in self.circle_positions:
            painter.drawEllipse(QPointF(pos[0], pos[1]), 5, 5)

    def update_circles(self, positions):
        self.circle_positions = positions
        self.update()


def update_multiplier():
    global multiplier
    if win32api.GetKeyState(0x31) < 0 and not key_states[0x31]:
        multiplier = settings_manager.get("Aimbot.target_height_1", 0.18)
        key_states[0x31] = True
    elif win32api.GetKeyState(0x31) >= 0:
        key_states[0x31] = False

    if win32api.GetKeyState(0x32) < 0 and not key_states[0x32]:
        multiplier = settings_manager.get("Aimbot.target_height_2", 0.11)
        key_states[0x32] = True
    elif win32api.GetKeyState(0x32) >= 0:
        key_states[0x32] = False


def main():
    global detectionOverlay, multiplier

    app = QApplication([])
    detection_overlay = DetectionOverlay()
    fps_overlay = FPSOverlay()
    fov_overlay = FOVOverlay()  # <-- ADD THIS
    detection_overlay.show()
    fps_overlay.show()
    fov_overlay.show()  # <-- ADD THIS

    # Mouse movement setup
    mouse_movement_queue = Queue(maxsize=2)

    def mouse_movement_worker():
        mouse = MouseMover(
            smoothing="linear",
            get_speed=lambda: settings_manager.get("Aimbot.speed", 0.08),
            easing_strength=3,
            control_strength=0.9
        )
        last_position = None
        while True:
            try:
                position = mouse_movement_queue.get(timeout=0.001)
                if (win32api.GetKeyState(0x02) < 0 and
                        (last_position is None or position != last_position)):
                    mouse.set_mouse_position(*position)
                    last_position = position
                while not mouse_movement_queue.empty():
                    mouse_movement_queue.get_nowait()
            except Empty:
                continue
            except Exception as e:
                print(f"Mouse movement error: {e}")

    movement_thread = threading.Thread(target=mouse_movement_worker, daemon=True)
    movement_thread.start()

    try:
        detector = FastObjectDetector(engine_path='assets/models/' + settings_manager.get("AI.model", "csgo2_best.engine"))
        region = (LEFT, TOP, RIGHT, BOTTOM)
        camera = bettercam.create(output_idx=0, output_color="BGRA", region=region)
        camera.start(target_fps=200, video_mode=True)

        # Frame producer-consumer setup
        frame_queue = Queue(maxsize=1)

        def frame_producer():
            while True:
                frame = camera.get_latest_frame()
                if frame is not None:
                    try:
                        if frame_queue.full():
                            frame_queue.get_nowait()
                        frame_queue.put_nowait(frame)
                    except (Empty, Full):
                        pass

        producer_thread = threading.Thread(target=frame_producer, daemon=True)
        producer_thread.start()

        frame_count = 0
        last_fps_time = time.time()

        while True:
            try:
                frame = frame_queue.get(timeout=0.001)
            except Empty:
                continue

            current_time = time.time()
            update_multiplier()

            # Process frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            boxes = detector.detect(frame_rgb)

            # Find closest box
            circle_positions = []
            if boxes:
                closest_box = None
                min_distance_sq = float('inf')
                region_center_x_norm = 0.5
                region_center_y_norm = 0.5

                for box in boxes:
                    x1, y1, x2, y2 = box['bbox']
                    box_center_x = (x1 + x2) / 2
                    box_center_y = (y1 + y2) / 2
                    distance_sq = (box_center_x - region_center_x_norm) ** 2 + (
                                box_center_y - region_center_y_norm) ** 2
                    if distance_sq < min_distance_sq:
                        min_distance_sq = distance_sq
                        closest_box = box

                if closest_box:
                    x1, y1, x2, y2 = closest_box['bbox']
                    x1_abs = x1 * REGION_WIDTH
                    y1_abs = y1 * REGION_HEIGHT
                    x2_abs = x2 * REGION_WIDTH
                    y2_abs = y2 * REGION_HEIGHT

                    circle_x = int((x1_abs + x2_abs) / 2)
                    circle_y = int(y1_abs + (y2_abs - y1_abs) * multiplier)

                    screen_x = LEFT + circle_x
                    screen_y = TOP + circle_y

                    if win32api.GetKeyState(0x02) < 0:
                        try:
                            mouse_movement_queue.put_nowait((screen_x, screen_y))
                        except Full:
                            pass

                    circle_positions.append((circle_x, circle_y))

            detection_overlay.update_circles(circle_positions)

            # FPS counter
            frame_count += 1
            elapsed_time = current_time - last_fps_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                fps_overlay.update_fps(fps)
                frame_count = 0
                last_fps_time = current_time

            app.processEvents()

    except KeyboardInterrupt:
        print("\nStopping gracefully...")
    finally:
        camera.stop()
        del camera


if __name__ == "__main__":
    main()
