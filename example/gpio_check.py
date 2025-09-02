#!/usr/bin/python3
"""
GPIO兼容性检查和修复脚本
用于解决lgpio库依赖问题
"""
import sys
import subprocess
import os

def check_gpio_libraries():
    """检查可用的GPIO库"""
    print("=== GPIO库检查 ===")
    
    libraries = [
        ('lgpio', 'lgpio'),
        ('gpiozero', 'gpiozero'),
        ('RPi.GPIO', 'RPi.GPIO'),
        ('pigpio', 'pigpio')
    ]
    
    available = []
    for name, module in libraries:
        try:
            __import__(module)
            print(f"✅ {name} - 已安装")
            available.append(name)
        except ImportError:
            print(f"❌ {name} - 未安装")
    
    return available

def install_lgpio():
    """安装lgpio库"""
    print("\n=== 安装lgpio库 ===")
    try:
        # 尝试系统包管理器安装
        result = subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-lgpio'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 通过apt安装lgpio成功")
            return True
    except Exception as e:
        print(f"apt安装失败: {e}")
    
    try:
        # 尝试pip安装
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'lgpio'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 通过pip安装lgpio成功")
            return True
    except Exception as e:
        print(f"pip安装失败: {e}")
    
    return False

def check_permissions():
    """检查GPIO权限"""
    print("\n=== GPIO权限检查 ===")
    
    # 检查用户是否在gpio组中
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        if 'gpio' in result.stdout:
            print("✅ 用户已在gpio组中")
        else:
            print("❌ 用户不在gpio组中")
            print("运行: sudo usermod -a -G gpio $USER")
            print("然后重新登录")
    except Exception as e:
        print(f"权限检查失败: {e}")
    
    # 检查/dev/gpiomem权限
    if os.path.exists('/dev/gpiomem'):
        stat = os.stat('/dev/gpiomem')
        print(f"✅ /dev/gpiomem 存在，权限: {oct(stat.st_mode)[-3:]}")
    else:
        print("❌ /dev/gpiomem 不存在")

def test_gpio():
    """测试GPIO功能"""
    print("\n=== GPIO功能测试 ===")
    
    try:
        from gpiozero import DigitalOutputDevice
        import time
        
        # 测试GPIO控制（使用非关键引脚）
        test_pin = DigitalOutputDevice(18, active_high=True, initial_value=False)
        
        print("测试GPIO控制...")
        for i in range(3):
            test_pin.on()
            time.sleep(0.1)
            test_pin.off()
            time.sleep(0.1)
        
        test_pin.close()
        print("✅ GPIO功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ GPIO功能测试失败: {e}")
        return False

def main():
    print("树莓派GPIO兼容性检查工具")
    print("=" * 40)
    
    # 检查可用库
    available = check_gpio_libraries()
    
    # 如果没有lgpio，尝试安装
    if 'lgpio' not in available:
        print("\n检测到lgpio未安装，尝试安装...")
        if install_lgpio():
            print("lgpio安装成功，警告应该消失")
        else:
            print("lgpio安装失败，但不影响OLED功能")
            print("gpiozero库可以正常工作")
    
    # 检查权限
    check_permissions()
    
    # 测试GPIO
    if test_gpio():
        print("\n🎉 GPIO配置正常，可以运行OLED程序")
    else:
        print("\n⚠️  GPIO测试失败，请检查硬件连接")
    
    print("\n建议:")
    print("1. 确保以下依赖已安装:")
    print("   sudo apt install python3-lgpio python3-spidev python3-smbus")
    print("2. 确保用户在gpio组中:")
    print("   sudo usermod -a -G gpio $USER")
    print("3. 重启后生效:")
    print("   sudo reboot")

if __name__ == "__main__":
    main()