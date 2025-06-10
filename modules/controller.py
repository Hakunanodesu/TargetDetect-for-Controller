import pywinusb.hid as hid
import vgamepad as vg
import threading
import time
import sys

from utils.tools import median_of_three


class DualSenseToX360Mapper:
    """
    DualSenseToX360Mapper 类：
    - 使用 pywinusb.hid 读取 DualSense 控制器的原始 HID 输入
    - 使用 vgamepad 创建虚拟 Xbox 360 手柄，并将 DualSense 输入映射到虚拟手柄
    - 提供 start() 和 stop() 方法，方便在外部控制映射循环的启动和停止
    """

    # DualSense 的供应商 ID 和产品 ID（USB）
    # DEFAULT_VENDOR_ID = 0x054C Sony
    # DEFAULT_PRODUCT_ID = 0x0DF2 DualSense Edge USB 接入时的 PID

    def __init__(self,
                 vendor_id: int,
                 product_id: int,
                 poll_interval: float = 0.002):
        """
        初始化 DualSenseToX360Mapper。

        :param vendor_id: DualSense 供应商 ID，默认使用 Sony（0x054C）
        :param product_id: DualSense 产品 ID，默认使用 DualSense Edge（0x0DF2）
        :param poll_interval: 映射循环的轮询间隔（秒）
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.poll_interval = poll_interval

        # 存储 DualSense 的实时状态
        self.dual_sense_state = {
            "lx": 0,       # 左摇杆 X 轴 (0-255)
            "ly": 0,       # 左摇杆 Y 轴 (0-255)
            "rx": 0,       # 右摇杆 X 轴 (0-255)
            "ry": 0,       # 右摇杆 Y 轴 (0-255)
            "lt": 0,       # 左扳机 (0-255)
            "rt": 0,       # 右扳机 (0-255)
            "shoulders_sticks_start_back": 0,  # 按钮掩码
            "buttons_hat": 0,                  # 按钮掩码
            "touchpad_ps": 0,                  # 触控板和PS键状态 (0-3)
        }

        # 支持右摇杆叠加（偏移量）
        self.rx_override = None
        self.ry_override = None

        # 虚拟 Xbox 360 手柄对象（使用 vgamepad）
        self.virtual_gamepad = vg.VX360Gamepad()

        # DualSense 设备对象（pywinusb.hid.HidDevice），方便后续关闭
        self._hid_device = None

        # 线程控制
        self._mapping_thread = None
        self._stop_event = threading.Event()

    def _input_handler(self, data: bytearray):
        """
        PyWinUSB 的回调函数。当 DualSense 有新输入时调用。

        :param data: bytearray，长度因设备而异
        """
        # 基本检查
        if len(data) < 11:  # 修改为11以包含新的数据位
            return

        # 更新摇杆和扳机状态
        self.dual_sense_state["lx"] = data[1]
        self.dual_sense_state["ly"] = data[2]
        self.dual_sense_state["rx"] = data[3]
        self.dual_sense_state["ry"] = data[4]
        self.dual_sense_state["lt"] = data[5]
        self.dual_sense_state["rt"] = data[6]

        # 更新按钮掩码，高字节在 data[9]，低字节在 data[8]
        self.dual_sense_state["shoulders_sticks_start_back"] = data[9]
        self.dual_sense_state["buttons_hat"] = data[8]
        
        # 更新触控板和PS键状态
        self.dual_sense_state["touchpad_ps"] = data[10]

    def _find_and_register_dualsense(self) -> bool:
        """
        查找并打开 DualSense 设备，注册输入回调。

        :return: 如果成功找到并注册 DualSense，返回 True；否则返回 False
        """
        all_devices = hid.HidDeviceFilter(
            vendor_id=self.vendor_id,
            product_id=self.product_id
        ).get_devices()

        if not all_devices:
            sys.stdout.write("\n>>> 未找到 DualSense 设备，请确认已通过 USB 或蓝牙连接。")
            return False

        # 只打开第一个匹配的 DualSense 设备
        self._hid_device = all_devices[0]
        self._hid_device.open()
        # 注册回调，将收到的新数据传给 _input_handler 方法
        self._hid_device.set_raw_data_handler(lambda data: self._input_handler(data))
        sys.stdout.write(f"\n>>> 已连接并注册 DualSense (VID:0x{self.vendor_id:04X}, PID:0x{self.product_id:04X})")
        return True

    def _ds_to_xinput_axis(self, val: int) -> int:
        """
        将 DualSense 的 0-255 值映射到 XInput 的 -32768 ~ +32767。

        :param val: DualSense 单轴原始值 (0-255)
        :return: 对应的 XInput 值 (int)
        """
        return int(val * 257 - 32768)

    def add_rx_ry_offset(self, dx: int = 0, dy: int = 0):
        """在原始值上添加偏移量"""
        rx = self.dual_sense_state["rx"]
        ry = self.dual_sense_state["ry"]
        self.rx_override = median_of_three(rx + dx, 255, 0)
        self.ry_override = median_of_three(ry + dy, 255, 0)

    def _map_to_x360(self):
        """
        将当前 dual_sense_state 中的信息映射到虚拟 Xbox 360 手柄。
        """
        # 1. 左摇杆
        lx = self._ds_to_xinput_axis(self.dual_sense_state["lx"])
        ly = -self._ds_to_xinput_axis(self.dual_sense_state["ly"]) - 1
        self.virtual_gamepad.left_joystick(x_value=lx, y_value=ly)

        # 2. 右摇杆
        rx = self.rx_override if self.rx_override is not None else self.dual_sense_state["rx"]
        ry = self.ry_override if self.ry_override is not None else self.dual_sense_state["ry"]
        rx = self._ds_to_xinput_axis(rx)
        ry = -self._ds_to_xinput_axis(ry) - 1
        self.virtual_gamepad.right_joystick(x_value=rx, y_value=ry)

        # 3. 扳机（vgamepad 接受 0-255）
        self.virtual_gamepad.left_trigger(self.dual_sense_state["lt"])
        self.virtual_gamepad.right_trigger(self.dual_sense_state["rt"])

        # 4. 按钮 & D-Pad
        btns = self.dual_sense_state["buttons_hat"]
        shoulders = self.dual_sense_state["shoulders_sticks_start_back"] & 0x0F

        # 肩键（L1/R1）- 独立处理，不受扳机影响
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        
        # 左肩键 (L1)
        if (shoulders & 0x01) != 0:
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        
        # 右肩键 (R1)
        if (shoulders & 0x02) != 0:
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

        # A 按钮
        if (btns & 0x20) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        # B 按钮
        if (btns & 0x40) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        # X 按钮
        if (btns & 0x10) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        # Y 按钮
        if (btns & 0x80) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

        # 镜头相关的按键：Back、Start、LeftThumb、RightThumb
        sticks = self.dual_sense_state["shoulders_sticks_start_back"] & 0xF0
        # Back
        if (sticks & 0x10) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        # Start
        if (sticks & 0x20) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
            
        # 处理触控板和PS键（额外映射）
        touchpad_ps = self.dual_sense_state["touchpad_ps"]
        
        # PS键映射到Start（额外）
        # if (touchpad_ps & 0x01) != 0:
        #     self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
            
        # 触控板映射到Back（额外）
        if (touchpad_ps & 0x02) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
            
        # Left Thumb（L3）
        if (sticks & 0x40) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        # Right Thumb（R3）
        if (sticks & 0x80) != 0:
            self.virtual_gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
        else:
            self.virtual_gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

        # D-Pad（Hat）
        # 先全部释放
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        self.virtual_gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        hat = self.dual_sense_state["buttons_hat"] & 0x0F
        if hat == 0:       # Up
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        elif hat == 1:     # Up + Right
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        elif hat == 2:     # Right
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        elif hat == 3:     # Down + Right
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        elif hat == 4:     # Down
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        elif hat == 5:     # Down + Left
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        elif hat == 6:     # Left
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        elif hat == 7:     # Up + Left
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
            self.virtual_gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

        # 最后提交一次报告，让系统感知最新状态
        self.virtual_gamepad.update()

    def start(self):
        """
        启动映射循环：
        1. 查找并注册 DualSense
        2. 创建虚拟手柄（已在 __init__ 中创建）
        3. 启动一个后台线程，不断将 DualSense 输入映射到虚拟手柄
        """
        if not self._find_and_register_dualsense():
            return False

        sys.stdout.write("\n>>> 虚拟 Xbox360 手柄已创建。DualSense 的输入将直接映射到虚拟手柄上。")

        # 重置（防止多次调用 start）
        self._stop_event.clear()

        # 后台线程负责循环映射
        def run_loop():
            try:
                while not self._stop_event.is_set():
                    self._map_to_x360()
                    time.sleep(self.poll_interval)
            except Exception as e:
                sys.stdout.write(f">>> 映射循环遇到异常：{e}")

        self._mapping_thread = threading.Thread(target=run_loop, daemon=True)
        self._mapping_thread.start()
        return True

    def stop(self):
        """
        停止映射循环，并关闭 DualSense 设备、重置虚拟手柄。
        """
        self._stop_event.set()
        if self._mapping_thread:
            self._mapping_thread.join(timeout=0)
        self._cleanup()

    def _cleanup(self):
        """
        清理工作：关闭 DualSense 设备、重置虚拟手柄并提交更新
        """
        if self._hid_device:
            try:
                self._hid_device.close()
                sys.stdout.write("\n>>> DualSense 设备已关闭。")
            except Exception:
                pass
            finally:
                self._hid_device = None

        if self.virtual_gamepad:
            try:
                self.virtual_gamepad.reset()
                self.virtual_gamepad.update()
                if hasattr(self.virtual_gamepad, 'vigem_disconnect'):
                    self.virtual_gamepad.vigem_disconnect()
                sys.stdout.write("\n>>> 虚拟手柄已重置并关闭。")
            except Exception:
                pass
            finally:
                self.virtual_gamepad = None


if __name__ == "__main__":
    # 创建 DualSense 映射器实例
    mapper = DualSenseToX360Mapper(
        vendor_id=0x054C,  # Sony
        product_id=0x0DF2  # DualSense Edge
    )
    
    try:
        # 启动映射
        if mapper.start():
            print("按 Ctrl+C 停止程序...")
            # 保持程序运行
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止程序...")
    finally:
        # 确保正确清理资源
        mapper.stop()
