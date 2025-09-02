#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
OLED显示管理器 - 参考game.py的简洁实现
"""
import sys
import os
import threading
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 添加驱动路径 - 参考game.py的方法
current_dir = os.path.dirname(os.path.realpath(__file__))
libdir = os.path.join(current_dir, "..", "drive")  # drive在上级目录

if os.path.exists(libdir):
    sys.path.append(libdir)
    
from drive import SSD1305

# 简化的文本显示类
class SimpleTextArea:
    def __init__(self, width=108, height=24):
        self.width = width
        self.height = height
        self.lines = []
        self.max_lines = 3  # 最多显示3行
        
        # 尝试加载字体 - 参考game.py的字体路径
        try:
            # 尝试使用相对路径加载字体
            font_path = os.path.join(current_dir, "..", "assets", "fonts", "fusion-pixel-10px.ttf")
            if os.path.exists(font_path):
                self.font = ImageFont.truetype(font_path, 10)
            else:
                # 备用8px字体
                font_path_8 = os.path.join(current_dir, "..", "assets", "fonts", "fusion-pixel-8px.ttf")
                if os.path.exists(font_path_8):
                    self.font = ImageFont.truetype(font_path_8, 8)
                else:
                    self.font = ImageFont.load_default()
        except Exception:
            self.font = ImageFont.load_default()
    
    def append_text(self, text):
        """添加新文本"""
        max_chars = self.width // 8
        if len(text) > max_chars:
            text = text[:max_chars-3] + "..."
        
        self.lines.append(text)
        
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
    
    def render(self):
        """渲染文本区域"""
        image = Image.new('1', (self.width, self.height), 0)
        draw = ImageDraw.Draw(image)
        
        y = 0
        line_height = 8
        for line in self.lines:
            if y + line_height <= self.height:
                draw.text((2, y), line, font=self.font, fill=255)
                y += line_height
        
        return image
    
    def clear(self):
        """清空文本"""
        self.lines = []

class OLEDDisplay:
    def __init__(self, width=128, height=32):
        """初始化OLED显示器 - 参考game.py的简洁方式"""
        self.width = width
        self.height = height
        
        # 全局实例管理
        if hasattr(OLEDDisplay, '_instance'):
            raise RuntimeError("OLED显示器已经初始化，请使用get_oled()获取实例")
        OLEDDisplay._instance = self
        
        # 初始化显示屏 - 完全参考game.py
        try:
            self.disp = SSD1305.SSD1305()
            self.disp.Init()
            self.disp.set_screen_rotation(1)  # 180度旋转
            self.disp.clear()
            print("OLED硬件初始化成功，已设置180度旋转")
        except Exception as e:
            print(f"OLED硬件初始化失败: {e}")
            self.disp = None
        
        # 初始化文本显示区域
        self.text_area = SimpleTextArea(width=width-20, height=height-10)
        
        # 加载状态栏字体
        try:
            font_path = os.path.join(current_dir, "..", "assets", "fonts", "fusion-pixel-8px.ttf")
            if os.path.exists(font_path):
                self.status_font = ImageFont.truetype(font_path, 8)
            else:
                self.status_font = ImageFont.load_default()
        except Exception:
            self.status_font = ImageFont.load_default()
        
        # 状态信息
        self.status_text = "小智AI"
        self.is_listening = False
        self.is_speaking = False
        
        # 主图像 - 参考game.py的方式
        self.image = Image.new('1', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # 显示更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self._display_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.show_welcome()
        
    def show_welcome(self):
        """显示欢迎信息"""
        self.println("=== 小智 AI ===", False)
        self.println("正在初始化...", False)
        
    def println(self, text, timestamp=True):
        """输出一行文本到OLED"""
        if timestamp:
            time_str = datetime.now().strftime("%H:%M")
            display_text = f"[{time_str}] {text}"
        else:
            display_text = text
            
        self.text_area.append_text(display_text)
        print(f"OLED: {display_text}")
        
    def set_status(self, status_text, listening=False, speaking=False):
        """设置状态栏显示"""
        self.status_text = status_text
        self.is_listening = listening
        self.is_speaking = speaking
        
    def clear_display(self):
        """清空显示内容"""
        self.text_area.clear()
        
    def _draw_screen(self):
        """绘制完整屏幕 - 参考game.py的绘制方式"""
        # 清空画布
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
        
        # 绘制状态栏
        self.draw.rectangle((0, 0, self.width-1, 9), outline=255, fill=0)
        self.draw.text((2, 1), self.status_text, font=self.status_font, fill=255)
        
        # 绘制状态指示器
        if self.is_listening:
            if int(time.time() * 2) % 2:  # 闪烁效果
                self.draw.ellipse((self.width-12, 2, self.width-6, 8), outline=255, fill=255)
            self.draw.text((self.width-20, 1), "REC", font=self.status_font, fill=255)
        elif self.is_speaking:
            self.draw.text((self.width-25, 1), "PLAY", font=self.status_font, fill=255)
            
        # 绘制分隔线
        self.draw.line((0, 9, self.width-1, 9), fill=255)
        
        # 渲染并绘制文本区域
        text_image = self.text_area.render()
        # 将文本粘贴到主图像上（状态栏下方）
        self.image.paste(text_image, (0, 10))
        
    def _display_loop(self):
        """显示更新循环 - 参考game.py的帧率控制"""
        frame_time = 1.0 / 10.0  # 10fps，降低CPU使用
        
        while self.running:
            try:
                frame_start = time.time()
                
                # 绘制屏幕
                self._draw_screen()
                
                # 更新到硬件显示
                if self.disp:
                    try:
                        self.disp.getbuffer(self.image)
                        self.disp.ShowImage()
                    except Exception as e:
                        print(f"OLED显示更新错误: {e}")
                
                # 帧率控制
                elapsed = time.time() - frame_start
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                    
            except Exception as e:
                print(f"OLED显示循环错误: {e}")
                time.sleep(0.5)
                
    def cleanup(self):
        """清理资源 - 参考game.py的清理方式"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
        if self.disp:
            try:
                self.disp.clear()
                self.disp.reset()
            except Exception:
                pass
        # 清理全局实例
        if hasattr(OLEDDisplay, '_instance'):
            delattr(OLEDDisplay, '_instance')

# 全局OLED显示实例
_oled_instance = None

def init_oled():
    """初始化OLED显示器"""
    global _oled_instance
    if _oled_instance is None:
        try:
            _oled_instance = OLEDDisplay()
        except RuntimeError:
            _oled_instance = OLEDDisplay._instance
        except Exception as e:
            print(f"OLED初始化失败: {e}")
            _oled_instance = MockOLEDDisplay()
    return _oled_instance

def get_oled():
    """获取OLED显示器实例"""
    global _oled_instance
    if _oled_instance is None:
        init_oled()
    return _oled_instance

def oled_print(text, timestamp=True):
    """OLED打印函数"""
    try:
        oled = get_oled()
        if hasattr(oled, 'println'):
            oled.println(text, timestamp)
        else:
            if timestamp:
                time_str = datetime.now().strftime("%H:%M")
                print(f"[{time_str}] {text}")
            else:
                print(text)
    except Exception as e:
        print(f"OLED打印错误: {e}")
        print(f"回退到控制台: {text}")

def oled_status(status, listening=False, speaking=False):
    """设置OLED状态"""
    try:
        oled = get_oled()
        if hasattr(oled, 'set_status'):
            oled.set_status(status, listening, speaking)
        else:
            print(f"状态: {status} (录音:{listening}, 播放:{speaking})")
    except Exception as e:
        print(f"OLED状态设置错误: {e}")

def cleanup_oled():
    """清理OLED资源"""
    global _oled_instance
    if _oled_instance:
        try:
            if hasattr(_oled_instance, 'cleanup'):
                _oled_instance.cleanup()
        except Exception as e:
            print(f"OLED清理错误: {e}")
        finally:
            _oled_instance = None

# 虚拟OLED显示器
class MockOLEDDisplay:
    def __init__(self):
        print("使用虚拟OLED显示器")
    
    def println(self, text, timestamp=True):
        if timestamp:
            time_str = datetime.now().strftime("%H:%M")
            print(f"虚拟OLED: [{time_str}] {text}")
        else:
            print(f"虚拟OLED: {text}")
    
    def set_status(self, status_text, listening=False, speaking=False):
        status_str = []
        if listening: status_str.append("录音")
        if speaking: status_str.append("播放")
        print(f"虚拟OLED状态: {status_text} {' '.join(status_str)}")
    
    def cleanup(self):
        print("虚拟OLED清理完成")

# 测试函数
if __name__ == "__main__":
    try:
        oled = init_oled()
        
        oled_print("OLED测试开始")
        time.sleep(1)
        
        oled_status("测试模式", listening=True)
        oled_print("录音状态测试")
        time.sleep(2)
        
        oled_status("测试模式", speaking=True)
        oled_print("播放状态测试")
        time.sleep(2)
        
        oled_status("正常运行")
        oled_print("OLED测试完成")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("测试中断")
    finally:
        cleanup_oled()