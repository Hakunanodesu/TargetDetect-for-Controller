import tkinter as tk
import json
import os
import time
from utils.tools import enum_hid_devices, find_model_files


class InitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("初始化配置")
        self.config = {
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

        self.text = tk.Text(root, height=20, width=80, state='disabled')
        self.text.pack(padx=10, pady=5)

        self.entry = tk.Entry(root, width=80)
        self.entry.bind("<Return>", self.process_input)
        self.entry.pack(padx=10, pady=5)
        self.entry.focus()

        self.step = self.step_controller
        self.root.after(100, lambda: self.step())
    
    def _print(self, msg):
        self.text.config(state='normal')
        self.text.insert(tk.END, msg + "\n")
        self.text.see(tk.END)
        self.text.config(state='disabled')

    def process_input(self, event):
        user_input = self.entry.get().strip().lower()
        self.entry.delete(0, tk.END)
        self.step(user_input)

    def step_controller(self, user_input=None):
        self._print(">>> 正在初始化手柄配置...")
        self._print(">>> 开始枚举当前 HID 设备...")
        self.prev_devices = enum_hid_devices()
        self._print(f">>> 初始检测到 {len(self.prev_devices)} 台 HID 设备。")
        self._print(">>> 请插入/拔出手柄设备...")

        self._poll_controller()
        self.step = self.step_model

    def _poll_controller(self):
        curr_devices = enum_hid_devices()
        diff = (curr_devices - self.prev_devices) | (self.prev_devices - curr_devices)

        if len(diff) == 1:
            for (vid, pid, path) in diff:
                self.config["controller"]["Vendor_ID"] = f"0x{vid:04X}"
                self.config["controller"]["Product_ID"] = f"0x{pid:04X}"
                self._print(f"[检测到设备] VID=0x{vid:04X} PID=0x{pid:04X}")
            self._print(">>> 手柄配置完成。")
            self.root.after(500, self.step_model)  # 稍等后执行模型选择步骤
        elif len(diff) > 1:
            self._print(">>> 检测到多个设备变化，请重试。")
            self.prev_devices = curr_devices
            self.root.after(1000, self._poll_controller)
        else:
            self.prev_devices = curr_devices
            self.root.after(1000, self._poll_controller)

    def step_model(self):
        self._print(">>> 正在初始化模型配置...")
        self._print(">>> 开始枚举模型文件...")
        self._poll_model_files()

    def _poll_model_files(self):
        files = find_model_files()
        if not files:
            self._print(">>> 未找到模型文件，请放入当前目录，按回车重试。")
            self.step = lambda x: self._poll_model_files()
        else:
            for i, f in enumerate(files):
                self._print(f"[{i}] {f}")
            self._print(">>> 请输入要使用的模型编号：")
            self.step = lambda x: self.select_model(x, files)

    def select_model(self, user_input, files):
        if user_input.isdigit() and 0 <= int(user_input) < len(files):
            self.config["model_path"] = files[int(user_input)]
            self._finish()
        else:
            self._print(">>> 输入无效，请重新输入模型编号：")

    def _finish(self):
        os.makedirs("configs", exist_ok=True)
        with open("configs/cfg_global.json", "w") as f:
            json.dump(self.config, f, indent=4)
        self._print(">>> 配置完成，窗口将自动关闭。")
        self.root.after(1000, self.root.destroy)







# import time
# import json
# import logging
# import traceback
# import os
# import sys

# from utils.tools import enum_hid_devices, find_model_files


# def main():
#     try:
#         sys.stdout.write("\n>>> 请根据提示操作以完成初始配置，您可以在任何时候按 Ctrl+C 退出。（回车以继续）")
#         input()
#         if not os.path.exists("configs/cfg_global.json"):
#             config = {
#                 "track_settings": {
#                     "track_size": 320,
#                     "track_strength": 0.4,
#                     "snap_size": 100,
#                     "snap_strength": 0.8,
#                     "hipfire_scale": 0.8
#                 },
#                 "model_path": "./apv5.onnx",
#                 "controller": {
#                     "Vendor_ID": "0x054C",
#                     "Product_ID": "0x0DF2"
#                 }
#             }
#         else:
#             with open("configs/cfg_global.json", "r") as f:
#                 config = json.load(f)

#         while True:
#             flag = input(">>> 1. 初始化手柄配置（yes/no）")
#             if flag.lower() == "yes":
#                 sys.stdout.write(">>> 开始枚举当前 HID 设备 ...")
#                 prev_devices = enum_hid_devices()
#                 sys.stdout.write(f">>> 初始检测到 {len(prev_devices)} 台 HID 设备。")
#                 sys.stdout.write(">>> 请插入或拔出手柄设备。")
                
#                 poll_interval=1.0
#                 while True:
#                     time.sleep(poll_interval)
#                     curr_devices = enum_hid_devices()

#                     # 找出设备变化
#                     device = (curr_devices - prev_devices) | (prev_devices - curr_devices) # | {(1,2,3)}

#                     if len(device) == 1:
#                         for (vid, pid, path) in device:
#                             sys.stdout.write(f"[检测到设备] VID=0x{vid:04X}  PID=0x{pid:04X}  PATH={path}")
#                             config["controller"]["Vendor_ID"] = f"0x{vid:04X}"
#                             config["controller"]["Product_ID"] = f"0x{pid:04X}"
#                         sys.stdout.write(">>> 手柄配置完成。")
#                         break
#                     elif len(device) > 1:
#                         sys.stdout.write(">>> 检测到多个设备变化，请重新插入/拔出手柄，并保证其他设备不变。")

#                     # 更新上一轮设备集
#                     prev_devices = curr_devices
#                 break
#             elif flag.lower() == "no":
#                 sys.stdout.write(">>> 跳过手柄配置。")
#                 break
#             else:
#                 sys.stdout.write(">>> 输入无效，请重新输入。")

#         while True:
#             flag = input(">>> 2. 初始化模型配置（yes/no）")
#             if flag.lower() == "yes":
#                 sys.stdout.write(">>> 开始枚举工作目录下的模型文件。")
#                 while True:
#                     files = find_model_files()
#                     sys.stdout.write(f">>> 检测到 {len(files)} 个模型文件。")
#                     if len(files) == 0:
#                         input(">>> 未检测到模型文件，请将模型文件放置在当前工作目录下。（回车以重新检测）")
#                         continue
#                     else:
#                         break
#                 for i, file in enumerate(files):
#                     sys.stdout.write(f"[{i}] {file}")
#                 msg = ">>> 请选择要使用的模型文件（输入序号）："
#                 while True:
#                     index = input(msg)
#                     if index.isdigit() and 0 <= int(index) < len(files):
#                         config["model_path"] = files[int(index)]
#                         break
#                     else:
#                         sys.stdout.write(">>> 输入无效，请重新输入。")
#                 sys.stdout.write(">>> 模型配置完成。")
#                 break
#             elif flag.lower() == "no":
#                 sys.stdout.write(">>> 跳过模型配置。")
#                 break
#             else:
#                 sys.stdout.write(">>> 输入无效，请重新输入。")
        
#         with open("configs/cfg_global.json", "w") as f:
#             json.dump(config, f, indent=4)
#         sys.stdout.write(">>> 初始配置完成。")
#         return 0
#     except KeyboardInterrupt:
#         sys.stdout.write("\n>>> 程序已停止。")
#         return 1
#     except Exception as e:
#         logging.error("发生异常：%s", str(e))
#         logging.error("异常类型：%s", type(e).__name__)
#         logging.error("完整堆栈信息：\n%s", traceback.format_exc())
#         return 1


# if __name__ == "__main__":
#     main()
