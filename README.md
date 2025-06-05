# TargetDetect-for-Controller

## 项目概述

一个基于深度学习的实时目标检测系统，集成了 YOLO 目标检测模型和 DualSense 手柄控制映射功能。该项目能够通过屏幕截图进行目标检测和追踪，并将 DualSense 手柄输入映射到虚拟 Xbox 360 手柄，实现游戏辅助和自动化控制。

## 主要特性

- 🎯 **实时目标检测**：基于 YOLO 模型的高效目标识别
- 🎮 **手柄映射**：DualSense 到 Xbox 360 手柄的完整映射
- 📸 **屏幕捕获**：实时屏幕截图和目标追踪
- ⚡ **GPU 加速**：支持 CUDA 加速推理
- 🔧 **易于配置**：初始化和配置工具
- 🎯 **目标追踪**：智能目标跟踪算法

## 系统要求

### 硬件要求
- Windows 操作系统
- DualSense 手柄
- NVIDIA GPU（推荐，用于 CUDA 加速）

### 软件要求
- Python 3.11
- CUDA Toolkit（如使用 GPU 加速）

## 安装和配置

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-repo/TargetDetect-for-Controller.git
cd TargetDetect-for-Controller

# 安装依赖
pip install -r requirements.txt
```

### 2. CUDA 配置（可选）

如需使用 GPU 加速，请：
1. 访问 [NVIDIA CUDA 下载页面](https://developer.nvidia.com/cuda-downloads)
2. 下载并安装对应版本的 CUDA Toolkit
3. 确保 PyTorch 版本与 CUDA 版本兼容

### 3. 手柄连接

确保 DualSense 手柄已正确连接到计算机并识别。

## 使用方法

### 快速开始

1. **初始化配置（可选，第一次运行 `run.py` 时会自动运行）**
   ```bash
   python init.py
   ```
   运行配置向导，设置检测参数、手柄映射等选项。

2. **启动检测和控制**
   ```bash
   python run.py
   ```
   启动实时目标检测和手柄控制映射。

### 模型训练

如需训练自定义模型：

1. 准备数据集（如 `datasets/apex.yaml`）
2. 运行训练脚本：
   ```bash
   python train.py
   ```

## 配置文件

### 全局配置 (`configs/cfg_global.json`)
- 推理设置（设备、批次大小等）
- 屏幕截图配置
- 目标追踪参数
- 随机种子设置

### YOLO 配置 (`configs/cfg_yolo.json`)
- 模型路径和参数
- 检测阈值
- NMS 设置

## 项目结构

```
TargetDetect-for-Controller/
├── configs/                  # 配置文件
├── models/                   # 模型定义
├── modules/                  # 核心功能模块
├── utils/                    # 工具函数
├── datasets/                 # 训练数据集
├── init.py                   # 配置初始化
├── run.py                    # 主程序
├── train.py                  # 训练脚本
└── requirements.txt          # 依赖列表
```

## 开发计划

- [ ] 集成 HidHide 功能
- [ ] 添加 OpenVINO 推理支持
- [x] 重构初始化模块，提升用户体验
- [x] 支持 AMD GPU 加速
- [ ] 支持更多手柄类型

## 致谢

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - 强大的目标检测框架
- [ViGEmBus](https://github.com/nefarius/ViGEmBus) - 虚拟游戏手柄驱动
- [vgamepad](https://github.com/yannbouteiller/vgamepad) - 虚拟游戏手柄库

## 许可证

无

## 注意事项

⚠️ **重要提示**：
- 当前版本仅支持 Windows 系统和 DualSense 手柄
- 使用前请确保手柄正确连接且 `ViGEmBus` 驱动正常
- 检测到 `run.py` 首次运行会自动运行 `init.py` 进行配置，若后续需要修改配置，请手动运行 `init.py`
- 请勿用于游戏辅助用途，进攻学习交流使用

## 技术支持

如遇问题，请：
1. 检查系统要求和依赖安装
2. 查看项目 Issues 页面
3. 提交详细的问题报告

---

**项目状态**：积极开发中 | **最后更新**：2025年6月5日