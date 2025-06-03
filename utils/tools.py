from ultralytics import YOLO
import ctypes
import psutil
import GPUtil

def get_cpu_gpu_usage():
    total_cpu = psutil.cpu_percent()
    total_gpu = GPUtil.getGPUs()[0].load * 100
    return total_cpu, total_gpu

def cvtmodel(model_path: str, fmt: str):
    model = YOLO(model_path)
    model.export(format=fmt)

def get_screenshot_region(screenshot_size):
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    region_left = (screen_width  - screenshot_size) // 2
    region_top  = (screen_height - screenshot_size) // 2

    region = (
        region_left, 
        region_top, 
        region_left + screenshot_size, 
        region_top + screenshot_size
    )
    return region

def median_of_three(x, max, min):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x
    
if __name__ == "__main__":
    print(get_cpu_gpu_usage())