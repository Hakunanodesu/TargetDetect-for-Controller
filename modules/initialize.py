import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import json
import sys

from utils.tools import enum_hid_devices, find_model_files
from modules.delay_stdout import DelayedStdoutRedirector


class InitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("初始化配置")
        self.force_quit = True
        self.running = True  # 添加运行标志
        self.root.rowconfigure(0, weight=1)  # ScrolledText 这一行可伸缩
        self.root.rowconfigure(2, weight=0)  # Entry 一行高度固定
        self.root.columnconfigure(0, weight=1)  # 唯一一列可伸缩

        # 文本输出区 using ScrolledText
        self.text = scrolledtext.ScrolledText(root, height=20, width=80, state='disabled')
        self.text.grid(row=0, column=0, sticky="nsew")

        # Redirect stdout to delayed redirector
        sys.stdout = DelayedStdoutRedirector(self.text, interval_ms=50)

        vcmd = (self.root.register(self._validate_number), '%P')
        self.entry = tk.Entry(root, state="disabled", validate='key', validatecommand=vcmd)
        self.entry.bind("<Return>", self._on_entry)
        self.entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5, ipady=8)
        self.entry.focus()

        self.config = {
            "model_path": "apv5.onnx",
            "controller": {
                "Vendor_ID": "0x054C",
                "Product_ID": "0x0DF2"
            },
            "detect_settings": {
                "range": {
                    "outer": 480,
                    "middle": 320,
                    "inner": 80
                },
                "curve": {
                    "outer": [
                        0.15,
                        0.15
                    ],
                    "inner": [
                        0.0,
                        1.0
                    ]
                },
                "hipfire_scale": 0.7
            }
        }

        sys.stdout.write(">>> 正在初始化手柄配置...")
        self.prev_devices = enum_hid_devices()
        sys.stdout.write(f">>> 初始检测到 {len(self.prev_devices)} 台 HID 设备。请插入/拔出手柄设备...")
        self.poll_thread = threading.Thread(target=self._poll_controller_bg, daemon=True)
        self.poll_thread.start()
        
        # 添加窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """窗口关闭时的处理函数"""
        self.running = False  # 停止后台线程
        self.root.destroy()

    def _validate_number(self, proposed_text):
        return proposed_text == "" or proposed_text.isdigit()

    def _poll_controller_bg(self):
        """后台线程：检测 HID 设备插拔"""
        while self.running:  # 使用运行标志控制循环
            curr = enum_hid_devices()
            diff = (curr - self.prev_devices) | (self.prev_devices - curr) # | {(0, 0, 0)}
            if len(diff) == 1:
                vid, pid, _ = next(iter(diff))
                self.config["controller"]["Vendor_ID"] = f"0x{vid:04X}"
                self.config["controller"]["Product_ID"] = f"0x{pid:04X}"
                self.root.after(0, lambda: sys.stdout.write(f"[检测到设备] VID=0x{vid:04X} PID=0x{pid:04X}"))
                self.root.after(0, lambda: self._on_controller_detected(vid, pid))
                break
            elif len(diff) > 1:
                self.prev_devices = curr
                self.root.after(0, lambda: sys.stdout.write(">>> 检测到多个设备变化，请重试。"))
            else:
                self.prev_devices = curr
            time.sleep(1)

    def _on_controller_detected(self, vid, pid):
        sys.stdout.write(">>> 手柄配置完成。")
        sys.stdout.write(">>> 正在初始化模型配置...")
        sys.stdout.write(">>> 开始枚举模型文件…")
        self.entry.config(state="normal")
        self._poll_model_files()

    def _poll_model_files(self):
        files = find_model_files()
        if not files:
            sys.stdout.write(">>> 未找到模型文件，请放入当前目录，按回车重试。")
        else:
            sys.stdout.write(f">>> 检测到 {len(files)} 个模型文件：")
            for i, f in enumerate(files):
                sys.stdout.write(f"[{i}] {f}")
            sys.stdout.write(f">>> 请输入要使用的模型编号（例如：0 代表使用 {files[0]}）...")
            self.model_files = files

    def _on_entry(self, event):
        s = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if hasattr(self, 'model_files'):
            if s.isdigit() and 0 <= int(s) < len(self.model_files):
                self.config["model_path"] = self.model_files[int(s)]
                self._finish()
            else:
                sys.stdout.write(">>> 输入无效，请重新输入模型编号：")
        else:
            sys.stdout.write(">>> 重试枚举模型文件...")
            self._poll_model_files()

    def _finish(self):
        with open("user_config.json", "w") as f:
            json.dump(self.config, f, indent=4)
        sys.stdout.write(">>> 配置完成，窗口将自动关闭。")
        self.force_quit = False
        self.root.after(500, self.root.destroy)


if __name__ == "__main__":
    root = tk.Tk()
    InitApp(root)
    root.mainloop()
