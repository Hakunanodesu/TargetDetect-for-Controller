# 项目说明文档

## 简介

本项目是一个基于深度学习的目标检测系统，使用了 YOLO11 模型进行实时目标检测，并通过 DualSense 手柄进行交互控制。项目包含模型训练、目标追踪等功能。当前仅支持Windows操作系统。

## To-Do 列表

以下是项目当前需要完成的任务：

- [ ] 添加HidHide功能
- [ ] 重写get_controller.py，使其能初始化更多参数，更加的用户友好

## 文件结构

```
TargetDetect-for-Controller/
├── cfg_global.json     # 全局配置文件
├── datasets/           # 数据集目录
│   └── apex.yaml       # 数据集配置文件
├── get_controller.py   # 获取手柄信息的脚本
├── models/             # 模型目录
│   ├── cfg_yolo.json   # YOLO模型配置文件
│   └── yolo.py         # YOLO模型定义
├── modules/            # 模块目录
│   ├── controller.py   # 手柄控制映射模块
│   └── grab_screen.py  # 屏幕截图模块
├── README.md           # 项目说明文档
├── requirements.txt    # 项目依赖列表
├── run.py              # 主运行脚本
├── train.py            # 训练脚本
├── utils/              # 工具目录
└── tools.py            # 工具函数
```

# 项目说明文档

## 文件结构

```
TargetDetect-for-Controller/
├── cfg_global.json           # 全局配置文件
├── datasets/                 # 数据集目录
│   └── apex.yaml             # 数据集配置文件
├── get_controller.py         # 获取手柄信息的脚本
├── models/                   # 模型目录
│   ├── cfg_yolo.json         # YOLO模型配置文件
│   └── yolo.py               # YOLO模型定义
├── modules/                  # 模块目录
│   ├── controller.py         # 手柄控制映射模块
│   └── grab_screen.py        # 屏幕截图模块
├── README.md                 # 项目说明文档
├── requirements.txt          # 项目依赖列表
├── run.py                    # 主运行脚本
├── train.py                  # 训练脚本
└── utils/                    # 工具目录
    └── tools.py              # 工具函数
```

## 使用方法

### 环境配置

1. 确保 CUDA 环境可用（如果使用 NVIDIA GPU 加速），请在 `https://developer.nvidia.com/cuda-downloads` 下载您的 GPU 所对应的 CUDA 版本。

2. 安装 Python（3.11）及其依赖库（请确保安装的 PyTorch 版本跟您的 CUDA 版本能对应）：
   ```
   pip install -r requirements.txt
   ```

### 模型训练

1. 准备数据集并配置，例：`datasets/apex.yaml`。
2. 运行 `train.py` 进行模型训练：
   ```
   python train.py
   ```

### 屏幕目标检测 + 手柄控制映射 + 追踪

1. 连接 DualSense 手柄。
2. 运行 `get_controller.py` 获取手柄的 Vendor ID (VID) 和 Product ID (PID)。
3. 在 `cfg_global.json` 中配置手柄信息。
4. 在 `cfg_global.json` 中配置模型权重路径。
5. 在 `cfg_global.json` 中配置运行设备，如 `"cpu"` 或 `"cuda:0"` ，`null` 为自动检测。
6. 运行 `run.py` 启动手柄控制映射。

## 功能描述

- `YOLO11`：一个目标检测模型类，提供模型初始化、推理和训练方法。
- `DualSenseToX360Mapper`：一个类，用于将 DualSense 手柄的输入映射到虚拟 Xbox 360 手柄。
- `cfg_global.json`：包含推理设置、设备配置、随机种子、屏幕截图大小和跟踪设置等。
- `train.py`：用于训练 YOLO 模型的脚本。
- `run.py`：主运行脚本，负责启动手柄控制映射和实时目标检测。
- `tools.py`：包含一些工具函数，如模型转换等。

## 注意事项

- 目前的版本仅支持 DualSense 手柄
- 请确保在使用前已正确连接 DualSense 手柄。
- 在使用 GPU 加速时，请确保 CUDA 环境配置正确。
- 本项目中的所有脚本和模块均需在 Python 环境下运行。
