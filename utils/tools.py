from ultralytics import YOLO
import ctypes
# import psutil
# import GPUtil
import mss
from pywinusb import hid
from pathlib import Path


def find_model_files():
    """
    在当前工作目录（及其子目录）中查找后缀为 .pt、.onnx、.engine 的文件，
    并返回它们相对于当前工作目录的路径列表。
    """
    cwd = Path.cwd()
    extensions = {'.pt', '.onnx', '.engine'}
    result = []

    for path in cwd.rglob('*'):
        if path.is_file() and path.suffix.lower() in extensions:
            # 将绝对路径转换为相对于 cwd 的相对路径
            rel_path = path.relative_to(cwd)
            result.append("./" + str(rel_path).replace('\\', '/'))

    return result

# def get_cpu_gpu_usage():
#     total_cpu = psutil.cpu_percent()
#     total_gpu = GPUtil.getGPUs()[0].load * 100
#     return total_cpu, total_gpu

def cvtmodel(model_path: str, fmt: str):
    model = YOLO(model_path)
    model.export(format=fmt)

def get_screenshot_region_dxcam(screenshot_size):
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

def enum_hid_devices():
    """
    枚举系统中所有 HID 设备，返回一个集合（set），
    其中每个元素为三元组 (vendor_id, product_id, device_path)。
    之所以包含 device_path，是为了区分同样 VID/PID 但路径不同的多个设备。
    """
    device_set = set()
    # 创建一个 HID 设备筛选器，不指定任何 VID/PID，表示获取所有 HID 设备
    all_devices = hid.HidDeviceFilter().get_devices()
    for device in all_devices:
        try:
            vid = device.vendor_id
            pid = device.product_id
            path = device.device_path  # 唯一标识此设备的路径
            device_set.add((vid, pid, path))
        except Exception:
            # 某些设备可能取不到 vendor_id/product_id，就跳过
            continue
    return device_set

def median_of_three(x, max, min): # 比min，max嵌套函数更快
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x
    
    
if __name__ == "__main__":
    # print(get_cpu_gpu_usage())
    pass