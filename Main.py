import time
import time
import bettercam
import cv2
import cv2
from render.inference_fps import FPSOverlay
from render.capture import ScreenCapture
from win32api import GetSystemMetrics
from ObjectDetector import FastObjectDetector
from gui.widgets.colors import theme_manager # Import theme_manager instead of Colors
from mouse_mover import MouseMover
import win32api
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPointF
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

# UpdateThread and associated classes moved to render.inference_fps


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
                return None, -1
            prev_write = (self.write_idx - 1) % self.size
            # Return frame AND the processed count as a sequence ID
            return self.buffer[prev_write].copy(), self.frames_processed

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

# FPSOverlay moved to render.inference_fps


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

def frame_producer(capture, frame_buffer):
    while True:
        frame = capture.get_latest_frame()
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
        target_fps = int(settings_manager.get("Aimbot.fps", 999))
        capture = ScreenCapture(region=region, output_idx=0, output_color="BGRA", target_fps=target_fps)
        capture.start()

        # Initialize frame buffer with size 3
        frame_buffer = FrameRingBuffer(buffer_size=3)

        # Start frame producer thread
        producer_thread = threading.Thread(target=frame_producer, args=(capture, frame_buffer), daemon=True)
        producer_thread.start()

        frame_count = 0
        last_fps_time = time.time()
        update_gui_counter = 0  # Counter for GUI updates

        last_processed_seq_id = -1

        while True:
            frame, seq_id = frame_buffer.get_latest_frame()
            if frame is None:
                continue

            # Check if we should cap inference FPS
            if settings_manager.get("AI.cap_inference_fps", False):
                if seq_id <= last_processed_seq_id:
                    time.sleep(0.0001) # Sleep briefly to yield
                    continue
            
            last_processed_seq_id = seq_id
            
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
                capture_fps = capture.get_fps()
                fps_overlay.update_fps(fps, capture_fps)
                frame_count = 0
                last_fps_time = current_time

            # Process Qt events in batches
            if update_gui_counter == 0:
                app.processEvents()

    except KeyboardInterrupt:
        print("\nStopping gracefully...")
    finally:
        capture.stop()
        del capture

if __name__ == "__main__":
    main()