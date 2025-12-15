import socket
import struct
import threading
import time
import random
from win32api import GetSystemMetrics, GetAsyncKeyState

# ==========================================
# HARDWARE CONFIGURATION
# ==========================================
ESP32_IP = "192.168.1.24"
ESP32_PORT = 4210

# THE SECRET KEY (Must match ESP32 exactly)
# A random lookup table for high-speed XOR encryption
SECRET_KEY = [
    0x4A, 0x1F, 0xC3, 0x89, 0x2D, 0xE5, 0x7B, 0x90, 0x12, 0x66, 0xF4, 0xAB, 0x09, 0xDD, 0x5E, 0x33,
    0x81, 0x47, 0x9C, 0x22, 0xFA, 0x05, 0xE0, 0x6B, 0x18, 0xD2, 0xB7, 0x4F, 0x94, 0x3A, 0xC8, 0x71,
    0x56, 0x0E, 0xBF, 0xA3, 0x29, 0xD6, 0x8C, 0x14, 0x60, 0xF9, 0x3E, 0x77, 0xB2, 0x98, 0x41, 0x06,
    0xED, 0x53, 0xAA, 0x1B, 0xC5, 0x86, 0x2F, 0xD9, 0x74, 0x02, 0xB0, 0x6E, 0x95, 0x37, 0xF1, 0x24,
    0xCC, 0x59, 0x10, 0x84, 0xDB, 0x63, 0x0A, 0xA8, 0x44, 0xEF, 0x7D, 0x26, 0x91, 0x35, 0xBC, 0x68,
    0x17, 0xD4, 0x72, 0xFE, 0x51, 0x0D, 0x99, 0x2A, 0xC1, 0x8F, 0x48, 0xE6, 0x75, 0x32, 0xB9, 0x04,
    0xF6, 0x6D, 0x21, 0x9E, 0x5C, 0x07, 0xBB, 0x40, 0x83, 0xD0, 0x67, 0x2E, 0xE2, 0x79, 0x15, 0xCF,
    0x58, 0xA5, 0x3B, 0x93, 0x0F, 0xFB, 0x4D, 0x88, 0x1C, 0x70, 0xAE, 0x36, 0xE9, 0x64, 0x25, 0x9A,
    0x55, 0x82, 0x13, 0xC6, 0x3F, 0xF2, 0x7E, 0x2B, 0x97, 0x45, 0x08, 0xDA, 0x61, 0xE8, 0x34, 0xB6,
    0x03, 0xCB, 0x9F, 0x50, 0xA1, 0x19, 0x76, 0xE4, 0x8D, 0x23, 0xD5, 0x6A, 0x16, 0xAC, 0x7F, 0x46,
    0xF5, 0x20, 0x9B, 0x57, 0x0B, 0xC9, 0x80, 0x3D, 0xE1, 0x69, 0x1D, 0xB4, 0x78, 0x27, 0xDF, 0x54,
    0x96, 0x42, 0xEC, 0x7A, 0x11, 0xA6, 0x30, 0xF8, 0x65, 0xBE, 0xD7, 0x8E, 0x2C, 0x5F, 0x01, 0xCA,
    0x49, 0x92, 0x1A, 0xE3, 0x73, 0x38, 0xA9, 0x5D, 0xD1, 0x62, 0xB5, 0x0C, 0xFC, 0x85, 0x31, 0xAF,
    0x6C, 0x28, 0xF3, 0x7C, 0x9D, 0x4E, 0x1E, 0xB8, 0x52, 0xA0, 0x00, 0xCD, 0x8B, 0x43, 0xE7, 0x5B,
    0x39, 0xA2, 0x6F, 0xD8, 0x22, 0xEE, 0x87, 0x12, 0x5A, 0xBD, 0x74, 0x4C, 0x90, 0x3C, 0xF0, 0xA4,
    0xB1, 0x66, 0x05, 0xEB, 0x7B, 0x2F, 0x94, 0x47, 0xC4, 0x18, 0xAD, 0x5E, 0xD3, 0x8A, 0x2D, 0xFE
]

class MouseMover:
    def __init__(self, smoothing="linear", get_speed=lambda: 1, get_trigger_key=lambda: 0x05, easing_strength=1.0, control_strength=1.0):
        self.ip = ESP32_IP
        self.port = ESP32_PORT

        self.get_speed = get_speed
        self.get_trigger_key = get_trigger_key
        
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.setblocking(False)

        self.HEAD_MOVE = 0xAB
        self.HEAD_CLICK = 0xAC

        self.target_x = self.center_x
        self.target_y = self.center_y
        self.current_x = self.center_x
        self.current_y = self.center_y
        
        self.running = True
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        
        print(f"[*] UDP Encrypted Mouse -> {self.ip}:{self.port}")

    def set_mouse_position(self, x, y):
        with self.lock:
            self.target_x = max(0, min(x, self.screen_width - 1))
            self.target_y = max(0, min(y, self.screen_height - 1))
            self.current_x = self.center_x
            self.current_y = self.center_y

    def _encrypt_and_send(self, header, data1, data2=0):
        """
        FULL ENCRYPTION ENGINE - ALL BYTES ENCRYPTED
        
        Protocol v2.0:
        1. Generate random Salt (0-255)
        2. Derive 4 different keys from salt using offsets in SECRET_KEY
        3. XOR each byte (header, data1, data2) with its own key
        4. Calculate checksum for integrity
        5. Send [Salt] [EncHeader] [EncData1] [EncData2] [EncChecksum]
        
        This ensures ALL data in the air is encrypted - no plaintext headers!
        """
        salt = random.randint(0, 255)
        
        # Derive different keys for each byte position
        # Using prime-ish offsets for better key distribution
        key_header = SECRET_KEY[salt]
        key_data1 = SECRET_KEY[(salt + 73) % 256]  # Prime offset
        key_data2 = SECRET_KEY[(salt + 149) % 256]  # Prime offset
        key_check = SECRET_KEY[(salt + 211) % 256]  # Prime offset
        
        # XOR Encryption for ALL bytes
        enc_header = (header ^ key_header) & 0xFF
        enc_data1 = (data1 ^ key_data1) & 0xFF
        enc_data2 = (data2 ^ key_data2) & 0xFF
        
        # Simple checksum: XOR of original bytes (for integrity verification)
        checksum = (header ^ data1 ^ data2) & 0xFF
        enc_checksum = (checksum ^ key_check) & 0xFF
        
        # Packet: [Salt, EncHeader, EncData1, EncData2, EncChecksum]
        # Salt is the only "plaintext" but it reveals nothing without the key table
        try:
            packet = struct.pack('BBBBB', salt, enc_header, enc_data1, enc_data2, enc_checksum)
            self.sock.sendto(packet, (self.ip, self.port))
        except BlockingIOError:
            pass

    def click(self, button='left'):
        btn_code = 1 if button == 'left' else 2
        # Use encryption for clicks too
        self._encrypt_and_send(self.HEAD_CLICK, btn_code, 0)

    def _calculate_relative_movement(self, current_x, current_y, target_x, target_y):
        dx = target_x - current_x
        dy = target_y - current_y
        speed_val = self.get_speed()
        max_step = max(1, int(127 * speed_val))

        if abs(dx) > max_step or abs(dy) > max_step:
            scale = max_step / max(abs(dx), abs(dy))
            dx = int(dx * scale)
            dy = int(dy * scale)

        return dx, dy

    def _worker_loop(self):
        while self.running:
            trigger_key = self.get_trigger_key()
            if not (GetAsyncKeyState(trigger_key) & 0x8000):
                time.sleep(0.01)
                continue

            with self.lock:
                tx, ty = self.target_x, self.target_y
                cx, cy = self.current_x, self.current_y

            dx, dy = self._calculate_relative_movement(cx, cy, tx, ty)

            if abs(dx) <= 2 and abs(dy) <= 2:
                time.sleep(0.001)
                continue

            if dx != 0 or dy != 0:
                # Prepare data for encryption
                # Convert signed (-127 to 127) to unsigned byte (0-255) for XOR math
                # We cast to unsigned 8-bit integer
                dx_u = dx & 0xFF
                dy_u = dy & 0xFF
                
                self._encrypt_and_send(self.HEAD_MOVE, dx_u, dy_u)

                with self.lock:
                    self.current_x += dx
                    self.current_y += dy

                speed = self.get_speed()
                if speed > 0:
                    time.sleep(0.001 / speed)
                else:
                    time.sleep(0.001)

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        self.sock.close()