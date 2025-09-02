#!/bin/bash
# 快速修复脚本 - 解决当前问题

echo "=== 快速修复小智AI问题 ==="

# 1. 安装lgpio库（消除警告）
echo "1. 安装lgpio库..."
sudo apt update
sudo apt install -y python3-lgpio

# 2. 安装其他可能缺失的依赖
echo "2. 安装音频和字体依赖..."
sudo apt install -y python3-pyaudio alsa-utils fonts-dejavu-core

# 3. 在虚拟环境中安装lgpio
echo "3. 在虚拟环境中安装lgpio..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install lgpio
    deactivate
fi

# 4. 创建简化的ALSA配置
echo "4. 修复ALSA音频配置..."
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
EOF

echo "✅ 快速修复完成！"
echo ""
echo "现在运行测试："
echo "  python test_oled.py"
echo ""
echo "然后运行小智AI："
echo "  python py-xiaozhi.py"