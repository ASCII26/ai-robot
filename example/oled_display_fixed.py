#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
OLED显示管理器 - 修复版本
解决GPIO冲突、字体加载和音频配置问题
"""
import sys
import os
import threading
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 简化的文本显示类（避免复杂的依赖）
class SimpleTextArea:
    def __init__(self, width=108, height=24):
        self.width = width
        self.height = height
        self.lines = []
        self.max_lines = 3  # 最多显示3行
        
        # 尝试加载字体，失败时使用默认字体
        try:
            # 尝试加载项目字体
            font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'assets/fonts/fusion-pixel-8px.ttf')
            if os.path.exists(font_path):
                self.font = ImageFont.truetype(font_path, 8)
            else:
                # 使用系统默认字体
                self.font = ImageFont.load_default()
        except Exception:
            # 最后的备选方案
            self.font = ImageFont.load_default()
    
    def append_text(self, text):
        """添加新文本"""
        # 简单换行处理
        max_chars = self.width // 6  # 假设每个字符6像素宽
        if len(text) > max_chars:
            text = text[:max_chars-3] + "..."
        
        self.lines.append(text)
        
        # 保持最大行数限制
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
        """初始化OLED显示器"""
        self.width = width
        self.height = height
        
        # 全局实例管理 - 避免重复初始化
        if hasattr(OLEDDisplay, '_instance'):
            raise RuntimeError("OLED显示器已经初始化，请使用get_oled()获取实例")
        OLEDDisplay._instance = self
        
        # 初始化硬件 - 添加异常处理
        self.disp = None
        try:
            from drive.SSD1305 import SSD1305
            self.disp = SSD1305()
            self.disp.Init()
            self.disp.clear()
            print("OLED硬件初始化成功")
        except Exception as e:
            print(f"OLED硬件初始化失败: {e}")
            print("将使用虚拟显示模式")
            # 不退出，继续运行但不显示到硬件
        
        # 初始化文本显示区域
        self.text_area = SimpleTextArea(width=width-20, height=height-8)
        
        # 尝试加载字体
        try:
            font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'assets/fonts/fusion-pixel-8px.ttf')
            if os.path.exists(font_path):
                self.status_font = ImageFont.truetype(font_path, 5)
            else:
                self.status_font = ImageFont.load_default()
        except Exception:
            self.status_font = ImageFont.load_default()
        
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
        self.println("=== 小智 AI ===", False)
        self.println("正在初始化...", False)
        
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
        draw.text((2, 0), self.status_text, font=self.status_font, fill=255)
        
        # 绘制状态指示器
        if self.is_listening:
            # 录音指示器 (红点闪烁效果)
            if int(time.time() * 2) % 2:  # 每0.5秒闪烁
                draw.ellipse((self.width-10, 1, self.width-4, 7), outline=255, fill=255)
            draw.text((self.width-15, 0), "REC", font=self.status_font, fill=255)
            
        elif self.is_speaking:
            # 播放指示器
            draw.text((self.width-15, 0), "PLAY", font=self.status_font, fill=255)
            
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
                if self.disp:
                    try:
                        self.disp.getbuffer(main_image)
                        self.disp.ShowImage()
                    except Exception as e:
                        print(f"OLED显示更新错误: {e}")
                        # 不退出循环，继续运行
                
                time.sleep(1/10)  # 10 FPS更新率，降低CPU使用
                
            except Exception as e:
                print(f"OLED显示循环错误: {e}")
                time.sleep(0.5)
                
    def cleanup(self):
        """清理资源"""
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
            # 如果已经有实例，直接返回
            _oled_instance = OLEDDisplay._instance
        except Exception as e:
            print(f"OLED初始化失败: {e}")
            # 创建一个虚拟显示器继续运行
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
            # 回退到控制台输出
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

# 虚拟OLED显示器（用于测试和调试）
class MockOLEDDisplay:
    """虚拟OLED显示器，只输出到控制台"""
    def __init__(self):
        self.status_text = "小智AI"
        self.is_listening = False
        self.is_speaking = False
        print("使用虚拟OLED显示器")
    
    def println(self, text, timestamp=True):
        if timestamp:
            time_str = datetime.now().strftime("%H:%M")
            print(f"虚拟OLED: [{time_str}] {text}")
        else:
            print(f"虚拟OLED: {text}")
    
    def set_status(self, status_text, listening=False, speaking=False):
        self.status_text = status_text
        self.is_listening = listening
        self.is_speaking = speaking
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