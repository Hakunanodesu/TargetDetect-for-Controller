# 项目说明文档

## 简介

本项目是一个基于深度学习的目标检测系统，使用了 YOLO11 模型进行实时目标检测，并通过 DualSense 手柄进行交互控制。项目包含模型训练、推理以及手柄控制映射等功能。

## 文件结构

```
controller/
├── config.json               # 配置文件
├── datasets/                 # 数据集目录
│   └── apex.yaml             # 数据集配置文件
├── models/                   # 模型目录
│   └── yolo.py               # YOLO11 模型定义
├── modules/                  # 模块目录
│   └── controller.py         # DualSense 手柄控制映射模块
├── README.md                 # 项目说明文档
├── requirements.txt          # 项目依赖列表
├── run.py                    # 主运行脚本
├── runs/                     # 训练运行目录
│   └── detect/
│       └── epoch100/
│           ├── args.yaml     # 训练参数配置
│           └── weights/      # 模型权重文件
├── tests/                    # 测试目录
│   └── test.py               # 测试脚本
├── train.py                  # 训练脚本
└── utils/                    # 工具目录
    └── tools.py              # 工具函数
```

## 使用方法

### 环境配置

1. 安装 Python 及其依赖库：
   ```
   pip install -r requirements.txt
   ```

2. 确保 CUDA 环境可用（如果使用 GPU 加速）。

### 模型训练

1. 准备数据集并配置，例：`datasets/apex.yaml`。
2. 运行 `train.py` 进行模型训练：
   ```
   python train.py
   ```

### 模型推理

1. 确保模型权重路径正确。
2. 运行 `run.py` 进行实时目标检测：
   ```
   python run.py
   ```

### 手柄控制映射

1. 连接 DualSense 手柄。
2. 运行 `run.py` 启动手柄控制映射。

## 功能描述

- `YOLO11`：一个目标检测模型类，提供模型初始化、推理和训练方法。
- `DualSenseToX360Mapper`：一个类，用于将 DualSense 手柄的输入映射到虚拟 Xbox 360 手柄。
- `config.json`：包含推理设置、设备配置、随机种子、屏幕截图大小和跟踪设置等。
- `train.py`：用于训练 YOLO11 模型的脚本。
- `run.py`：主运行脚本，负责启动手柄控制映射和实时目标检测。
- `tools.py`：包含一些工具函数，如模型转换等。

## 注意事项

- 目前的版本仅支持 DualSense 手柄，请运行 `get_controller.py` 并根据提示确认手柄的 Vendor ID (VID) 和 Product ID (PID)。
- 请确保在使用前已正确连接 DualSense 手柄。
- 在使用 GPU 加速时，请确保 CUDA 环境配置正确。
- 本项目中的所有脚本和模块均需在 Python 环境下运行。
- 请根据实际修改 `run.py` 中的手柄信息和模型权重路径等。
