#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
OLED显示测试脚本
在运行小智AI之前，先运行此脚本测试OLED显示是否正常
"""
import time
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from oled_display import init_oled, oled_print, oled_status, cleanup_oled
    
    def test_oled():
        print("开始OLED显示测试...")
        
        # 初始化OLED
        oled = init_oled()
        
        # 测试基本显示
        oled_print("OLED测试开始")
        time.sleep(1)
        
        # 测试状态指示
        oled_status("测试模式")
        oled_print("状态栏测试")
        time.sleep(2)
        
        # 测试录音状态
        oled_status("录音测试", listening=True)
        oled_print("录音状态指示器测试")
        for i in range(5):
            oled_print(f"录音测试 {i+1}/5")
            time.sleep(1)
            
        # 测试播放状态
        oled_status("播放测试", speaking=True) 
        oled_print("播放状态指示器测试")
        for i in range(5):
            oled_print(f"播放测试 {i+1}/5")
            time.sleep(1)
            
        # 测试长文本滚动
        oled_status("滚动测试")
        oled_print("这是一个很长的文本，用来测试文本区域的滚动功能是否正常工作")
        time.sleep(2)
        
        # 添加更多文本测试滚动
        for i in range(10):
            oled_print(f"滚动测试行 {i+1}")
            time.sleep(0.5)
            
        oled_status("测试完成")
        oled_print("OLED显示测试完成")
        print("OLED显示测试完成，请检查显示屏是否正常显示内容")
        time.sleep(3)
        
    if __name__ == "__main__":
        try:
            test_oled()
        except KeyboardInterrupt:
            print("测试中断")
        except Exception as e:
            print(f"测试出错: {e}")
        finally:
            cleanup_oled()
            print("测试结束")
            
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保:")
    print("1. 在项目根目录运行此脚本")
    print("2. OLED硬件正确连接")
    print("3. 相关驱动库已安装")