import time
import bettercam
import cv2
from win32api import GetSystemMetrics
from ObjectDetector import FastObjectDetector
from mouse_mover import MouseMover
import win32api
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF
from queue import Queue, Empty, Full
import threading

# Screen dimensions
REGION_WIDTH = 500  # Can be any size now
REGION_HEIGHT = 500
LEFT = (GetSystemMetrics(0) - REGION_WIDTH) // 2  # (2560 - 640) // 2
TOP = (GetSystemMetrics(1) - REGION_HEIGHT) // 2  # (1440 - 640) // 2
RIGHT = LEFT + REGION_WIDTH
BOTTOM = TOP + REGION_HEIGHT

# Overlay toggle
overlay_enabled = False

# Multiplier for circle_y calculation (top 12% of the detection box)
multiplier = 0.12

# Key states
key_states = {
    0x31: False,  # Key '1'
    0x32: False,  # Key '2'
}

# Click radius (adjustable)
CLICK_RADIUS = 9  # Radius around the click position

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay")
        self.setGeometry(LEFT, TOP, REGION_WIDTH, REGION_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.circle_positions = []
        self.fps = 0.0  # Initialize fps as float
        self.gradient_offset = 0
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self.update_gradient)
        self.gradient_timer.start(50)

    def paintEvent(self, event):
        if not overlay_enabled:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circles
        painter.setPen(QPen(QColor(255, 0, 0, 127), 7))
        for pos in self.circle_positions:
            # Adjust the coordinates to center the circle
            painter.drawEllipse(QPointF(pos[0], pos[1]), 5, 5)  # 25 is the radius

        # Draw FPS with gradient
        self.draw_fps(painter)

    def draw_fps(self, painter):
        # Create gradient
        gradient = QLinearGradient(QPointF(0, 0), QPointF(200, 0))
        gradient.setColorAt(0, QColor(64, 244, 208))
        gradient.setColorAt(0.5, QColor(255, 192, 203))
        gradient.setColorAt(1, QColor(64, 244, 238))
        gradient.setSpread(QLinearGradient.ReflectSpread)

        # Set gradient position
        gradient.setStart(QPointF(self.gradient_offset, 0))
        gradient.setFinalStop(QPointF(self.gradient_offset + 200, 0))

        # Create text path for gradient fill
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)

        # Draw background for better visibility
        fps_text = f"FPS: {self.fps:.1f}"
        text_rect = painter.fontMetrics().boundingRect(fps_text)
        text_x = REGION_WIDTH - 120 # Position from left
        text_y = 16  # Position from top

        # Draw text with gradient
        painter.setPen(QPen(gradient, 2))
        painter.drawText(text_x, text_y, fps_text)

    def update_gradient(self):
        self.gradient_offset = (self.gradient_offset + 5) % 200
        self.update()

    def update_fps(self, fps):
        self.fps = float(fps)  # Ensure fps is float
        self.update()

    def update_circles(self, positions):
        """Update the positions of circles to be drawn"""
        self.circle_positions = positions
        self.update()

def get_distance_to_center(box):
    """Calculate distance from box center to region center"""
    x1, y1, x2, y2 = box['bbox']

    # Convert normalized coordinates back to region coordinates
    x1 = x1 * REGION_WIDTH
    x2 = x2 * REGION_WIDTH
    y1 = y1 * REGION_HEIGHT
    y2 = y2 * REGION_HEIGHT

    headshot_mode = True

    box_center_x = (x1 + x2) / 2
    box_center_y = (y1 + y2) / 2

    # Calculate distance to center of region
    center_x = REGION_WIDTH / 2
    center_y = REGION_HEIGHT / 2

    return math.sqrt((box_center_x - center_x) ** 2 + (box_center_y - center_y) ** 2)

def update_multiplier():
    global multiplier
    if win32api.GetKeyState(0x31) < 0 and not key_states[0x31]:  # Key '1' pressed and state was not pressed
        multiplier = 0.12
        key_states[0x31] = True  # Update key state
    elif win32api.GetKeyState(0x31) >= 0:  # Key '1' released
        key_states[0x31] = False  # Reset key state

    if win32api.GetKeyState(0x32) < 0 and not key_states[0x32]:  # Key '2' pressed and state was not pressed
        multiplier = 0.12
        key_states[0x32] = True  # Update key state
    elif win32api.GetKeyState(0x32) >= 0:  # Key '2' released
        key_states[0x32] = False  # Reset key state

def is_cursor_in_circle(circle_positions):
    """Check if the cursor (center of the screen) is within the red circle"""
    if not circle_positions:
        return False

    # Cursor is always at the center of the screen
    cursor_x = REGION_WIDTH // 2
    cursor_y = REGION_HEIGHT // 2

    for pos in circle_positions:
        circle_x, circle_y = pos
        distance = math.sqrt((cursor_x - circle_x) ** 2 + (cursor_y - circle_y) ** 2)
        if distance <= CLICK_RADIUS:  # Use configurable radius
            return True

    return False

def click_worker(mouse_mover, overlay):
    """Worker function to continuously check and click if cursor is in circle"""
    last_click_time = 0  # Track the last click time
    while True:
        if is_cursor_in_circle(overlay.circle_positions):
            current_time = time.time()
            if current_time - last_click_time >= 0.2 or last_click_time == 0:  # No delay for the first click
                mouse_mover.click(button='left')
                last_click_time = current_time
        time.sleep(0.01)  # Small sleep to avoid high CPU usage

def main():
    global overlay_enabled, multiplier

    app = QApplication([])
    overlay = Overlay()
    overlay.show()

    # Create a MouseMover instance
    mouse_mover = MouseMover(
        smoothing="linear",
        speed_multiplier=0.08,
        easing_strength=3,
        control_strength=0.9
    )

    # Create a separate thread for mouse movement with a smaller queue
    mouse_movement_queue = Queue(maxsize=2)  # Reduced queue size for more responsive movement

    def mouse_movement_worker():
        last_position = None
        while True:
            try:
                position = mouse_movement_queue.get(timeout=0.001)  # Shorter timeout for faster updates

                # Only update if position changed and right click is held
                if (win32api.GetKeyState(0x02) < 0 and
                        (last_position is None or position != last_position)):
                    mouse_mover.set_mouse_position(*position)
                    last_position = position

                # Clear queue to always use latest position
                while not mouse_movement_queue.empty():
                    try:
                        mouse_movement_queue.get_nowait()
                    except Empty:
                        break

            except Empty:
                continue
            except Exception as e:
                print(f"Mouse movement error: {e}")

    # Start mouse movement thread
    movement_thread = threading.Thread(target=mouse_movement_worker, daemon=True)
    movement_thread.start()

    # Start click worker thread
    click_thread = threading.Thread(target=click_worker, args=(mouse_mover, overlay), daemon=True)
    click_thread.start()

    try:
        detector = FastObjectDetector(engine_path='assets/models/new_csgo.engine')
        region = (LEFT, TOP, RIGHT, BOTTOM)
        camera = bettercam.create(output_idx=0, output_color="BGRA", region=region)
        camera.start(target_fps=200, video_mode=True)

        frame_count = 0
        last_fps_time = time.time()
        last_detection_time = time.time()

        while True:
            frame = camera.get_latest_frame()
            if frame is None:
                continue

            current_time = time.time()

            # Update multiplier based on key press
            update_multiplier()

            # Process frame and update detection
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            boxes = detector.detect(frame_rgb)

            # Update overlay positions and mouse movement
            circle_positions = []
            if boxes:
                boxes.sort(key=get_distance_to_center)
                closest_box = boxes[0]

                x1, y1, x2, y2 = closest_box['bbox']
                x1 = x1 * REGION_WIDTH
                y1 = y1 * REGION_HEIGHT
                x2 = x2 * REGION_WIDTH
                y2 = y2 * REGION_HEIGHT

                # Calculate the click position in the top 12% of the detection box
                circle_x = int((x1 + x2) / 2)
                circle_y = int(y1 + (y2 - y1) * multiplier)

                screen_x = int(LEFT + circle_x)
                screen_y = int(TOP + circle_y)

                # Update mouse position if right click is held
                if win32api.GetKeyState(0x02) < 0:
                    try:
                        while not mouse_movement_queue.empty():
                            mouse_movement_queue.get_nowait()
                        mouse_movement_queue.put_nowait((screen_x, screen_y))
                    except (Full, Empty):
                        pass

                circle_positions.append((circle_x, circle_y))

            overlay.update_circles(circle_positions)

            # Update FPS counter
            frame_count += 1
            elapsed_time = current_time - last_fps_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                overlay.update_fps(fps)
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
