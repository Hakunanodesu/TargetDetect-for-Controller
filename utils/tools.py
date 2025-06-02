import mss
from ultralytics import YOLO

def cvtmodel(model_path: str, fmt: str):
    model = YOLO(model_path)
    model.export(format=fmt)

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

def median_of_three(x, max, min):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x