import time
import bettercam
import cv2
from win32api import GetSystemMetrics
from ObjectDetector import FastObjectDetector
from gui.widgets.colors import theme_manager # Import theme_manager instead of Colors
from mouse_mover import MouseMover
import win32api
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF, QThread
import threading
from queue import Queue, Empty, Full
import json
from pathlib import Path
from gui.ConfigManager import ConfigManager
import numpy as np

# Initialize config manager at module level
settings_manager = ConfigManager()
# Ensure theme manager loads theme from config *before* widgets are created
from gui.widgets.colors import get_theme_manager
get_theme_manager(settings_manager)


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

class UpdateThread(QThread):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        while True:
            self.widget.update_position()
            time.sleep(0.5)  # 500ms interval

class FrameRingBuffer:
    def __init__(self, buffer_size=3, frame_shape=None):
        self.size = buffer_size
        self.frame_shape = frame_shape
        self.buffer = [None] * buffer_size if frame_shape is None else np.zeros((buffer_size, *frame_shape), dtype=np.uint8)
        self.write_idx = 0
        self.read_idx = 0
        self._lock = threading.Lock()
        self.frames_processed = 0
        self.frames_dropped = 0

    def put_frame(self, frame):
        if self.frame_shape is None and frame is not None:
            self.frame_shape = frame.shape
            self.buffer = np.zeros((self.size, *self.frame_shape), dtype=np.uint8)

        with self._lock:
            next_write = (self.write_idx + 1) % self.size
            if next_write == self.read_idx:
                self.read_idx = (self.read_idx + 1) % self.size
                self.frames_dropped += 1
            np.copyto(self.buffer[self.write_idx], frame)
            self.write_idx = next_write
            self.frames_processed += 1

    def get_latest_frame(self):
        with self._lock:
            if self.write_idx == self.read_idx:
                return None
            prev_write = (self.write_idx - 1) % self.size
            return self.buffer[prev_write].copy()

class FOVOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FOV Overlay")
        self.setGeometry(LEFT, TOP, REGION_WIDTH, REGION_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        theme_manager.themeChanged.connect(self.update) # Update on theme change

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("fov", True):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        border_color = theme_manager.get_color("PRIMARY") # Use theme_manager
        border_color.setAlpha(80)
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(0, 0, REGION_WIDTH, REGION_HEIGHT)

class FPSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create update thread for position
        self.update_thread = UpdateThread(self)
        self.update_thread.start()

        self.fps = 0.0
        # Re-introduce gradient attributes and timer
        self.gradient_offset = 0
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self.update_gradient)
        self.gradient_timer.start(50) # Animation speed
        self.update_position()
        theme_manager.themeChanged.connect(self.update) # Update on theme change

    def update_position(self):
        visual_config = settings_manager.config.get("Visual", {})
        new_x = int(visual_config.get("fps_x", 604.0))
        new_y = int(visual_config.get("fps_y", 503.0))
        if (self.x(), self.y()) != (new_x, new_y):
            self.move(new_x, new_y)

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("fps", True):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_fps(painter)

    def draw_fps(self, painter):
        # Re-introduce gradient using PRIMARY and ACCENT colors
        gradient = QLinearGradient(QPointF(0, 0), QPointF(200, 0)) # Adjust size as needed
        gradient.setColorAt(0, theme_manager.get_color("PRIMARY"))
        gradient.setColorAt(0.5, theme_manager.get_color("ACCENT"))
        gradient.setColorAt(1, theme_manager.get_color("PRIMARY"))
        gradient.setSpread(QLinearGradient.ReflectSpread)
        gradient.setStart(QPointF(self.gradient_offset, 0))
        gradient.setFinalStop(QPointF(self.gradient_offset + 200, 0)) # Match size

        font = QFont("Arial", 16, QFont.Bold) # Consider theming the font later if needed
        painter.setFont(font)
        fps_text = f"FPS: {self.fps:.1f}"
        text_x = REGION_WIDTH - 120 # Position might need adjustment depending on theme/font
        text_y = 16

        # Set the pen to use the animated gradient
        painter.setPen(QPen(gradient, 2)) # Use gradient, adjust thickness if needed
        painter.drawText(text_x, text_y, fps_text)


    # Re-introduce update_gradient method
    def update_gradient(self):
        self.gradient_offset = (self.gradient_offset + 5) % 200 # Match gradient size
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
        theme_manager.themeChanged.connect(self.update) # Update on theme change

    def paintEvent(self, event):
        if not settings_manager.config.get("Visual", {}).get("target", False):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Use theme_manager.get_color() which returns a QColor
        painter.setPen(QPen(theme_manager.get_color("AIM_INDICATOR"), 7))
        for pos in self.circle_positions:
            painter.drawEllipse(QPointF(pos[0], pos[1]), 5, 5)

    def update_circles(self, positions):
        self.circle_positions = positions
        self.update()


key_states = {
    0x31: False,  # Key '1'
    0x32: False,  # Key '2'
}

# Variables for smooth aim height adjustment
left_click_held = False
original_multiplier = None

# Create a function to update settings when config changes
def update_settings_from_config():
    global multiplier
    # If we're not in midst of adjustment, update multiplier to current setting
    if not left_click_held or original_multiplier is None:
        if win32api.GetAsyncKeyState(0x31) < 0:
            multiplier = settings_manager.get("Aimbot.target_height_1", 0.18)
        elif win32api.GetAsyncKeyState(0x32) < 0:
            multiplier = settings_manager.get("Aimbot.target_height_2", 0.11)


# Register the observer with the settings manager to be notified of changes
settings_manager.register_observer(update_settings_from_config)


def update_multiplier():
    global multiplier, left_click_held, original_multiplier

    target_height_1 = settings_manager.get("Aimbot.target_height_1", 0.18)
    target_height_2 = settings_manager.get("Aimbot.target_height_2", 0.11)
    base_height_increment = settings_manager.get("Aimbot.recoil", 0.03)

    if win32api.GetAsyncKeyState(0x31) < 0 and not key_states[0x31]:
        multiplier = target_height_1
        key_states[0x31] = True
    elif win32api.GetAsyncKeyState(0x31) >= 0:
        key_states[0x31] = False

    if win32api.GetAsyncKeyState(0x32) < 0 and not key_states[0x32]:
        multiplier = target_height_2
        key_states[0x32] = True
    elif win32api.GetAsyncKeyState(0x32) >= 0:
        key_states[0x32] = False

    trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
    # Debug print to verify key and state
    # print(f"Trigger Key: {trigger_key}, State: {win32api.GetAsyncKeyState(trigger_key)}")
    
    right_click_held = (win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0
    left_click_current = (win32api.GetAsyncKeyState(0x01) & 0x8000) != 0

    if not right_click_held:
        if left_click_held and original_multiplier is not None:
            multiplier = original_multiplier
            original_multiplier = None
        left_click_held = False
        return

    current_speed = settings_manager.get("Aimbot.speed", 0.08)

    height_increment = base_height_increment * current_speed

    if left_click_current:
        if not left_click_held:
            left_click_held = True
            original_multiplier = multiplier

        max_recoil_factor = settings_manager.get("Aimbot.max_recoil", 2.0)
        max_value = original_multiplier * max_recoil_factor
        multiplier = min(multiplier + height_increment, max_value)

    elif left_click_held:
        left_click_held = False
        multiplier = original_multiplier
        original_multiplier = None

def frame_producer(camera, frame_buffer):
    while True:
        frame = camera.get_latest_frame()
        if frame is not None:
            frame_buffer.put_frame(frame)
        time.sleep(0.001)  # Small sleep to prevent CPU thrashing

def main():
    app = QApplication([])
    detection_overlay = DetectionOverlay()
    fps_overlay = FPSOverlay()
    fov_overlay = FOVOverlay()
    detection_overlay.show()
    fps_overlay.show()
    fov_overlay.show()

    # Mouse movement setup with larger queue
    mouse_movement_queue = Queue(maxsize=1)

    def mouse_movement_worker():
        mouse = MouseMover(
            smoothing="linear",
            get_speed=lambda: settings_manager.get("Aimbot.speed", 0.08),
            # ADD THIS LINE BELOW:
            get_trigger_key=lambda: settings_manager.get("Aimbot.trigger_key", 0x05),
            easing_strength=3,
            control_strength=0.9
        )
        last_position = None
        while True:
            try:
                position = mouse_movement_queue.get(timeout=0.001)
                trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
                if ((win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0 and
                        (last_position is None or position != last_position)):
                    mouse.set_mouse_position(*position)
                    last_position = position
            except Empty:
                continue
            except Exception as e:
                print(f"Mouse movement error: {e}")

    movement_thread = threading.Thread(target=mouse_movement_worker, daemon=True)
    movement_thread.start()

    try:
        current_model_name = settings_manager.get("AI.model", "csgo2_best.engine")
        detector = FastObjectDetector(engine_path='assets/models/' + current_model_name)
        
        # Model reload state
        model_reload_state = {
            "needed": False,
            "new_model_name": None
        }

        def check_model_change():
            new_name = settings_manager.get("AI.model", "csgo2_best.engine")
            if new_name != current_model_name:
                model_reload_state["needed"] = True
                model_reload_state["new_model_name"] = new_name

        settings_manager.register_observer(check_model_change)

        region = (LEFT, TOP, RIGHT, BOTTOM)
        camera = bettercam.create(output_idx=0, output_color="BGRA", region=region)
        camera.start(target_fps=200, video_mode=True)

        # Initialize frame buffer with size 3
        frame_buffer = FrameRingBuffer(buffer_size=3)

        # Start frame producer thread
        producer_thread = threading.Thread(target=frame_producer, args=(camera, frame_buffer), daemon=True)
        producer_thread.start()

        frame_count = 0
        last_fps_time = time.time()
        update_gui_counter = 0  # Counter for GUI updates

        while True:
            frame = frame_buffer.get_latest_frame()
            if frame is None:
                continue
            
            # Check for model reload
            if model_reload_state["needed"]:
                new_name = model_reload_state["new_model_name"]
                if new_name:
                    print(f"Switching model to {new_name}...")
                    if detector.reload('assets/models/' + new_name):
                        current_model_name = new_name
                    model_reload_state["needed"] = False

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

                    trigger_key = settings_manager.get("Aimbot.trigger_key", 0x05)
                    if (win32api.GetAsyncKeyState(trigger_key) & 0x8000) != 0:
                        try:
                            mouse_movement_queue.put_nowait((screen_x, screen_y))
                        except Full:
                            pass

                    circle_positions.append((circle_x, circle_y))

            # Update GUI less frequently (every 2 frames)
            update_gui_counter += 1
            if update_gui_counter >= 2:
                detection_overlay.update_circles(circle_positions)
                update_gui_counter = 0

            # FPS counter
            frame_count += 1
            elapsed_time = current_time - last_fps_time
            if elapsed_time >= 0.5:  # Update FPS every 500ms instead of every second
                fps = frame_count / elapsed_time
                fps_overlay.update_fps(fps)
                frame_count = 0
                last_fps_time = current_time

            # Process Qt events in batches
            if update_gui_counter == 0:
                app.processEvents()

    except KeyboardInterrupt:
        print("\nStopping gracefully...")
    finally:
        camera.stop()
        del camera

if __name__ == "__main__":
    main()
