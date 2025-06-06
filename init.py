import time
import json
import logging
import traceback
import os

from utils.tools import enum_hid_devices, find_model_files, get_nvidia_gpu_info, cvtmodel, get_cpu_info


def main():
    try:
        print(">>> 请根据提示操作以完成初始配置，您可以在任何时候按 Ctrl+C 退出。（回车以继续）")
        input()
        if not os.path.exists("configs/cfg_global.json"):
            config = {
                "track_settings": {
                    "track_size": 320,
                    "track_strength": 0.4,
                    "snap_size": 100,
                    "snap_strength": 0.8,
                    "hipfire_scale": 0.8
                },
                "model_path": "./apv5.onnx",
                "controller": {
                    "Vendor_ID": "0x054C",
                    "Product_ID": "0x0DF2"
                }
            }
        else:
            with open("configs/cfg_global.json", "r") as f:
                config = json.load(f)

        while True:
            flag = input(">>> 1. 初始化手柄配置（yes/no）")
            if flag.lower() == "yes":
                print(">>> 开始枚举当前 HID 设备 ...")
                prev_devices = enum_hid_devices()
                print(f">>> 初始检测到 {len(prev_devices)} 台 HID 设备。")
                print(">>> 请插入或拔出手柄设备。")
                
                poll_interval=1.0
                while True:
                    time.sleep(poll_interval)
                    curr_devices = enum_hid_devices()

                    # 找出设备变化
                    device = (curr_devices - prev_devices) | (prev_devices - curr_devices) # | {(1,2,3)}

                    if len(device) == 1:
                        for (vid, pid, path) in device:
                            print(f"[检测到设备] VID=0x{vid:04X}  PID=0x{pid:04X}  PATH={path}")
                            config["controller"]["Vendor_ID"] = f"0x{vid:04X}"
                            config["controller"]["Product_ID"] = f"0x{pid:04X}"
                        print(">>> 手柄配置完成。")
                        break
                    elif len(device) > 1:
                        print(">>> 检测到多个设备变化，请重新插入/拔出手柄，并保证其他设备不变。")

                    # 更新上一轮设备集
                    prev_devices = curr_devices
                break
            elif flag.lower() == "no":
                print(">>> 跳过手柄配置。")
                break
            else:
                print(">>> 输入无效，请重新输入。")

        while True:
            flag = input(">>> 2. 初始化截图配置（yes/no）")
            if flag.lower() == "yes":
                info = "通常来说不管您使用的是 NVIDIA GPU 还是 AMD GPU，dxcam 都能提供更高的性能，但若是您遇到了卡顿的情况，请切换回 mss。"
                while True:
                    method = input(f">>> 请选择要使用的截图方法。{info}（dxcam/mss）：")
                    info = ""
                    if method == "dxcam" or method == "mss":
                        config["screenshot_settings"]["method"] = method
                        break
                    else:
                        print(">>> 输入无效，请重新输入。")
                print(">>> 截图配置完成。")
                break
            elif flag.lower() == "no":
                print(">>> 跳过截图配置。")
                break
            else:
                print(">>> 输入无效，请重新输入。")

        while True:
            flag = input(">>> 3. 初始化模型配置（yes/no）")
            if flag.lower() == "yes":
                print(">>> 开始枚举工作目录下的模型文件。")
                files = find_model_files()
                print(f">>> 检测到 {len(files)} 个模型文件。")
                for i, file in enumerate(files):
                    print(f"[{i}] {file}")
                msg = ">>> 请选择要使用的模型文件（输入序号）："
                while True:
                    index = input(msg)
                    if index.isdigit() and 0 <= int(index) < len(files):
                        config["model_path"] = files[int(index)]

                        suffix = config["model_path"].split(".")[-1]
                        if suffix != "onnx":
                            msg = ">>> 检测到非 ONNX 格式模型权重文件，请重新选择（输入序号）:"
                        else:
                            break
                    else:
                        print(">>> 输入无效，请重新输入。")
                print(">>> 模型配置完成。")
                break
            elif flag.lower() == "no":
                print(">>> 跳过模型配置。")
                break
            else:
                print(">>> 输入无效，请重新输入。")
        
        config["first_run"] = False
        with open("configs/cfg_global.json", "w") as f:
            json.dump(config, f, indent=4)
        print(">>> 初始配置完成。")
    except KeyboardInterrupt:
        print("\n>>> 程序已停止。")
    except Exception as e:
        logging.error("发生异常：%s", str(e))
        logging.error("异常类型：%s", type(e).__name__)
        logging.error("完整堆栈信息：\n%s", traceback.format_exc())


if __name__ == "__main__":
    main()
