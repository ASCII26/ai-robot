#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
OLED显示管理器 - 用于小智AI脚本的输出显示
"""
import sys
import os
import threading
import time
from PIL import Image, ImageDraw
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drive.SSD1305 import SSD1305
from ui.textarea import TextArea
from ui.fonts import Fonts

class OLEDDisplay:
    def __init__(self, width=128, height=32):
        """初始化OLED显示器"""
        self.width = width
        self.height = height
        
        # 初始化硬件
        self.disp = SSD1305()
        self.disp.Init()
        self.disp.clear()
        
        # 初始化文本显示区域
        self.text_area = TextArea(width=width-20, height=height-8)
        self.fonts = Fonts()
        
        # 状态栏区域 (顶部8像素)
        self.status_text = "小智AI"
        self.is_listening = False
        self.is_speaking = False
        
        # 显示更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self._display_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # 显示欢迎信息
        self.show_welcome()
        
    def show_welcome(self):
        """显示欢迎信息"""
        self.println("=== 小智 AI ===")
        self.println("正在初始化...")
        
    def println(self, text, timestamp=True):
        """输出一行文本到OLED（类似print功能）"""
        if timestamp:
            time_str = datetime.now().strftime("%H:%M")
            display_text = f"[{time_str}] {text}"
        else:
            display_text = text
            
        self.text_area.append_text(display_text)
        
        # 同时输出到控制台（用于调试）
        print(f"OLED: {display_text}")
        
    def set_status(self, status_text, listening=False, speaking=False):
        """设置状态栏显示"""
        self.status_text = status_text
        self.is_listening = listening
        self.is_speaking = speaking
        
    def clear_display(self):
        """清空显示内容"""
        self.text_area.clear()
        
    def _draw_status_bar(self, image):
        """绘制状态栏"""
        draw = ImageDraw.Draw(image)
        
        # 绘制状态栏背景
        draw.rectangle((0, 0, self.width-1, 7), outline=255, fill=0)
        
        # 绘制状态文本
        draw.text((2, 0), self.status_text, font=self.fonts.size_5, fill=255)
        
        # 绘制状态指示器
        if self.is_listening:
            # 录音指示器 (红点闪烁效果)
            if int(time.time() * 2) % 2:  # 每0.5秒闪烁
                draw.ellipse((self.width-10, 1, self.width-4, 7), outline=255, fill=255)
            draw.text((self.width-20, 0), "●", font=self.fonts.size_5, fill=255)
            
        elif self.is_speaking:
            # 播放指示器 (音符符号)
            draw.text((self.width-12, 0), "♪", font=self.fonts.size_5, fill=255)
            
        # 绘制分隔线
        draw.line((0, 7, self.width-1, 7), fill=255)
        
    def _display_loop(self):
        """显示更新循环"""
        while self.running:
            try:
                # 创建主画面
                main_image = Image.new('1', (self.width, self.height), 0)
                
                # 绘制状态栏
                self._draw_status_bar(main_image)
                
                # 渲染文本区域
                text_image = self.text_area.render()
                # 将文本区域贴到主画面（状态栏下方）
                main_image.paste(text_image, (0, 8))
                
                # 更新到硬件显示
                self.disp.getbuffer(main_image)
                self.disp.ShowImage()
                
                time.sleep(1/30)  # 30 FPS更新率
                
            except Exception as e:
                print(f"OLED显示错误: {e}")
                time.sleep(0.1)
                
    def cleanup(self):
        """清理资源"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
        self.disp.clear()
        self.disp.reset()

# 全局OLED显示实例
_oled_instance = None

def init_oled():
    """初始化OLED显示器"""
    global _oled_instance
    if _oled_instance is None:
        _oled_instance = OLEDDisplay()
    return _oled_instance

def get_oled():
    """获取OLED显示器实例"""
    global _oled_instance
    if _oled_instance is None:
        init_oled()
    return _oled_instance

def oled_print(text, timestamp=True):
    """OLED打印函数"""
    oled = get_oled()
    oled.println(text, timestamp)

def oled_status(status, listening=False, speaking=False):
    """设置OLED状态"""
    oled = get_oled()
    oled.set_status(status, listening, speaking)

def cleanup_oled():
    """清理OLED资源"""
    global _oled_instance
    if _oled_instance:
        _oled_instance.cleanup()
        _oled_instance = None

# 测试函数
if __name__ == "__main__":
    try:
        oled = init_oled()
        
        oled.println("OLED测试开始")
        time.sleep(2)
        
        oled.set_status("测试模式", listening=True)
        oled.println("录音状态测试")
        time.sleep(3)
        
        oled.set_status("测试模式", speaking=True)
        oled.println("播放状态测试")
        time.sleep(3)
        
        oled.set_status("正常运行")
        oled.println("OLED测试完成")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("测试中断")
    finally:
        cleanup_oled()