import serial
import serial.tools.list_ports
from win32api import GetSystemMetrics, GetKeyState
import threading
import time


def list_ports():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device}")
        return port.device
    return None


class MouseMover:
    _serial_port_lock = threading.Lock()
    _serial_port_opened = False

    def __init__(self, smoothing="linear", speed_multiplier=1, easing_strength=1.0, control_strength=1.0):
        print(
            f"__init__ called: smoothing={smoothing}, speed_multiplier={speed_multiplier}, "
            f"easing_strength={easing_strength}, control_strength={control_strength}")

        # Get screen dimensions
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        print(f"Screen dimensions: {self.screen_width}x{self.screen_height}")

        # Always use screen center as current position
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        print(f"Screen center: ({self.center_x}, {self.center_y})")

        self.smoothing = smoothing
        self.speed_multiplier = speed_multiplier
        self.easing_strength = easing_strength
        self.control_strength = max(0.0, min(1.0, control_strength))

        # Arduino communication setup
        self.port = list_ports()
        self.ser = None
        if not MouseMover._serial_port_opened:
            self._open_serial_port()
            if self.ser:
                MouseMover._serial_port_opened = True

        # Movement state
        self.target_x = self.center_x
        self.target_y = self.center_y
        self.move_thread = None
        self.stop_move_flag = False
        self.current_x = self.center_x
        self.current_y = self.center_y

    def _open_serial_port(self):
        with MouseMover._serial_port_lock:
            if self.port:
                try:
                    self.ser = serial.Serial(
                        port=self.port,
                        baudrate=115200,
                        timeout=0.05,
                        write_timeout=0.05,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE
                    )
                    print(f"Successfully opened port {self.port}")
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()

                    print("Testing communication...")
                    self.ser.write(b"TEST\r\n")
                    self.ser.flush()
                    response = self.ser.readline().decode().strip()
                    print(f"Response: '{response}'")
                    if response != "OK":
                        print("Communication test failed")
                        self.ser.close()
                        self.ser = None
                except serial.SerialException as e:
                    print(f"Error opening serial port: {e}")
                    self.ser = None
            else:
                print("No serial ports found.")

    def click(self, button='left'):
        """Simulate a mouse click with the specified button"""
        if not self.ser:
            print("Serial connection not available")
            return False

        try:
            # Send click command to Arduino
            button_code = '1' if button.lower() == 'left' else '2'
            command = f"CLICK {button_code}\r\n"
            self.ser.write(command.encode())
            response = self.ser.readline().decode().strip()

            if response == "OK":
                return True
            else:
                print(f"Unexpected response: {response}")
                return False

        except Exception as e:
            print(f"Error performing mouse click: {e}")
            return False

    def _constrain_to_screen(self, x, y):
        """Constrain coordinates to screen boundaries"""
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        return x, y

    def _calculate_relative_movement(self, current_x, current_y, target_x, target_y):
        """Calculate relative movement with speed control"""
        # Calculate raw movement
        dx = target_x - current_x
        dy = target_y - current_y

        # Apply speed multiplier to determine step size
        max_step = max(1, int(127 * self.speed_multiplier))  # 127 is max single step for Arduino

        # Scale down movements if they exceed max_step
        if abs(dx) > max_step or abs(dy) > max_step:
            scale = max_step / max(abs(dx), abs(dy))
            dx = int(dx * scale)
            dy = int(dy * scale)

        return dx, dy

    def _update_mouse_position(self):
        """Update mouse position based on current target"""
        # Check if right mouse button is released
        if self.stop_move_flag or GetKeyState(0x02) >= 0:
            return False

        target_x, target_y = self._constrain_to_screen(self.target_x, self.target_y)

        # Calculate movement relative to current position
        dx, dy = self._calculate_relative_movement(self.current_x, self.current_y, target_x, target_y)

        # Check if we're close enough to target
        if abs(dx) <= 2 and abs(dy) <= 2:
            return False

        # Move the mouse if we have a valid movement
        if dx != 0 or dy != 0:
            try:
                command = f"MOVE {dx},{dy},0\r\n"
                self.ser.write(command.encode())
                response = self.ser.readline().decode().strip()
                if response == "OK":
                    # Update current position
                    self.current_x += dx
                    self.current_y += dy
                    # Small delay to allow the movement to complete
                    time.sleep(0.001 / self.speed_multiplier)
                else:
                    print(f"Unexpected response: {response}")
            except Exception as e:
                print(f"Error in mouse movement: {e}")
                return False

        return True

    def set_mouse_position(self, target_x, target_y):
        """Set target position and start movement thread"""
        # Constrain target position to screen boundaries
        self.target_x, self.target_y = self._constrain_to_screen(target_x, target_y)

        # Stop any existing movement
        if self.move_thread and self.move_thread.is_alive():
            self.stop_move_flag = True
            self.move_thread.join()

        # Reset current position to center (since that's our reference point)
        self.current_x = self.center_x
        self.current_y = self.center_y

        # Start new movement thread
        self.stop_move_flag = False
        self.move_thread = threading.Thread(target=self._move_mouse_smoothly, daemon=True)
        self.move_thread.start()
        return self.move_thread

    def _move_mouse_smoothly(self):
        """Smoothly move mouse to target position"""
        while not self.stop_move_flag and self._update_mouse_position():
            pass