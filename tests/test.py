import dxcam

# 创建一个 DXCamera 实例
camera = dxcam.create()

# 进行屏幕截图
frame = camera.grab()

# 显示截图
from PIL import Image
Image.fromarray(frame).show()