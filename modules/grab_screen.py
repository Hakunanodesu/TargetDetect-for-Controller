import dxcam


class ScreenGrabber:

    def __init__(self, region=None):
        self.camera = dxcam.create()
        self.region = region

    def grab_frame(self):
        frame = self.camera.grab(region=self.region)
        return frame

    def stop(self):
        self.camera.stop()

