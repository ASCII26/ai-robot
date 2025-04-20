import sounddevice as sd
import scipy.io.wavfile as wav
import requests

# 设置输入设备 index
sd.default.device = (4, None)

# 录音参数
duration = 5
sample_rate = 44100
filename = "recorded.wav"

# 录音
print("开始说话...")
recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()
wav.write(filename, sample_rate, recording)
print("录音完成，上传 DeepSeek 识别...")

# 上传到 DeepSeek Whisper API
API_KEY = "sk-60915f600bb041f59b8a9ea2cdc1f78b"
url = "https://api.deepseek.com/audio/whisper"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

files = {
    "file": (filename, open(filename, "rb"), "audio/wav")
}

data = {
    "model": "deepseek-whisper",
    "language": "zh"
}

response = requests.post(url, headers=headers, files=files, data=data)

if response.ok:
    result = response.json()
    print("识别结果：", result["text"])
else:
    print("请求失败：", response.status_code, response.text)
