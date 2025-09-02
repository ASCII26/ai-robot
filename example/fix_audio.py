#!/usr/bin/python3
"""
音频配置修复脚本
解决树莓派ALSA音频配置问题
"""
import os
import subprocess
import sys

def fix_alsa_config():
    """修复ALSA配置"""
    print("=== 修复ALSA音频配置 ===")
    
    # 创建简化的ALSA配置
    alsa_conf_content = """# 简化的ALSA配置文件
pcm.!default {
    type hw
    card 0
}

ctl.!default {
    type hw
    card 0
}"""
    
    try:
        # 创建用户ALSA配置目录
        home_dir = os.path.expanduser("~")
        asound_file = os.path.join(home_dir, ".asoundrc")
        
        with open(asound_file, 'w') as f:
            f.write(alsa_conf_content)
        
        print(f"✅ 创建ALSA配置文件: {asound_file}")
        return True
    except Exception as e:
        print(f"❌ ALSA配置失败: {e}")
        return False

def install_audio_packages():
    """安装必要的音频包"""
    print("\n=== 安装音频包 ===")
    
    packages = [
        'alsa-utils',
        'pulseaudio',
        'python3-pyaudio'
    ]
    
    for package in packages:
        try:
            print(f"安装 {package}...")
            result = subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} 安装成功")
            else:
                print(f"⚠️ {package} 安装可能有问题")
        except Exception as e:
            print(f"❌ {package} 安装失败: {e}")

def check_audio_devices():
    """检查音频设备"""
    print("\n=== 音频设备检查 ===")
    
    try:
        # 检查音频卡
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("可用音频输出设备:")
            print(result.stdout)
        else:
            print("❌ 无法获取音频设备列表")
    except Exception as e:
        print(f"音频设备检查失败: {e}")
    
    try:
        # 检查录音设备
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("可用音频输入设备:")
            print(result.stdout)
        else:
            print("❌ 无法获取录音设备列表")
    except Exception as e:
        print(f"录音设备检查失败: {e}")

def test_audio():
    """测试音频功能"""
    print("\n=== 音频功能测试 ===")
    
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        print("PyAudio可用设备:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} (输入:{info['maxInputChannels']}, 输出:{info['maxOutputChannels']})")
        
        p.terminate()
        print("✅ PyAudio测试成功")
        return True
    except ImportError:
        print("❌ PyAudio未安装")
        return False
    except Exception as e:
        print(f"❌ PyAudio测试失败: {e}")
        return False

def disable_jack():
    """禁用JACK音频服务"""
    print("\n=== 禁用JACK音频服务 ===")
    
    try:
        # 停止JACK服务
        subprocess.run(['sudo', 'systemctl', 'stop', 'jack'], 
                      capture_output=True, text=True)
        subprocess.run(['sudo', 'systemctl', 'disable', 'jack'], 
                      capture_output=True, text=True)
        print("✅ JACK服务已禁用")
    except Exception as e:
        print(f"禁用JACK失败: {e}")

def main():
    print("树莓派音频配置修复工具")
    print("=" * 40)
    
    # 更新包列表
    print("更新软件包列表...")
    try:
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        print("✅ 软件包列表更新成功")
    except Exception as e:
        print(f"❌ 软件包更新失败: {e}")
    
    # 安装音频包
    install_audio_packages()
    
    # 修复ALSA配置
    fix_alsa_config()
    
    # 禁用JACK
    disable_jack()
    
    # 检查音频设备
    check_audio_devices()
    
    # 测试PyAudio
    audio_ok = test_audio()
    
    print("\n" + "=" * 40)
    if audio_ok:
        print("🎉 音频配置修复完成!")
        print("现在可以运行小智AI程序了")
    else:
        print("⚠️ 音频配置可能还有问题")
        print("建议重启后再试: sudo reboot")
    
    print("\n建议的下一步:")
    print("1. 重启树莓派: sudo reboot")
    print("2. 测试OLED显示: python test_oled.py")
    print("3. 运行小智AI: python py-xiaozhi.py")

if __name__ == "__main__":
    if os.geteuid() == 0:
        print("❌ 请不要用sudo运行此脚本")
        sys.exit(1)
    main()