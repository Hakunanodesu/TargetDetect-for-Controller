import mss
import cv2
import numpy as np

def get_screenshot_region(screenshot_size):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screen_width = monitor["width"]
        screen_height = monitor["height"]

        region_width = screenshot_size
        region_height = screenshot_size

        region_left = (screen_width  - region_width ) // 2
        region_top  = (screen_height - region_height) // 2

        region = {
            "left":   region_left,
            "top":    region_top,
            "width":  region_width,
            "height": region_height
        }
    return region

region = get_screenshot_region(640)
with mss.mss() as sct:
    while True:
        img = np.array(sct.grab(region))[:, :, :3]

        # 预览窗口（调试用，正常使用时请注释掉）
        annotated_frame = img
        cv2.imshow(f"Detection", annotated_frame)
        # 加上这一行，避免窗口卡死。1 毫秒内没有按键则返回 -1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # 按 q 键可退出循环
            raise KeyboardInterrupt