import keyboard
import time
import threading
from mouse_mover import MouseMover


class KeySequenceDetector:
    def __init__(self, first_key='<', second_key='space', reset_keys=['2', '3'], click_delay=0.349):
        """
        Initialize a key sequence detector that performs a left click
        when the second key is pressed after the first key.

        Args:
            first_key (str): The first key in the sequence (default: '<')
            second_key (str): The second key in the sequence (default: 'space')
            reset_keys (list): Keys that reset the sequence (default: ['2', '3'])
            click_delay (float): Delay before click in seconds (default: 0.349)
        """
        self.first_key = first_key
        self.second_key = second_key
        self.reset_keys = reset_keys
        self.click_delay = click_delay
        self.is_running = False
        self.last_key_pressed = None

        # Initialize the MouseMover
        try:
            self.mouse_mover = MouseMover()
            self.mouse_available = True
            print("Mouse mover initialized successfully")
        except Exception as e:
            self.mouse_available = False
            print(f"Failed to initialize mouse mover: {e}")

        # Lock to prevent multiple click operations from overlapping
        self.click_lock = threading.Lock()

    def _perform_delayed_click(self):
        """Perform a left click after the specified delay"""
        with self.click_lock:
            print(f"Starting delay for {self.click_delay * 1000}ms...")
            time.sleep(self.click_delay)  # Wait for exactly 349ms

            if self.mouse_available:
                print("Delay complete, performing left click")
                success = self.mouse_mover.click(button='left')
                if success:
                    print("Left click performed successfully")
                else:
                    print("Failed to perform left click")
            else:
                print("Mouse mover not available, click simulation skipped")

    def _on_key_event(self, e):
        """Handle key events"""
        if not e.event_type == keyboard.KEY_DOWN:
            return

        # Get the key name
        key_name = e.name

        # First key in sequence
        if key_name == self.first_key:
            print(f"First key '{self.first_key}' detected")
            self.last_key_pressed = self.first_key

        # Second key after first key (trigger the click)
        elif key_name == self.second_key and self.last_key_pressed == self.first_key:
            print(f"Second key '{self.second_key}' detected after '{self.first_key}'")
            # Don't reset the last key - keep it as first_key to allow repeating the sequence

            # Start a new thread for the delayed click
            click_thread = threading.Thread(target=self._perform_delayed_click)
            click_thread.daemon = True
            click_thread.start()

        # Check if this is a reset key
        elif key_name in self.reset_keys:
            print(f"Reset key '{key_name}' detected (sequence reset)")
            self.last_key_pressed = None

        # Other keys are ignored and don't reset the sequence
        else:
            # Only print if it's not a common key to avoid console spam
            if key_name not in ['shift', 'ctrl', 'alt']:
                print(f"Key '{key_name}' detected (sequence maintained)")

    def start(self):
        """Start monitoring for the key sequence."""
        if self.is_running:
            print(f"Already monitoring for key sequence")
            return

        self.is_running = True
        keyboard.hook(self._on_key_event)
        print(f"Started monitoring for key sequence: '{self.first_key}' followed by '{self.second_key}'")
        print(f"Will perform left click after {self.click_delay * 1000}ms delay when sequence is detected")
        print(f"Sequence will be reset only when keys {self.reset_keys} are pressed")

        try:
            # Keep the program running
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped monitoring")
            self.stop()

    def stop(self):
        """Stop monitoring for the key sequence."""
        if not self.is_running:
            return

        self.is_running = False
        keyboard.unhook_all()
        print(f"\nStopped monitoring key sequence")


# Example usage
if __name__ == "__main__":
    detector = KeySequenceDetector(
        first_key='<',
        second_key='space',
        reset_keys=['2', '3'],
        click_delay=0.349
    )
    print("Press Ctrl+C to stop")
    detector.start()