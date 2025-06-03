import dxcam
import time
import threading
import queue


class ScreenGrabber:

    def __init__(self, region=None, fps=120):
        self.camera = dxcam.create(region=region, output_idx=0, output_color="RGB")
        self.camera.start(target_fps=fps)

        self.inverval = 1 / fps
        self.stop_event = threading.Event()
        self.thread = None

    def grab_frame(self, frame_queue):
        while not self.stop_event.is_set():
            time.sleep(self.inverval)
            frame = self.camera.get_latest_frame()  # 立即返回最近一帧 numpy.ndarray
            if not frame_queue.full():
                frame_queue.put(frame)

    def start_grab_frame_thread(self):
        frame_queue = queue.Queue(maxsize=1)
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self.grab_frame, 
            args=(frame_queue,),
            daemon=True
        )
        self.thread.start()
        return frame_queue

    def stop(self):
        # 通知 grab_frame 里的循环退出
        self.stop_event.set()
        # 等待线程结束（如果线程还没启动过，就不阻塞）
        if self.thread is not None:
            self.thread.join()
            self.thread = None

        self.camera.stop()

