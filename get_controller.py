# -*- coding: utf-8 -*-
"""
脚本功能：
1. 通过 pywinusb.hid 枚举当前系统中的所有 HID 设备；
2. 周期性（例如每秒）再次枚举，并与上一次枚举结果比较，找出新增或移除的设备；
3. 当检测到有设备插入或拔出时，打印出该设备的 Vendor ID (VID) 和 Product ID (PID)。

使用方法：
1. 先确保已通过 pip 安装 pywinusb：
       pip install pywinusb
2. 保存本脚本为例如 monitor_hid.py，使用 Python 运行：
       python monitor_hid.py
3. 插拔 HID 设备，观察控制台输出。

注意：
- 本脚本采用轮询方式检测设备变化，延迟取决于轮询间隔（本例为 1 秒）。
- 如果需要更低延迟，可适当减小 sleep 时间，但也会增大 CPU 占用。
"""

import time
from pywinusb import hid

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

def main(poll_interval=1.0):
    """
    主函数：不断轮询并检测插拔事件
    参数：
        poll_interval：轮询间隔，单位秒
    """
    print(">>> 开始枚举当前 HID 设备 ...")
    prev_devices = enum_hid_devices()
    print(f">>> 初始检测到 {len(prev_devices)} 台 HID 设备。")
    print(">>> 请插入或拔出 HID 设备以查看实时变化（按 Ctrl+C 退出）。\n")

    try:
        while True:
            time.sleep(poll_interval)
            curr_devices = enum_hid_devices()

            # 找出新增设备：curr_devices 中有，prev_devices 中没有
            added = curr_devices - prev_devices
            # 找出移除设备：prev_devices 中有，curr_devices 中没有
            removed = prev_devices - curr_devices

            if added:
                for (vid, pid, path) in added:
                    print(f"[检测到设备插入] VID=0x{vid:04X}  PID=0x{pid:04X}  PATH={path}")

            if removed:
                for (vid, pid, path) in removed:
                    print(f"[检测到设备拔出] VID=0x{vid:04X}  PID=0x{pid:04X}  PATH={path}")

            # 更新上一轮设备集
            prev_devices = curr_devices

    except KeyboardInterrupt:
        print("\n>>> 程序已停止。")


if __name__ == "__main__":
    main(poll_interval=1.0)
