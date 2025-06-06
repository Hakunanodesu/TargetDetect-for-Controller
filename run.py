import json
import time
import sys
import logging
import traceback
import os
import threading
import tkinter as tk
from tkinter import scrolledtext

import cv2
import numpy as np

from modules.onnx import APV5Experimental
from modules.controller import DualSenseToX360Mapper
from modules.grab_screen import ScreenGrabber
from utils.tools import get_screenshot_region_dxcam
from init import InitApp


class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        if s.strip():
            self.text_widget.after(0, self.text_widget.insert, tk.END, s)
            self.text_widget.after(0, self.text_widget.see, tk.END)

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TGC v0.1.0")

        self.running = False
        self.thread = None

        self.button = tk.Button(root, text="启动", command=self.toggle)
        self.button.pack(pady=10)

        self.output = scrolledtext.ScrolledText(root, height=15, width=80, state='normal')
        self.output.pack()

        # 新增延迟信息显示 Label
        self.latency_label = tk.Label(root, text="延迟信息：等待数据...", font=("Arial", 10), justify=tk.LEFT)
        self.latency_label.pack(pady=5, anchor='w')

        # 重定向标准输出
        sys.stdout = StdoutRedirector(self.output)
        sys.stdout.write("点击“开始”按钮启动程序。")

    def update_latency_label(self, text):
        self.latency_label.config(text=text)

    def toggle(self):
        if not self.running:
            self.running = True
            self.button.config(text="停止")
            self.thread = threading.Thread(target=self.run_logic, daemon=True)
            self.thread.start()
        else:
            self.running = False
            self.button.config(text="启动")
            # 恢复label默认文字
            self.update_latency_label("延迟信息：等待数据...")


    def run_logic(self):
        try:
            # 检查配置文件，如果不存在则先弹出初始化窗口
            if not os.path.exists("configs/cfg_global.json"):
                sys.stdout.write("\n未检测到配置文件，开始初始化...")
                # 使用一个新的顶级窗口弹出初始化界面
                init_root = tk.Toplevel(self.root)
                init_app = InitApp(init_root)

                # 阻塞等待初始化窗口关闭（InitApp里退出会调用 root.quit()）
                init_root.wait_window()

                # 再次检查配置文件是否生成，没生成则退出
                if not os.path.exists("configs/cfg_global.json"):
                    sys.stdout.write("\n配置文件未生成，程序退出。")
                    self.running = False
                    self.root.after(0, self.button.config, {"text": "启动"})
                    self.root.after(0, self.update_latency_label, "延迟信息：等待数据...")
                    return

            with open("configs/cfg_global.json", "r") as f:
                config = json.load(f)
            vendor_id = int(config["controller"]["Vendor_ID"], 16)
            product_id = int(config["controller"]["Product_ID"], 16)

            mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
            mapper.start()

            sys.stdout.write("\n正在载入配置文件并启动...（点击“停止”退出）")

            track_strength = config["track_settings"]["track_strength"]
            snap_strength = config["track_settings"]["snap_strength"]
            hipfire_scale = config["track_settings"]["hipfire_scale"]
            snap_size = config["track_settings"]["snap_size"]
            snap_center = snap_size / 2
            screenshot_size = config["track_settings"]["track_size"]
            img_center = screenshot_size / 2
            model_path = config["model_path"]

            camera = ScreenGrabber(region=get_screenshot_region_dxcam(screenshot_size))
            model = APV5Experimental(model_path)

            sys.stdout.write(f"\n当前 EP：{model.provider}")
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
                    result and
                    (mapper.dual_sense_state["rt"] > 127 or mapper.dual_sense_state["lt"] > 255)
                ):
                    xy_result = result - img_center
                    distances = np.abs(xy_result[:, 0]) + np.abs(xy_result[:, 1])
                    min_idx = distances.argmin()
                    s_strength = snap_strength
                    t_strength = track_strength
                    if mapper.dual_sense_state["lt"] < 127:
                        s_strength *= hipfire_scale
                        t_strength *= hipfire_scale
                    if (np.abs(xy_result[min_idx]) < snap_center).all():
                        rx_offset = xy_result[min_idx][0] * (255 / snap_size) * s_strength
                        ry_offset = xy_result[min_idx][1] * (255 / snap_size) * s_strength
                    else:
                        rx_offset = xy_result[min_idx][0] * (255 / screenshot_size) * t_strength
                        ry_offset = xy_result[min_idx][1] * (255 / screenshot_size) * t_strength
                    mapper.add_rx_ry_offset(rx_offset, ry_offset)
                else:
                    mapper.rx_override = None
                    mapper.ry_override = None

                cycle_end = time.perf_counter()
                cycle_latency = (cycle_end - cycle_start) * 1000

                now = time.time()
                if now - last_print_time > 1:
                    latency_str = (
                        f"[Latency] full cycle: {cycle_latency:.3f} ms\n"
                        f"[Latency] screen grab: {grab_latency:.3f} ms\n"
                        f"[Latency] inference: {infer_latency:.3f} ms"
                    )
                    # 线程安全更新延迟Label
                    self.root.after(0, self.update_latency_label, latency_str)
                    last_print_time = now

            mapper.stop()
            cv2.destroyAllWindows()
            time.sleep(1)
            sys.stdout.write("\n已停止。")

        except Exception as e:
            logging.error("发生异常：%s", str(e))
            logging.error("异常类型：%s", type(e).__name__)
            logging.error("完整堆栈信息：\n%s", traceback.format_exc())
            self.running = False
            self.button.config(text="启动")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()





# import json
# import time
# import sys
# import logging
# import traceback
# import os

# import cv2
# import numpy as np

# from modules.onnx import APV5Experimental
# from modules.controller import DualSenseToX360Mapper
# from modules.grab_screen import ScreenGrabber
# from utils.tools import get_screenshot_region_dxcam


# """
# 直接运行脚本时，会创建 YourControllerToX360Mapper 实例并启动映射。
# 按 Ctrl+C 终止循环并退出。
# """
# try:
#     print("你可以在任何时候通过 Ctrl+C 退出程序")

#     if not os.path.exists("configs/cfg_global.json"):
#         from init import main as init_main
#         if init_main() != 0:
#             raise KeyboardInterrupt

#     with open("configs/cfg_global.json", "r") as f:
#         config = json.load(f)
#     vendor_id = int(config["controller"]["Vendor_ID"], 16)
#     product_id = int(config["controller"]["Product_ID"], 16)

#     mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
#     mapper.start()

#     print("\n正在载入配置文件并启动...（Ctrl+C 退出）")

#     try:
#         with open("configs/cfg_global.json", "r") as f:
#             config = json.load(f)
#         track_strength = config["track_settings"]["track_strength"]
#         snap_strength = config["track_settings"]["snap_strength"]
#         hipfire_scale = config["track_settings"]["hipfire_scale"]
#         snap_size = config["track_settings"]["snap_size"]
#         snap_center = snap_size / 2
#         screenshot_size = config["track_settings"]["track_size"]
#         img_center = screenshot_size / 2
#         model_path = config["model_path"]
        
#         # 加载截图
#         camera = ScreenGrabber(region=get_screenshot_region_dxcam(screenshot_size))

#         # 加载推理模型
#         model = APV5Experimental(model_path)

#         last_print_time = time.time()
#         print(f"\n当前 EP：{model.provider}\n\n\n")
#         while True:
#             cycle_start = time.perf_counter()
            
#             grab_start = time.perf_counter()
#             img = camera.grab_frame()
#             if img is None:
#                 continue
#             grab_end = time.perf_counter()
#             grab_latency = (grab_end - grab_start) * 1000

#             infer_start = time.perf_counter()
#             result, image = model.predict(img)
#             infer_end = time.perf_counter()
#             infer_latency = (infer_end - infer_start) * 1000

#             if (
#                 result and \
#                 (mapper.dual_sense_state["rt"] > 127 or mapper.dual_sense_state["lt"] > 255)
#             ):
#                 xy_result = result - img_center
#                 #中心距离排序
#                 distances = np.abs(xy_result[:, 0]) + np.abs(xy_result[:, 1])
#                 min_idx = distances.argmin()
#                 s_strength = snap_strength
#                 t_strength = track_strength
#                 if mapper.dual_sense_state["lt"] < 127:
#                     s_strength *= hipfire_scale
#                     t_strength *= hipfire_scale
#                 if (np.abs(xy_result[min_idx]) < snap_center).all():
#                     rx_offset = xy_result[min_idx][0] * (255 / snap_size) * s_strength
#                     ry_offset = xy_result[min_idx][1] * (255 / snap_size) * s_strength
#                 else:
#                     rx_offset = xy_result[min_idx][0] * (255 / screenshot_size) * t_strength
#                     ry_offset = xy_result[min_idx][1] * (255 / screenshot_size) * t_strength
#                 mapper.add_rx_ry_offset(
#                     rx_offset,
#                     ry_offset
#                 )
#             else:
#                 mapper.rx_override = None
#                 mapper.ry_override = None

#             # # 预览窗口（调试用，正常使用时请注释掉）
#             # annotated_frame = image
#             # cv2.imshow("Detection", annotated_frame)
#             # # 加上这一行，避免窗口卡死。1 毫秒内没有按键则返回 -1
#             # if cv2.waitKey(1) & 0xFF == ord('q'):
#             #     # 按 q 键可退出循环
#             #     raise KeyboardInterrupt
                
#             cycle_end = time.perf_counter()
#             cycle_latency = (cycle_end - cycle_start) * 1000

#             # cpu_usg, gpu_usg = get_cpu_gpu_usage()

#             now = time.time()
#             if now - last_print_time > 1:
#                 # \r 回到行首，end='' 避免换行，flush=True 保证立即输出
#                 sys.stdout.write("\033[3A")
#                 sys.stdout.write(f"\r\033[K[Latency] full cycle 耗时：{cycle_latency:.3f} ms\n")
#                 sys.stdout.write(f"\r\033[K[Latency] screen grab 耗时：{grab_latency:.3f} ms\n")
#                 sys.stdout.write(f"\r\033[K[Latency] inference 耗时：{infer_latency:.3f} ms\n")
#                 # sys.stdout.write(f"\r\033[K[Usage] CPU: {cpu_usg:.2f}% GPU: {gpu_usg:.2f}%\n")
#                 sys.stdout.flush()
#                 last_print_time = now
#     except KeyboardInterrupt:
#         pass
#     except Exception as e:
#         logging.error("发生异常：%s", str(e))
#         logging.error("异常类型：%s", type(e).__name__)
#         logging.error("完整堆栈信息：\n%s", traceback.format_exc())
# except KeyboardInterrupt:
#     pass
# finally:
#     try:
#         mapper.stop()
#         cv2.destroyAllWindows()

#         time.sleep(1)
#     except:
#         pass
#     print("已退出")