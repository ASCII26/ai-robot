#!/usr/bin/env python3
import evdev
from evdev import InputDevice, ecodes,list_devices
import subprocess
import re
from screen.base import LOGGER

CARD = "default"
MIN_DB = -115.0
STEP = "1.5dB"
DEVICE_PATH = "/dev/input/event0"

# 存储所有可用的 PCM 控制器
PCM_CONTROLS = []

def find_input_devices():
    devices = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.name.startswith("Razer"):


def detect_pcm_controls():
    global PCM_CONTROLS
    PCM_CONTROLS = []
    try:
        if CARD == "default":
            out = subprocess.check_output(["amixer", "scontrols"]).decode()
        else:
            out = subprocess.check_output(["amixer", "-c", CARD, "scontrols"]).decode()
        
        # 查找所有控制器，包括名称和索引
        controls = re.findall(r"'([^']*)',(\d+)", out)
        
        # 过滤出包含 PCM 的控制器
        pcm_controls = [f"{name},{index}" for name, index in controls if "PCM" in name]
        print(pcm_controls)

        for control in pcm_controls:
            # 检查每个 PCM 控制器是否有 Playback 限制
            if CARD == "default":
                info = subprocess.check_output(["amixer", "sget", control]).decode()
            else:
                info = subprocess.check_output(["amixer", "-c", CARD, "sget", control]).decode()
            
            if "Limits: Playback" in info:
                PCM_CONTROLS.append(control)
                LOGGER.info(f"发现 PCM 控制器: {control}")
    
    except Exception as e:
        LOGGER.error("检测 PCM 控制器失败:", e)

def db_to_volume(db):
    # 将 dB 值 (-100 到 0) 转换为 0-100 的音量百分比
    return int((db + 115) * 100 / 100)

def get_current_db(control):
    try:
        if CARD == "default":
            out = subprocess.check_output(["amixer", "get", control]).decode()
        else:
            out = subprocess.check_output(["amixer", "-c", CARD, "get", control]).decode()

        match = re.search(r'\[(\-?\d+\.\d+)dB\]', out)
        if match:
            db = float(match.group(1))
            volume = db_to_volume(db)
            LOGGER.info(f"[{control}] volume: {volume}% ({db}dB)")
            return db
    except Exception as e:
        LOGGER.error("Failed to get dB:", e)
    return None

def adjust_volume(direction):
    # 为所有检测到的 PCM 控制器设置音量
    for control in PCM_CONTROLS:
        current_db = get_current_db(control)
        if current_db is None:
            return
        if direction == "down" and current_db <= MIN_DB:
            LOGGER.info(f"🔇 Already at minimum {MIN_DB}dB")
            return
        delta = STEP + "+" if direction == "up" else STEP + "-"

        try:
            if CARD == "default":
                subprocess.run(["amixer", "set", control, delta], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.run(["amixer", "-c", CARD, "set", control, delta], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            LOGGER.error(f"set {control} volume failed:", e)

def listen(device_path):
    # 首先检测所有可用的 PCM 控制器
    detect_pcm_controls()
    
    dev = InputDevice(device_path)
    LOGGER.info(f"🎧 Listening on \033[1m\033[37m{dev.path}\033[0m - \033[1m\033[37m{dev.name}\033[0m")

    # if dev.name != DEVICE_NAME:
    #     LOGGER.error(f"🚫 Device name mismatch: {dev.name} != {DEVICE_NAME}")
    #     return
    
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:
            if event.code == ecodes.KEY_VOLUMEUP:
                adjust_volume("up")
            elif event.code == ecodes.KEY_VOLUMEDOWN:
                adjust_volume("down")

if __name__ == "__main__":
    listen(DEVICE_PATH)  # 替换为你的旋钮设备路径