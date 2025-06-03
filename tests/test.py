import threading
import queue
import time
from modules.grab_screen import ScreenGrabber
from utils.tools import get_screenshot_region

screenshot_size = (1920, 1080)  # 屏幕分辨率

frame_queue = queue.Queue(maxsize=5)  # 控制内存占用，避免过多帧堆积

camera = ScreenGrabber(region=get_screenshot_region(screenshot_size))

def grab_screen_thread(camera):
    while True:
        frame = camera.get_latest_frame()
        if frame is not None:
            if not frame_queue.full():
                frame_queue.put(frame)
        time.sleep(0.001)  # 可调节以平衡 CPU
