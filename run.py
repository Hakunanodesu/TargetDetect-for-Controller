import cv2
import torch
import json
import time
import sys
import mss
import numpy as np

from models.yolo import YOLO11
from modules.controller import DualSenseToX360Mapper
from modules.grab_screen import ScreenGrabber
from utils.tools import get_screenshot_region, get_screenshot_region_dxcam, get_cpu_gpu_usage

if __name__ == "__main__":
    """
    直接运行脚本时，会创建 YourControllerToX360Mapper 实例并启动映射。
    按 Ctrl+C 终止循环并退出。
    """
    try:
        # 检查GPU是否可用
        print(f"正在检查是否支持CUDA...{torch.cuda.is_available()}")
        print("你可以在任何时候通过Ctrl+C退出程序")

        with open("config.json", "r") as f:
            config = json.load(f)
        vendor_id = int(config["controller"]["Vendor_ID"], 16)
        product_id = int(config["controller"]["Product_ID"], 16)

        mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
        mapper.start()

        while True:
            print("\n3s后重新载入配置文件并启动...")
            time.sleep(3)

            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                screenshot_size = config["screenshot_size"]
                track_strength = config["track_settings"]["track_strength"]
                snap_size = config["track_settings"]["snap_size"]
                snap_strength = config["track_settings"]["snap_strength"]
                img_center = screenshot_size / 2
                snap_center = snap_size / 2
                model_path = config["model_path"]
                
                # 加载截图
                camera = ScreenGrabber(region=get_screenshot_region_dxcam(screenshot_size))
                region = get_screenshot_region(screenshot_size)

                # 加载推理模型
                model = YOLO11(model_path)
                model.inference("./datasets/bus.jpg")

                last_print_time = time.time()
                with mss.mss() as sct:
                    print("\n\n\n")
                    while True:
                        cycle_start = time.perf_counter()
                        
                        grab_start = time.perf_counter()
                        img = camera.grab_frame()
                        if img is None:
                            continue
                        # img = np.array(sct.grab(region))[:, :, :3]
                        # time.sleep(0.001)
                        grab_end = time.perf_counter()
                        grab_latency = (grab_end - grab_start) * 1000

                        infer_start = time.perf_counter()
                        result = model.inference(img)
                        infer_end = time.perf_counter()
                        infer_latency = (infer_end - infer_start) * 1000

                        xy_result = result.boxes.xywh[:, :2] - img_center
                        if (
                            xy_result.size(0) != 0 and \
                            (mapper.dual_sense_state["rt"] > 127 or mapper.dual_sense_state["lt"] > 127)
                        ):
                            #中心距离排序
                            distances = torch.abs(xy_result[:, 0]) + \
                                torch.abs(xy_result[:, 1])
                            min_idx = distances.argmin()
                            s_strength = snap_strength
                            t_strength = track_strength
                            if mapper.dual_sense_state["lt"] < 127:
                                s_strength /= 2
                                t_strength /= 2
                            if (torch.abs(xy_result[min_idx]) < snap_center).all():
                                rx_offset = xy_result[min_idx][0] * (255 / snap_size) * s_strength
                                ry_offset = xy_result[min_idx][1] * (255 / snap_size) * s_strength
                            else:
                                rx_offset = xy_result[min_idx][0] * (255 / screenshot_size) * t_strength
                                ry_offset = xy_result[min_idx][1] * (255 / screenshot_size) * t_strength
                            mapper.add_rx_ry_offset(
                                rx_offset,
                                ry_offset
                            )
                            # print("origin", xy_result[min_idx])
                            # print("offset", rx_offset, ry_offset)
                        else:
                            mapper.rx_override = None
                            mapper.ry_override = None

                        # # 预览窗口（调试用，正常使用时请注释掉）
                        # annotated_frame = result.plot()
                        # cv2.imshow(f"{model.model_name} Detection", annotated_frame)
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
                            sys.stdout.write(f"\r\033[K[Latency] cycle耗时：{cycle_latency:.3f} ms\n")
                            sys.stdout.write(f"\r\033[K[Latency] grab耗时：{grab_latency:.3f} ms\n")
                            sys.stdout.write(f"\r\033[K[Latency] infer耗时：{infer_latency:.3f} ms\n")
                            # sys.stdout.write(f"\r\033[K[Usage] CPU: {cpu_usg:.2f}% GPU: {gpu_usg:.2f}%\n")
                            sys.stdout.flush()
                            last_print_time = now
            except KeyboardInterrupt:
                pass
            except Exception as e:
                import logging
                import traceback
                logging.error("发生异常：%s", str(e))
                logging.error("异常类型：%s", type(e).__name__)
                logging.error("完整堆栈信息：\n%s", traceback.format_exc())
    except KeyboardInterrupt:
        pass
    finally:
        mapper.stop()
        cv2.destroyAllWindows()
        print("已退出")