import dxcam
import time


class ScreenGrabber:

    def __init__(self, region=None):
        self.camera = dxcam.create()
        self.region = region

    def grab_frame(self):
        # time.sleep(0.001)
        frame = self.camera.grab(region=self.region)
        return frame

    def stop(self):
        self.camera.stop()

