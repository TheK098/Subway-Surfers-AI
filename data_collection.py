import cv2
import numpy as np
import time
import mss
import win32gui
import os
import shutil
import threading
import keyboard
import pyuac

keys_to_monitor = ['left', 'right', 'up', 'down']
key_lock = threading.Lock()
key_presses = []

def get_window_coordinates(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return rect
    else:
        print("Window not found!")
        return None

def on_key_event(event):
    if event.name in keys_to_monitor and event.event_type == 'down':
        with key_lock:
            if event.name not in key_presses:
                key_presses.append(event.name)

def get_key_state():
    with key_lock:
        pressed_keys = key_presses.copy()
        key_presses.clear()
    return '+'.join(pressed_keys)

def capture_window_screenshots(window_name, interval=0.15, save_folder="data", downsample_factor=2, jpeg_quality=90):
    rect = get_window_coordinates(window_name)
    if rect:
        x1, y1, x2, y2 = rect
        monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
        count = 0
        with mss.mss() as sct:
            while True:
                start_time = time.perf_counter()
                img = sct.grab(monitor)
                img = np.array(img)

                # Crop a few pixels off the top and right
                cropped_img = img[35:, :-35]

                # Convert to grayscale
                gray_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGRA2GRAY)

                # Downsample the image
                downsampled_width = gray_img.shape[1] // downsample_factor
                downsampled_height = gray_img.shape[0] // downsample_factor
                downsampled_img = cv2.resize(gray_img, (downsampled_width, downsampled_height), interpolation=cv2.INTER_AREA)

                keys_pressed = get_key_state()
                filename = os.path.join(save_folder, f"screenshot_{count:04d}_{keys_pressed}.jpg")

                # Save the image as JPEG with specified quality
                cv2.imwrite(filename, downsampled_img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                count += 1
                elapsed = time.perf_counter() - start_time
                time.sleep(max(0, interval - elapsed))

def main():
    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")
    window_name = "BlueStacks App Player"
    
    downsample_factor = 3 
    jpeg_quality = 90 
    keyboard.hook(on_key_event)
    threading.Thread(target=capture_window_screenshots, args=(window_name, 0.15, "data", downsample_factor, jpeg_quality), daemon=True).start()
    keyboard.wait('esc')

if __name__ == "__main__":
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()
    else:
        main()
