# TargetDetect-for-Controller

## 项目概述

一个基于深度学习的实时目标检测系统，集成了 YOLO 目标检测模型和 DualSense 手柄控制映射功能。该项目能够通过屏幕截图进行目标检测和追踪，并将 DualSense 手柄输入映射到虚拟 Xbox 360 手柄，实现自动化控制。

## 开发计划

- [ ] 集成 HidHide 功能
- [x] 重构初始化模块，提升用户体验
- [ ] ~~支持 OpenVINO 加速~~
- [x] 支持 AMD GPU 加速 (理论上所有支持 DX12 的 GPU 都支持)
- [ ] 支持更多手柄类型

## 主要特性

- 🎯 **实时目标检测**：基于 YOLO 模型的高效目标识别
- 🎮 **手柄映射**：DualSense 手柄的映射（除了触控板和 PS 键）
- 📸 **屏幕捕获**：实时屏幕截图和目标追踪
- ⚡ **GPU 加速**：~~支持 CUDA 加速推理~~只要您的 GPU 支持 DX12 就可以
- 🔧 **易于配置**：初始化和配置工具
- 🎯 **目标追踪**：智能目标跟踪算法

## 系统要求

### 硬件要求
- Windows 操作系统
- DualSense 手柄
- ~~NVIDIA GPU（推荐，用于 CUDA 加速）~~支持 DX12 的 dGPU 或 iGPU

### 软件要求
- Python 3.11
- ~~CUDA Toolkit（如使用 GPU 加速）~~

## 安装和配置

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/Hakunanodesu/TargetDetect-for-Controller.git
cd TargetDetect-for-Controller

# 安装依赖
pip install -r requirements.txt
```

### 2. 手柄连接

确保 DualSense 手柄已正确连接到计算机并识别。

## 使用方法

### 快速开始

**启动检测和控制**
   ```bash
   python run.py
   ```
   启动实时目标检测和手柄控制映射。（初次使用时会自动运行初始化配置脚本）

### 重新初始化配置

**手动运行初始化脚本**
   ```bash
   python init.py
   ```

## 配置文件

### 全局配置 (`configs/cfg_global.json`)
- 推理设置（设备、批次大小等）
- 屏幕截图配置
- 目标追踪参数
- 随机种子设置

### 模型配置 (`configs/cfg_model.json`)
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

## 致谢

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - 强大的目标检测框架
- [ViGEmBus](https://github.com/nefarius/ViGEmBus) - 虚拟游戏手柄驱动
- [vgamepad](https://github.com/yannbouteiller/vgamepad) - 虚拟游戏手柄库

## 注意事项

⚠️ **重要提示**：
- 当前版本仅支持 Windows 系统和 DualSense 手柄
- 使用前请确保手柄正确连接且 `ViGEmBus` 驱动正常
- 检测到 `run.py` 首次运行会自动运行 `init.py` 进行配置，若后续需要修改配置，请手动运行 `init.py`
- 请勿用于游戏辅助用途，仅供学习交流使用

## 技术支持

如遇问题，请：
1. 检查系统要求和依赖安装
2. 查看项目 Issues 页面
3. 提交详细的问题报告

---

**项目状态**：积极开发中 | **最后更新**：2025年6月5日