# Muspi 项目新手指引

## 项目简介

Muspi 是一个基于 Python 的智能音乐娱乐系统，主要运行在树莓派等嵌入式设备上。它通过 OLED 显示屏(SSD1305)提供可视化界面，支持多种音频播放方式和AI语音助手功能。

## 核心功能

- **智能语音助手** (小智) - 支持语音交互和TTS
- **时钟显示** - 数字时钟界面
- **小游戏** - 包含恐龙跑跑和生命游戏等

## 硬件要求

- 树莓派 (推荐4B或更高版本)
- SSD1305 OLED显示屏 (128x32分辨率)
- 音频输出设备 (扬声器或耳机)
- 物理按键 (音量调节、切换等)
- 可选：麦克风

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <项目地址>
cd ai-robot

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 硬件连接

确保 SSD1305 OLED 显示屏正确连接到树莓派的 SPI 或 I2C 接口，按键连接到相应的 GPIO 引脚。

### 3. 配置插件

编辑 `config/plugins.json` 启用/禁用所需插件：

```json
{
    "plugins": [
        {
            "name": "xiaozhi",     // 小智语音助手
            "enabled": true,
            "auto_hide": false
        },
        {
            "name": "clock",       // 时钟显示
            "enabled": true,
            "auto_hide": false
        },
        {
            "name": "dino",        // 恐龙游戏
            "enabled": true,
            "auto_hide": false
        },
        {
            "name": "life",        // 生命游戏
            "enabled": false,
            "auto_hide": false
        }
        // ... 其他插件
    ]
}
```

### 4. 运行系统

```bash
# 直接运行
python main.py

# 或作为系统服务运行
sudo systemctl enable muspi.service
sudo systemctl start muspi.service
```

## 项目结构

```
ai-robot/
├── main.py              # 主入口文件
├── requirements.txt     # 项目依赖
├── muspi.service       # 系统服务配置
├── config/             # 配置文件目录
│   └── plugins.json    # 插件配置
├── screen/             # 显示系统
│   ├── manager.py      # 显示管理器
│   ├── plugin.py       # 插件管理器
│   ├── base.py         # 插件基类
│   └── plugins/        # 具体插件实现
├── drive/              # 硬件驱动
├── ui/                 # UI组件
├── until/              # 工具库
└── assets/             # 资源文件
```

## 主要组件说明

### DisplayManager (screen/manager.py:53)
- 管理OLED显示屏渲染
- 处理按键输入事件
- 控制插件切换和动画效果
- 管理屏幕休眠/唤醒

### PluginManager (screen/plugin.py:20)
- 动态加载和管理插件
- 根据配置文件启用/禁用插件
- 处理插件的生命周期

### 插件系统
每个插件继承自 `DisplayPlugin` 基类，实现：
- `update()` - 更新插件状态
- `get_image()` - 返回要显示的图像
- `event_listener()` - 处理事件

## 按键控制

- **前进键长按 (3秒)** - 关闭/唤醒屏幕
- **前进键短按** - 切换下一个插件
- **音量+/-** - 调节音量

## 开发建议

1. **添加新插件**：在 `screen/plugins/` 目录创建新文件，继承 `DisplayPlugin`
2. **修改UI组件**：查看 `ui/` 目录下的现有组件
3. **硬件适配**：修改 `drive/config.py` 适配不同硬件
4. **日志调试**：使用 `until/log.py` 中的 LOGGER 进行日志输出

## 常见问题

1. **显示屏无显示**：检查 SPI/I2C 连接和驱动配置
2. **音频无输出**：确认 ALSA 音频设备配置正确
3. **插件加载失败**：检查 `config/plugins.json` 配置和依赖安装

## 技术栈

- **Python 3.7+** - 主要开发语言
- **Pillow** - 图像处理
- **MQTT/OpusLib** - 音频流处理
- **GPIO/SPI/I2C** - 硬件接口