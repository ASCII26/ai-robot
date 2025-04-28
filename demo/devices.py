import sounddevice as sd
print("可用音频输入设备：")
for i, dev in enumerate(sd.query_devices()):
    if dev["max_input_channels"] > 0:
        print(f"[{i}] {dev['name']} - 输入通道数: {dev['max_input_channels']}")

print("可用音频输出设备：")
for i, dev in enumerate(sd.query_devices()):
    if dev["max_output_channels"] > 0:
        print(f"[{i}] {dev['name']} - 输出通道数: {dev['max_output_channels']}")
