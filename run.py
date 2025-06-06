import cv2
import json
import time
import sys
import logging
import traceback
import os
import numpy as np

from modules.onnx import APV5Experimental
from modules.controller import DualSenseToX360Mapper
from modules.grab_screen import ScreenGrabber
from utils.tools import get_screenshot_region_dxcam


"""
直接运行脚本时，会创建 YourControllerToX360Mapper 实例并启动映射。
按 Ctrl+C 终止循环并退出。
"""
try:
    print("你可以在任何时候通过 Ctrl+C 退出程序")

    if not os.path.exists("configs/cfg_global.json"):
        from init import main as init_main
        if init_main() != 0:
            raise KeyboardInterrupt

    with open("configs/cfg_global.json", "r") as f:
        config = json.load(f)
    vendor_id = int(config["controller"]["Vendor_ID"], 16)
    product_id = int(config["controller"]["Product_ID"], 16)

    mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
    mapper.start()

    while True:
        print("\n3s 后重新载入配置文件并启动...（Ctrl+C 退出）")
        time.sleep(3)

        try:
            with open("configs/cfg_global.json", "r") as f:
                config = json.load(f)
            track_strength = config["track_settings"]["track_strength"]
            snap_strength = config["track_settings"]["snap_strength"]
            hipfire_scale = config["track_settings"]["hipfire_scale"]
            snap_size = config["track_settings"]["snap_size"]
            snap_center = snap_size / 2
            screenshot_size = config["track_settings"]["track_size"]
            img_center = screenshot_size / 2
            model_path = config["model_path"]
            
            # 加载截图
            camera = ScreenGrabber(region=get_screenshot_region_dxcam(screenshot_size))

            # 加载推理模型
            model = APV5Experimental(model_path)

            last_print_time = time.time()
            print(f"\n当前 EP：{model.provider}\n\n\n")
            while True:
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
                    result and \
                    (mapper.dual_sense_state["rt"] > 127 or mapper.dual_sense_state["lt"] > 255)
                ):
                    xy_result = result - img_center
                    #中心距离排序
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
                    mapper.add_rx_ry_offset(
                        rx_offset,
                        ry_offset
                    )
                else:
                    mapper.rx_override = None
                    mapper.ry_override = None

                # # 预览窗口（调试用，正常使用时请注释掉）
                # annotated_frame = image
                # cv2.imshow("Detection", annotated_frame)
                # # 加上这一行，避免窗口卡死。1 毫秒内没有按键则返回 -1
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     # 按 q 键可退出循环
                #     raise KeyboardInterrupt
                    
                cycle_end = time.perf_counter()
                cycle_latency = (cycle_end - cycle_start) * 1000

                # cpu_usg, gpu_usg = get_cpu_gpu_usage()

                now = time.time()
                if now - last_print_time > 1:
                    # \r 回到行首，end='' 避免换行，flush=True 保证立即输出
                    sys.stdout.write("\033[3A")
                    sys.stdout.write(f"\r\033[K[Latency] full cycle 耗时：{cycle_latency:.3f} ms\n")
                    sys.stdout.write(f"\r\033[K[Latency] screen grab 耗时：{grab_latency:.3f} ms\n")
                    sys.stdout.write(f"\r\033[K[Latency] inference 耗时：{infer_latency:.3f} ms\n")
                    # sys.stdout.write(f"\r\033[K[Usage] CPU: {cpu_usg:.2f}% GPU: {gpu_usg:.2f}%\n")
                    sys.stdout.flush()
                    last_print_time = now
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.error("发生异常：%s", str(e))
            logging.error("异常类型：%s", type(e).__name__)
            logging.error("完整堆栈信息：\n%s", traceback.format_exc())
except KeyboardInterrupt:
    pass
finally:
    try:
        mapper.stop()
        cv2.destroyAllWindows()
    except:
        pass
    print("已退出")