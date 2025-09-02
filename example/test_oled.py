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

def test_imports():
    """测试必要的库导入"""
    print("检查库依赖...")
    
    try:
        import gpiozero
        print("✅ gpiozero库正常")
    except ImportError as e:
        print(f"❌ gpiozero库导入失败: {e}")
        return False
    
    try:
        import spidev
        print("✅ spidev库正常")
    except ImportError as e:
        print(f"❌ spidev库导入失败: {e}")
        print("请运行: sudo apt install python3-spidev")
        return False
    
    try:
        from smbus import SMBus
        print("✅ smbus库正常")
    except ImportError as e:
        print(f"❌ smbus库导入失败: {e}")
        print("请运行: sudo apt install python3-smbus")
        return False
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✅ PIL库正常")
    except ImportError as e:
        print(f"❌ PIL库导入失败: {e}")
        print("请运行: pip install Pillow")
        return False
    
    return True

def test_gpio_permissions():
    """测试GPIO权限"""
    print("检查GPIO权限...")
    
    if not os.path.exists('/dev/gpiomem'):
        print("❌ /dev/gpiomem不存在，请检查GPIO支持")
        return False
    
    try:
        # 尝试创建一个简单的GPIO对象
        from gpiozero import DigitalOutputDevice
        test_device = DigitalOutputDevice(18, active_high=True)
        test_device.close()
        print("✅ GPIO权限正常")
        return True
    except Exception as e:
        print(f"❌ GPIO权限错误: {e}")
        print("请运行: sudo usermod -a -G gpio $USER 然后重新登录")
        return False

try:
    # 先进行预检查
    if not test_imports():
        print("库依赖检查失败，请安装必要的依赖")
        sys.exit(1)
    
    if not test_gpio_permissions():
        print("GPIO权限检查失败，请检查权限配置")
        sys.exit(1)
    
    # 导入OLED显示模块
    from oled_display import init_oled, oled_print, oled_status, cleanup_oled
    
    def test_oled():
        print("开始OLED显示测试...")
        
        try:
            # 初始化OLED
            oled = init_oled()
            print("OLED初始化成功")
            
            # 测试基本显示
            oled_print("OLED测试开始", False)
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
                time.sleep(0.8)
                
            # 测试播放状态
            oled_status("播放测试", speaking=True) 
            oled_print("播放状态指示器测试")
            for i in range(5):
                oled_print(f"播放测试 {i+1}/5")
                time.sleep(0.8)
                
            # 测试长文本滚动
            oled_status("滚动测试")
            oled_print("这是一个很长的文本，用来测试文本区域的滚动功能是否正常工作")
            time.sleep(2)
            
            # 添加更多文本测试滚动
            for i in range(10):
                oled_print(f"滚动测试行 {i+1}")
                time.sleep(0.3)
                
            oled_status("测试完成")
            oled_print("OLED显示测试完成")
            print("✅ OLED显示测试完成，请检查显示屏是否正常显示内容")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ OLED测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    if __name__ == "__main__":
        success = False
        try:
            success = test_oled()
        except KeyboardInterrupt:
            print("测试被用户中断")
        except Exception as e:
            print(f"测试出现未知错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cleanup_oled()
            if success:
                print("🎉 测试成功！可以运行小智AI程序")
            else:
                print("❌ 测试失败，请检查硬件连接和配置")
            
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n解决方案:")
    print("1. 检查是否在正确的目录运行脚本")
    print("2. 安装lgpio库: sudo apt install python3-lgpio")  
    print("3. 安装其他依赖: sudo apt install python3-spidev python3-smbus")
    print("4. 检查硬件连接")
    print("5. 运行GPIO检查脚本: python gpio_check.py")
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()