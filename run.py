import json
import time
import sys
import logging
import traceback
import os
import threading
import tkinter as tk
from tkinter import scrolledtext

import numpy as np

from modules.onnx import APV5Experimental
from modules.controller import DualSenseToX360Mapper
from modules.grab_screen import ScreenGrabber
from modules.delay_stdout import DelayedStdoutRedirector
from modules.initialize import InitApp
from modules.aim_configurate import CFGApp
from utils.tools import get_screenshot_region_dxcam


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TGC v0.1.0")

        self.running = False
        self.mapper_running = False
        self.logic_started = False  # 标记 run_logic 是否已成功启动
        self.thread = None
        self.mapper = None

        # 按钮容器 Frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        # InitApp control button
        self.init_button = tk.Button(button_frame, text="初始化配置", command=self.start_init)
        self.init_button.pack(side='left', padx=5)

        # CFGApp control button
        self.cfg_button = tk.Button(
            button_frame, 
            text="修改识别配置", 
            state='normal' if os.path.exists("user_config.json") else 'disabled', 
            command=self.open_cfg
        )
        self.cfg_button.pack(side='left', padx=5)

        # Mapper control button
        self.mapper_button = tk.Button(
            button_frame, 
            text="启动手柄映射", 
            state='normal' if os.path.exists("user_config.json") else 'disabled', 
            command=self.toggle_mapper
        )
        self.mapper_button.pack(side='left', padx=5)

        # Main logic button
        self.button = tk.Button(button_frame, text="启动智慧核心", state='disabled', command=self.toggle)
        self.button.pack(side='left', padx=5)

        self.output = scrolledtext.ScrolledText(root, height=15, width=80, state='disabled')
        self.output.pack(fill='both', expand=True)

        self.latency_label = tk.Label(root, text="延迟信息：等待数据...", font=("Arial", 10), justify=tk.LEFT)
        self.latency_label.pack(pady=5, anchor='w')

        sys.stdout = DelayedStdoutRedirector(self.output, interval_ms=50)

    def update_latency_label(self, text):
        self.latency_label.config(text=text)

    def open_cfg(self):
        try:
            sys.stdout.write("\n>>> 正在修改识别配置...")
            cfg_root = tk.Toplevel(self.root)
            cfg_root.grab_set()  # 使子窗口获得焦点，主窗口无法操作
            cfg_app = CFGApp(cfg_root)
            cfg_root.wait_window()
            cfg_root.grab_release()  # 释放焦点
            sys.stdout = DelayedStdoutRedirector(self.output, interval_ms=50)
            if cfg_app.force_quit:
                sys.stdout.write("\n>>> 识别配置修改未完成。")
                return
            sys.stdout.write("\n>>> 识别配置修改完成。")
        except Exception as e:
            if 'cfg_root' in locals():
                cfg_root.grab_release()  # 确保在发生异常时也释放焦点
            sys.stdout.write(f"\n>>> 识别配置修改时出错: {e}")

    def start_init(self):
        try:
            sys.stdout.write("\n>>> 开始初始化配置...")
            init_root = tk.Toplevel(self.root)
            init_root.grab_set()  # 使子窗口获得焦点，主窗口无法操作
            init_app = InitApp(init_root)
            init_root.wait_window()
            init_root.grab_release()  # 释放焦点
            sys.stdout = DelayedStdoutRedirector(self.output, interval_ms=50)
            if init_app.force_quit:
                sys.stdout.write("\n>>> 初始化未完成。")
                return
            sys.stdout.write("\n>>> 配置初始化完成。")
            self.mapper_button.config(state='normal')
            self.cfg_button.config(state='normal')
        except Exception as e:
            if 'init_root' in locals():
                init_root.grab_release()  # 确保在发生异常时也释放焦点
            sys.stdout.write(f"\n>>> 初始化配置时出错: {e}")

    def toggle_mapper(self):
        if not self.mapper_running:
            try:
                with open("user_config.json", "r") as f:
                    config = json.load(f)
                vendor_id = int(config["controller"]["Vendor_ID"], 16)
                product_id = int(config["controller"]["Product_ID"], 16)
                sys.stdout.write("\n>>> 正在启动手柄映射...")
                self.mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
                status = self.mapper.start()
                if status:
                    self.mapper_running = True
                    self.mapper_button.config(text="停止手柄映射")
                    self.button.config(state='normal')
                    self.init_button.config(state='disabled')
                    sys.stdout.write("\n>>> 手柄映射已启动。")
                else:
                    sys.stdout.write("\n>>> 手柄映射启动失败，请检查设备。")
            except Exception as e:
                sys.stdout.write(f"\n>>> 启动映射时出错: {e}")
        else:
            if self.mapper:
                sys.stdout.write("\n>>> 正在停止手柄映射...")
                self.mapper.stop()
            self.mapper_running = False
            sys.stdout.write("\n>>> 手柄映射已停止。")
            self.mapper_button.config(text="启动手柄映射")
            self.button.config(state='disabled')
            self.init_button.config(state='normal')
            if self.running:
                self.toggle()

    def toggle(self):
        if not self.running and self.mapper_running:
            self.running = True
            self.logic_started = False
            sys.stdout.write("\n>>> 正在启动智慧核心...")
            self.button.config(text="关闭智慧核心")
            self.mapper_button.config(state="disabled")
            self.cfg_button.config(state='disabled')
            # 启动线程
            self.thread = threading.Thread(target=self._logic_wrapper, daemon=True)
            self.thread.start()
            # 检测线程是否启动成功
            self.root.after(1000, self._check_logic_started)
        else:
            self.running = False
            sys.stdout.write("\n>>> 正在关闭智慧核心...")
            self.button.config(text="启动智慧核心")
            self.mapper_button.config(state='normal')
            self.cfg_button.config(state='normal')
            self.update_latency_label("延迟信息：等待数据...")

    def _logic_wrapper(self):
        try:
            self.logic_started = True
            self.run_logic()
        except Exception as e:
            logging.error("智慧核心启动失败：%s", str(e))
            logging.error("异常类型：%s", type(e).__name__)
            logging.error("完整堆栈信息：\n%s", traceback.format_exc())
            self.running = False
            self.root.after(0, self._handle_logic_failure)
        finally:
            self.logic_started = False

    def _handle_logic_failure(self):
        self.button.config(text="启动智慧核心")
        self.mapper_button.config(state='normal')
        self.cfg_button.config(state='normal')
        sys.stdout.write("\n>>> 智慧核心启动失败，请检查配置。")

    def _check_logic_started(self):
        if not self.running:
            return
            
        if self.logic_started:
            sys.stdout.write("\n>>> 智慧核心已启动。")
        else:
            if not self.thread.is_alive():
                sys.stdout.write("\n>>> 智慧核心启动失败，请检查配置。")
                self._handle_logic_failure()
            else:
                # 如果线程仍然在运行但未设置标志，继续检查
                self.root.after(100, self._check_logic_started)

    def run_logic(self):
        try:
            def map_range(x: float, a: float, scale: list[float] = [0.2, 0.8]) -> int:
                normalized = x / a
                out_min = 127 * scale[0]
                out_max = 127 * scale[1]
                value = out_min + (out_max - out_min) * abs(normalized)
                return value

            with open("user_config.json", "r") as f:
                config = json.load(f)
            hipfire_scale = config["detect_settings"]["hipfire_scale"]
            strong_size = config["detect_settings"]["range"]["inner"]
            weak_size = config["detect_settings"]["range"]["middle"]
            ident_size = config["detect_settings"]["range"]["outer"]
            strong_center = strong_size / 2
            weak_center = weak_size / 2
            ident_center = ident_size / 2
            curve_inner = config["detect_settings"]["curve"]["inner"]
            curve_outer = config["detect_settings"]["curve"]["outer"]
            model_path = config["model_path"]

            camera = ScreenGrabber(region=get_screenshot_region_dxcam(ident_size))
            model = APV5Experimental(model_path)

            sys.stdout.write(f"\n>>> 智慧核心运行中，当前 EP：{model.provider}")
            last_print_time = time.time()

            while self.running:
                cycle_start = time.perf_counter()
                grab_start = time.perf_counter()
                img = camera.grab_frame()
                if img is None:
                    continue
                grab_end = time.perf_counter()
                grab_latency = (grab_end - grab_start) * 1000

                infer_start = time.perf_counter()
                result, image = model.predict(img)
                infer_end = time.perf_counter()
                infer_latency = (infer_end - infer_start) * 1000

                if (
                    result is not None and \
                    self.mapper.dual_sense_state["rt"] > 128
                ):
                    xy_result = result - ident_center
                    distances = np.abs(xy_result[:, 0]) + np.abs(xy_result[:, 1])
                    min_idx = distances.argmin()
                    strength = 1
                    if self.mapper.dual_sense_state["lt"] < 128:
                        strength *= hipfire_scale
                    euclidean_distance = np.sqrt(np.sum(xy_result[min_idx]**2))
                    cos_angle = xy_result[min_idx][0] / euclidean_distance
                    sin_angle = xy_result[min_idx][1] / euclidean_distance
                    if euclidean_distance < strong_center:
                        map_euclidean_distance = map_range(euclidean_distance, strong_size, curve_inner) * strength
                    elif euclidean_distance < weak_center:
                        map_euclidean_distance = map_range(euclidean_distance, weak_size, curve_outer) * strength
                    else:
                        map_euclidean_distance = 0
                    rx_offset = map_euclidean_distance * cos_angle
                    ry_offset = map_euclidean_distance * sin_angle
                    self.mapper.add_rx_ry_offset(rx_offset, ry_offset)
                else:
                    self.mapper.rx_override = None
                    self.mapper.ry_override = None

                cycle_end = time.perf_counter()
                cycle_latency = (cycle_end - cycle_start) * 1000

                now = time.time()
                if now - last_print_time > 1:
                    latency_str = (
                        f"[Latency] full cycle: {cycle_latency:.3f} ms\n"
                        f"[Latency] screen grab: {grab_latency:.3f} ms\n"
                        f"[Latency] inference: {infer_latency:.3f} ms"
                    )
                    self.root.after(0, self.update_latency_label, latency_str)
                    last_print_time = now

            sys.stdout.write("\n>>> 智慧核心已关闭。")

        except Exception as e:
            logging.error("发生异常：%s", str(e))
            logging.error("异常类型：%s", type(e).__name__)
            logging.error("完整堆栈信息：\n%s", traceback.format_exc())
            self.running = False
            self.root.after(0, self.button.config, {"text": "启动智慧核心"})


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
