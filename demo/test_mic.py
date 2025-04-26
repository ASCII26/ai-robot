import pyaudio
import opuslib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
import time
import numpy as np
from scipy import signal

# 设备采样率
DEVICE_RATE = 48000
# 目标采样率
TARGET_RATE = 16000
# 降采样比例
RESAMPLE_RATIO = TARGET_RATE / DEVICE_RATE
FRAME_SIZE = 960  # Opus 帧大小

def resample_audio(data, original_rate, target_rate):
    """将音频数据从原始采样率重采样到目标采样率"""
    # 将字节数据转换为 numpy 数组
    samples = np.frombuffer(data, dtype=np.int16)
    # 计算重采样后的样本数
    num_samples = int(len(samples) * target_rate / original_rate)
    # 重采样
    resampled = signal.resample(samples, num_samples)
    # 转换回 int16 并返回字节
    return resampled.astype(np.int16).tobytes()

def aes_ctr_encrypt(key, nonce, plaintext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_ctr_decrypt(key, nonce, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext

def test_audio():
    key = urandom(16)  # AES-256 key
    print(f"Key: {key.hex()}")
    nonce = urandom(16)  # Initialization vector (IV) or nonce for CTR mode
    print(f"Nonce: {nonce.hex()}")

    # 初始化Opus编码器，使用目标采样率
    encoder = opuslib.Encoder(TARGET_RATE, 1, opuslib.APPLICATION_AUDIO)
    decoder = opuslib.Decoder(TARGET_RATE, 1)
    
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    try:
        # 打开麦克风流
        mic = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=DEVICE_RATE,
            input=True,
            input_device_index=1,  # 使用 USB 音频设备
            frames_per_buffer=FRAME_SIZE,
            start=False  # 先不启动流
        )
        
        # 打开扬声器流
        spk = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=DEVICE_RATE,
            output=True,
            frames_per_buffer=FRAME_SIZE,
            start=False  # 先不启动流
        )
        
        # 启动流
        mic.start_stream()
        spk.start_stream()
        
        print("开始录制和播放...")
        
        while True:
            try:
            # 读取音频数据
                data = mic.read(FRAME_SIZE, exception_on_overflow=False)
                
                # 降采样到目标采样率
                resampled_data = resample_audio(data, DEVICE_RATE, TARGET_RATE)
                
            # 编码音频数据
                encoded_data = encoder.encode(resampled_data, int(FRAME_SIZE * RESAMPLE_RATIO))
                
            # 加密数据，添加nonce
            encrypt_encoded_data = nonce + aes_ctr_encrypt(key, nonce, bytes(encoded_data))
                
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:len(nonce)]
            split_encrypt_encoded_data = encrypt_encoded_data[len(nonce):]
            decrypt_data = aes_ctr_decrypt(key, split_encrypt_encoded_data_nonce, split_encrypt_encoded_data)
                
            # 解码播放音频数据
                decoded_data = decoder.decode(decrypt_data, int(FRAME_SIZE * RESAMPLE_RATIO))
                
                # 将解码后的数据重采样回设备采样率
                playback_data = resample_audio(decoded_data, TARGET_RATE, DEVICE_RATE)
                
                # 播放音频
                spk.write(playback_data)
                
                # 添加小延迟，避免 CPU 占用过高
                time.sleep(0.001)
                
            except Exception as e:
                print(f"处理音频数据时出错: {e}")
                time.sleep(0.1)  # 出错时等待一段时间
                continue
                
    except KeyboardInterrupt:
        print("停止录制.")
    finally:
        # 关闭流和PyAudio
        if 'mic' in locals():
        mic.stop_stream()
        mic.close()
        if 'spk' in locals():
        spk.stop_stream()
        spk.close()
        p.terminate()
        
if __name__ == "__main__":
    test_audio()