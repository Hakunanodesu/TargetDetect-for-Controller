# TargetDetect-for-Controller

## 项目概述

一个基于深度学习的实时目标检测系统，集成了 YOLO 目标检测模型和 DualSense 手柄控制映射功能。该项目能够通过屏幕截图进行目标检测和追踪，并将 DualSense 手柄输入映射到虚拟 Xbox 360 手柄，实现自动化控制。

## 开发计划

- [x] 重构初始化模块，提升用户体验
- [x] 支持 AMD GPU 加速 (理论上所有支持 DX12 的 GPU 都支持)
- [x] 图形化界面
- [ ] 集成 HidHide 功能
- [ ] 支持更多手柄类型

## 主要特性

- 🎯 **实时目标检测**：基于 YOLO 模型的高效目标识别
- 🎮 **手柄映射**：DualSense 手柄的映射（除了触控板和 PS 键）
- 📸 **屏幕捕获**：实时屏幕截图和目标追踪
- ⚡ **GPU 加速**：只要您的 GPU 支持 DX12 就可以
- 🔧 **易于配置**：初始化和配置工具
- 🎯 **目标追踪**：智能目标跟踪算法

## 系统要求

### 硬件要求
- Windows 操作系统
- DualSense 手柄

## 安装和配置

### 1. 环境准备

在 release 界面下载并解压项目文件

### 2. 手柄连接

确保 DualSense 手柄已正确连接到计算机并识别。

## 使用方法

**启动检测和控制**

双击 run.exe 文件即可启动程序，第一次运行会引导您进行初始化配置。

### 重新初始化配置

将 configs 文件夹内的 cfg_global.json 删除，重新运行 run.exe 即可重新初始化配置。

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

- [ViGEmBus](https://github.com/nefarius/ViGEmBus) - 虚拟游戏手柄驱动
- [vgamepad](https://github.com/yannbouteiller/vgamepad) - 虚拟游戏手柄库

## ⚠️ **重要提示**：

- 请勿用于游戏辅助用途，仅供学习交流使用

## 技术支持

如遇问题，请：
1. 检查系统要求和依赖安装
2. 查看项目 Issues 页面
3. 提交详细的问题报告

---

**项目状态**：积极开发中 | **最后更新**：2025年6月7日