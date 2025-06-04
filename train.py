from models.yolo import YOLO11
import torch

from utils.tools import cvtmodel


if __name__ == '__main__':
    # 检查GPU是否可用
    print(f"正在检查是否支持CUDA...{torch.cuda.is_available()}")

    saved_name = "epoch1000_"
    model = YOLO11("yolo11s.pt")
    model.train(data="./datasets/apex.yaml", name=saved_name)
