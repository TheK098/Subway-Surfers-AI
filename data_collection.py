import cv2
import numpy as np
import time
import mss
import win32gui
import os
import shutil
import threading
import keyboard  # Ensure this is installed
import pyuac  # pyuac is required for admin check

# List of keys to monitor
keys_to_monitor = ['left', 'right', 'up', 'down']
key_lock = threading.Lock()
key_presses = []

# Function to find the coordinates of the specific window
def get_window_coordinates(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return rect
    else:
        print("Window not found!")
        return None

# Function to handle key press events
def on_key_event(event):
    if event.name in keys_to_monitor and event.event_type == 'down':
        with key_lock:
            if event.name not in key_presses:
                key_presses.append(event.name)

# Function to get the current state of keys
def get_key_state():
    with key_lock:
        pressed_keys = key_presses.copy()
        key_presses.clear()
    return '+'.join(pressed_keys)

# Thread function for capturing screenshots
def capture_window_screenshots(window_name, interval=0.15, save_folder="data"):
    rect = get_window_coordinates(window_name)
    if rect:
        x1, y1, x2, y2 = rect
        monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
        count = 0
        with mss.mss() as sct:
            while True:
                start_time = time.perf_counter()

                # Capture the screenshot
                img = sct.grab(monitor)
                img = np.array(img)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # Get the current key state
                keys_pressed = get_key_state()

                # Save the screenshot with key info in filename
                filename = os.path.join(save_folder, f"screenshot_{count:04d}_{keys_pressed}.png")
                cv2.imwrite(filename, img)
                count += 1

                # Wait to make up the interval
                elapsed = time.perf_counter() - start_time
                time.sleep(max(0, interval - elapsed))

def main():
    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    window_name = "BlueStacks App Player"

    # Start the key event listener
    keyboard.hook(on_key_event)

    # Start the screenshot capturing thread
    threading.Thread(target=capture_window_screenshots, args=(window_name,), daemon=True).start()
    
    keyboard.wait('esc')  # Press 'esc' to exit the script

if __name__ == "__main__":
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()
    else:
        main()
