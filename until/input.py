import threading
from evdev import InputDevice, ecodes, list_devices
import select
import time
import pyinotify

from until.log import LOGGER

ecodes = ecodes

class KeyListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True  # set as daemon thread, exit when main program exits
        self.running = True
        self.devices = []
        self.callbacks = [] 
        self.wm = pyinotify.WatchManager()  # 创建 WatchManager
        self.notifier = None  # 初始化 notifier
        
    def on(self, callback):
        """add callback function"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            LOGGER.debug(f"add keyboardCallback: {callback.__name__}")

    def off(self, callback):
        """remove callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            LOGGER.debug(f"remove keyboardCallback: {callback.__name__}")

    def scan(self):
        """scan all available input devices"""
        devices = []
        for device_path in list_devices():
            try:
                dev = InputDevice(device_path)
                devices.append(dev)
                LOGGER.debug(f"scan device: {dev.name}")
            except Exception as e:
                LOGGER.error(f"cannot open device {device_path}: {e}")
        return devices

    def run(self):
        """线程主函数"""
        # 设置 inotify 监听
        mask = pyinotify.IN_CREATE | pyinotify.IN_DELETE  # 监听创建和删除事件
        self.wm.add_watch('/dev/input', mask, rec=True)
        self.notifier = pyinotify.ThreadedNotifier(self.wm, self.handle_device_change)
        self.notifier.start()
        
        # 扫描设备
        self.devices = self.scan()
        if not self.devices:
            LOGGER.error("no input device found")
            return

        while self.running:
            try:
                r, w, x = select.select(self.devices, [], [], 0.1)
                for device in r:
                    for event in device.read():
                        if event.type == ecodes.EV_KEY:
                            key_name = ecodes.KEY[event.code]
                            LOGGER.debug(f"{device.name} - key down {key_name}")
                            
                            # call all registered callbacks
                            for callback in self.callbacks:
                                try:
                                    callback(device.name, event)
                                except Exception as e:
                                    LOGGER.error(f"execute callback {callback.__name__} error: {e}")
                            
                            LOGGER.debug(f"Event: type={event.type}, code={event.code}, value={event.value}")
            except Exception as e:
                LOGGER.info("read device error, rescanning...")
                LOGGER.error(f"read device error: {e}")
                time.sleep(1)  # 出错后等待1秒再重试
                self.devices = self.scan()
                
    def handle_device_change(self, event):
        """detect device change"""
        LOGGER.debug(f"device change: {event.pathname}")
        self.devices = self.scan()  # 重新扫描设备

    def stop(self):
        """stop listening"""
        self.running = False
        if self.notifier:
            self.notifier.stop()