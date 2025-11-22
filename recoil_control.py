import time
from win32api import GetKeyState
from mouse_mover import MouseMover


def get_speed():
    """Returns the current speed value (1-5)"""
    return 1.9  # Medium speed

# ak-47: 1.7
# m4a4: 1.42
# m4a1-s: 1
# MP9: 1.85


def main():
    # Create mouse mover
    mouse = MouseMover(
        smoothing="linear",
        get_speed=get_speed,
        easing_strength=1.0,
        control_strength=1.0
    )

    print("Downward mouse movement script started")
    print("Hold left mouse button to move cursor down")
    print("Press Ctrl+C to exit")

    try:
        while True:
            # Check if left mouse button is pressed
            if GetKeyState(0x01) < 0:  # 0x01 is left mouse button
                # Calculate relative movement downward
                # We'll move down by small increments
                dy = int(3 * get_speed())

                # Send direct movement command to Arduino
                try:
                    command = f"MOVE 0,{dy},0\r\n"
                    mouse.ser.write(command.encode())
                    response = mouse.ser.readline().decode().strip()
                    print(f"Sent: {command.strip()}, Response: {response}")

                    # Small delay between movements
                    time.sleep(0.01)

                except Exception as e:
                    print(f"Error sending command: {e}")
            else:
                # When button is released, wait a bit longer
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nScript terminated by user")


if __name__ == "__main__":
    main()