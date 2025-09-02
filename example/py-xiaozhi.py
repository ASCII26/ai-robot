#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import time
import requests
import paho.mqtt.client as mqtt
import threading
import pyaudio
import opuslib  # windwos平台需要将opus.dll 拷贝到C:\Windows\System32
import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
import logging
# from pynput import keyboard as pynput_keyboard  # 注释掉键盘控制，后续接入键盘时启用
import sys
import select

# 导入OLED显示模块
from oled_display_simple import oled_print, oled_status, init_oled, cleanup_oled

OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
MAC_ADDR = 'b8:27:eb:01:7c:15'
# {"mqtt":{"endpoint":"post-cn-apg3xckag01.mqtt.aliyuncs.com","client_id":"GID_test@@@cc_ba_97_20_b4_bc",
# "username":"Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01","password":"0mrkMFELXKyelhuYy2FpGDeCigU=",
# "publish_topic":"device-server","subscribe_topic":"devices"},"firmware":{"version":"0.9.9","url":""}}
mqtt_info = {}
aes_opus_info = {"type": "hello", "version": 3, "transport": "udp",
                 "udp": {"server": "120.24.160.13", "port": 8884, "encryption": "aes-128-ctr",
                         "key": "263094c3aa28cb42f3965a1020cb21a7", "nonce": "01000000ccba9720b4bc268100000000"},
                 "audio_params": {"format": "opus", "sample_rate": 24000, "channels": 1, "frame_duration": 60},
                 "session_id": "b23ebfe9"}

iot_msg = {"session_id": "635aa42d", "type": "iot",
           "descriptors": [{"name": "Speaker", "description": "当前 AI 机器人的扬声器",
                            "properties": {"volume": {"description": "当前音量值", "type": "number"}},
                            "methods": {"SetVolume": {"description": "设置音量",
                                                      "parameters": {
                                                          "volume": {"description": "0到100之间的整数", "type": "number"}
                                                      }
                                                      }
                                        }
                            },
                           {"name": "Lamp", "description": "一个测试用的灯",
                            "properties": {"power": {"description": "灯是否打开", "type": "boolean"}},
                            "methods": {"TurnOn": {"description": "打开灯", "parameters": {}},
                                        "TurnOff": {"description": "关闭灯", "parameters": {}}
                                        }
                            }
                           ]
           }
iot_status_msg = {"session_id": "635aa42d", "type": "iot", "states": [
    {"name": "Speaker", "state": {"volume": 50}}, {"name": "Lamp", "state": {"power": False}}]}
goodbye_msg = {"session_id": "b23ebfe9", "type": "goodbye"}
local_sequence = 0
listen_state = None
tts_state = None
key_state = None
audio = None
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp_socket.setblocking(False)
conn_state = False
mqttc = None
recv_audio_thread = threading.Thread()
send_audio_thread = threading.Thread()



def get_ota_version():
    global mqtt_info
    header = {
        'Device-Id': MAC_ADDR,
        'Content-Type': 'application/json'
    }
    post_data = {"flash_size": 16777216, "minimum_free_heap_size": 8318916, "mac_address": f"{MAC_ADDR}",
                 "chip_model_name": "esp32s3", "chip_info": {"model": 9, "cores": 2, "revision": 2, "features": 18},
                 "application": {"name": "xiaozhi", "version": "0.9.9", "compile_time": "Jan 22 2025T20:40:23Z",
                                 "idf_version": "v5.3.2-dirty",
                                 "elf_sha256": "22986216df095587c42f8aeb06b239781c68ad8df80321e260556da7fcf5f522"},
                 "partition_table": [{"label": "nvs", "type": 1, "subtype": 2, "address": 36864, "size": 16384},
                                     {"label": "otadata", "type": 1, "subtype": 0, "address": 53248, "size": 8192},
                                     {"label": "phy_init", "type": 1, "subtype": 1, "address": 61440, "size": 4096},
                                     {"label": "model", "type": 1, "subtype": 130, "address": 65536, "size": 983040},
                                     {"label": "storage", "type": 1, "subtype": 130, "address": 1048576,
                                      "size": 1048576},
                                     {"label": "factory", "type": 0, "subtype": 0, "address": 2097152, "size": 4194304},
                                     {"label": "ota_0", "type": 0, "subtype": 16, "address": 6291456, "size": 4194304},
                                     {"label": "ota_1", "type": 0, "subtype": 17, "address": 10485760,
                                      "size": 4194304}],
                 "ota": {"label": "factory"},
                 "board": {"type": "bread-compact-wifi", "ssid": "chuchu", "rssi": -58, "channel": 6,
                           "ip": "192.168.31.100", "mac": "b8:27:eb:01:7c:15"}}

    response = requests.post(OTA_VERSION_URL, headers=header, data=json.dumps(post_data))
    oled_print("连接小智服务器成功")
    oled_print(f"响应: {response.status_code}")
    logging.info(f"get version: {response}")
    mqtt_info = response.json()['mqtt']


def aes_ctr_encrypt(key, nonce, plaintext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_ctr_decrypt(key, nonce, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext


def send_audio():
    global aes_opus_info, udp_socket, local_sequence, listen_state, audio
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    server_ip = aes_opus_info['udp']['server']
    server_port = aes_opus_info['udp']['port']
    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    
    mic = None
    try:
        # 打开麦克风流，增加缓冲区大小以避免溢出
        mic = audio.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=1920,  # 增加缓冲区大小
            input_device_index=None  # 使用默认输入设备
        )
        
        oled_print("音频录制启动")
        oled_status("录音中", listening=True)
        
        while True:
            if listen_state == "stop":
                time.sleep(0.1)
                continue
                
            try:
                # 读取音频数据，添加异常处理
                data = mic.read(960, exception_on_overflow=False)  # 忽略溢出
                # 编码音频数据
                encoded_data = encoder.encode(data, 960)
                
                # nonce插入data.size local_sequence_
                local_sequence += 1
                new_nonce = nonce[0:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(local_sequence, '08x')
                # 加密数据，添加nonce
                encrypt_encoded_data = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(new_nonce), bytes(encoded_data))
                data = bytes.fromhex(new_nonce) + encrypt_encoded_data
                sent = udp_socket.sendto(data, (server_ip, server_port))
                
            except Exception as read_error:
                oled_print(f"音频错误: {str(read_error)[:20]}")
                time.sleep(0.01)
                continue
                
    except Exception as e:
        oled_print(f"录音错误: {str(e)[:20]}")
    finally:
        oled_print("录音结束")
        oled_status("就绪")
        local_sequence = 0
        # 安全关闭音频流
        if mic and hasattr(mic, '_stream'):
            try:
                if mic._is_running:
                    mic.stop_stream()
                mic.close()
            except Exception as close_error:
                oled_print(f"关闭音频流错误: {str(close_error)[:20]}")
        udp_socket = None


def recv_audio():
    global aes_opus_info, udp_socket, audio
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    sample_rate = aes_opus_info['audio_params']['sample_rate']
    frame_duration = aes_opus_info['audio_params']['frame_duration']
    frame_num = int(frame_duration / (1000 / sample_rate))
    oled_print(f"音频接收: {sample_rate}Hz")
    
    # 初始化Opus解码器
    decoder = opuslib.Decoder(sample_rate, 1)
    spk = None
    
    try:
        spk = audio.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=sample_rate, 
            output=True, 
            frames_per_buffer=frame_num
        )
        
        oled_print("等待AI回复")
        oled_status("播放中", speaking=True)
        
        while True:
            try:
                data, server = udp_socket.recvfrom(4096)
                # 解密数据,分离nonce
                split_encrypt_encoded_data_nonce = data[:16]
                split_encrypt_encoded_data = data[16:]
                decrypt_data = aes_ctr_decrypt(bytes.fromhex(key),
                                               split_encrypt_encoded_data_nonce,
                                               split_encrypt_encoded_data)
                # 解码播放音频数据
                decoded_audio = decoder.decode(decrypt_data, frame_num)
                spk.write(decoded_audio)
                
            except socket.timeout:
                time.sleep(0.01)
                continue
            except Exception as recv_error:
                oled_print(f"接收错误: {str(recv_error)[:20]}")
                time.sleep(0.01)
                continue
                
    except Exception as e:
        oled_print(f"播放错误: {str(e)[:20]}")
    finally:
        oled_print("播放结束")
        oled_status("就绪")
        # 安全关闭音频流
        if spk and hasattr(spk, '_stream'):
            try:
                if spk._is_running:
                    spk.stop_stream()
                spk.close()
            except Exception as close_error:
                oled_print(f"关闭输出流错误: {str(close_error)[:20]}")
        udp_socket = None


def list_audio_devices():
    """列出可用的音频设备"""
    oled_print("=== 音频设备 ===", False)
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    input_devices = []
    output_devices = []
    
    for i in range(0, numdevices):
        device_info = audio.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            input_devices.append((i, device_info.get('name')))
        if device_info.get('maxOutputChannels') > 0:
            output_devices.append((i, device_info.get('name')))
    
    oled_print(f"输入设备: {len(input_devices)}个")
    for idx, name in input_devices[:2]:  # 只显示前2个
        oled_print(f"  {idx}: {name[:15]}")
    
    oled_print(f"输出设备: {len(output_devices)}个")
    for idx, name in output_devices[:2]:  # 只显示前2个  
        oled_print(f"  {idx}: {name[:15]}")
    
    return input_devices, output_devices


def test_audio_devices():
    """测试音频设备"""
    input_devices, output_devices = list_audio_devices()
    
    if not input_devices:
        oled_print("❌ 未找到音频输入设备")
        return False
    
    if not output_devices:
        oled_print("❌ 未找到音频输出设备")
        return False
    
    oled_print("✅ 音频设备正常")
    return True


def on_message(client, userdata, message):
    global aes_opus_info, udp_socket, tts_state, recv_audio_thread, send_audio_thread
    msg = json.loads(message.payload)
    
    if msg['type'] == 'hello':
        oled_print("建立语音连接")
        aes_opus_info = msg
        udp_socket.connect((msg['udp']['server'], msg['udp']['port']))
        # 检查recv_audio_thread线程是否启动
        if not recv_audio_thread.is_alive():
            recv_audio_thread = threading.Thread(target=recv_audio)
            recv_audio_thread.start()
        else:
            oled_print("接收线程已运行")
        # 检查send_audio_thread线程是否启动
        if not send_audio_thread.is_alive():
            send_audio_thread = threading.Thread(target=send_audio)
            send_audio_thread.start()
        else:
            oled_print("发送线程已运行")
            
    elif msg['type'] == 'tts':
        tts_state = msg['state']
        if msg['state'] == 'start':
            # 显示AI回复的文本内容
            if 'text' in msg:
                oled_print(f"小智: {msg['text']}")
            else:
                oled_print("小智正在回复...")
        elif msg['state'] == 'sentence_start':
            # 如果是句子开始，也显示文本
            if 'text' in msg:
                oled_print(f"小智: {msg['text']}")
                
    elif msg['type'] == 'asr':
        # 语音识别结果
        if 'text' in msg:
            oled_print(f"你说: {msg['text']}")
            
    elif msg['type'] == 'goodbye':
        if udp_socket and msg.get('session_id') == aes_opus_info.get('session_id'):
            oled_print("会话结束")
            aes_opus_info['session_id'] = None
            
    else:
        # 其他类型的消息，显示更多信息
        oled_print(f"收到: {msg['type']}")


def on_connect(client, userdata, flags, rs, pr):
    # subscribe_topic = mqtt_info['subscribe_topic'].split("/")[0] + '/p2p/GID_test@@@' + MAC_ADDR.replace(':', '_')
    # print(f"subscribe topic: {subscribe_topic}")
    # 订阅主题
    # client.subscribe(subscribe_topic)
    oled_print("MQTT连接成功")


def push_mqtt_msg(message):
    global mqtt_info, mqttc
    mqttc.publish(mqtt_info['publish_topic'], json.dumps(message))


def test_aes():
    nonce = "0100000030894a57f148f4f900000000"
    key = "f3aed12668b8bc72ba41461d78e91be9"

    plaintext = b"Hello, World!"

    # Encrypt the plaintext
    ciphertext = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(nonce), plaintext)
    print(f"Ciphertext: {ciphertext.hex()}")

    # Decrypt the ciphertext back to plaintext
    decrypted_plaintext = aes_ctr_decrypt(bytes.fromhex(key), bytes.fromhex(nonce), ciphertext)
    print(f"Decrypted plaintext: {decrypted_plaintext}")


def test_audio():
    key = urandom(16)  # AES-256 key
    print(f"Key: {key.hex()}")
    nonce = urandom(16)  # Initialization vector (IV) or nonce for CTR mode
    print(f"Nonce: {nonce.hex()}")

    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    decoder = opuslib.Decoder(16000, 1)
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
    mic = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    spk = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=960)

    try:
        while True:
            # 读取音频数据
            data = mic.read(960)
            # 编码音频数据
            encoded_data = encoder.encode(data, 960)
            # 加密数据，添加nonce
            encrypt_encoded_data = nonce + aes_ctr_encrypt(key, nonce, bytes(encoded_data))
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:len(nonce)]
            split_encrypt_encoded_data = encrypt_encoded_data[len(nonce):]
            decrypt_data = aes_ctr_decrypt(key, split_encrypt_encoded_data_nonce, split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, 960))
            # print(f"Encoded frame size: {len(encoded_data)} bytes")
    except KeyboardInterrupt:
        print("停止录制.")
    finally:
        # 关闭流和PyAudio
        mic.stop_stream()
        mic.close()
        spk.stop_stream()
        spk.close()
        p.terminate()


def on_space_key_press(event):
    global key_state, udp_socket, aes_opus_info, listen_state, conn_state
    if key_state == "press":
        return
    key_state = "press"
    # 判断是否需要发送hello消息
    if conn_state is False or aes_opus_info['session_id'] is None:
        conn_state = True
        # 发送hello消息,建立udp连接
        hello_msg = {"type": "hello", "version": 3, "transport": "udp",
                     "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}
        push_mqtt_msg(hello_msg)
        oled_print("发送hello消息")
    if tts_state == "start" or tts_state == "entence_start":
        # 在播放状态下发送abort消息
        push_mqtt_msg({"type": "abort"})
        oled_print("中断TTS播放")
    if aes_opus_info['session_id'] is not None:
        # 发送start listen消息
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "start", "mode": "manual"}
        oled_print("开始监听")
        push_mqtt_msg(msg)


def on_space_key_release(event):
    global aes_opus_info, key_state
    key_state = "release"
    # 发送stop listen消息
    if aes_opus_info['session_id'] is not None:
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "stop"}
        oled_print("停止监听")
        push_mqtt_msg(msg)


# ============= 键盘控制函数 (注释掉，后续接入键盘时启用) =============
# def on_press(key):
#     if key == pynput_keyboard.Key.space:
#         on_space_key_press(None)


# def on_release(key):
#     if key == pynput_keyboard.Key.space:
#         on_space_key_release(None)
#     # Stop listener
#     if key == pynput_keyboard.Key.esc:
#         return False


# ============= 命令行控制函数 =============
def command_line_control():
    """命令行控制函数"""
    oled_print("=== 命令行控制 ===", False)
    oled_print("命令: s-开始 t-停止 q-退出", False)
    
    while True:
        try:
            cmd = input("命令: ").strip().lower()
            
            if cmd in ['start', 's']:
                oled_print(">> 开始语音识别")
                on_space_key_press(None)
                
            elif cmd in ['stop', 't']:
                oled_print(">> 停止语音识别")
                on_space_key_release(None)
                
            elif cmd in ['quit', 'q']:
                oled_print(">> 正在退出...")
                # 发送goodbye消息
                if aes_opus_info.get('session_id'):
                    goodbye_msg = {"session_id": aes_opus_info['session_id'], "type": "goodbye"}
                    push_mqtt_msg(goodbye_msg)
                    oled_print("发送goodbye消息")
                cleanup_oled()
                sys.exit(0)
                
            elif cmd in ['help', 'h']:
                oled_print("=== 帮助信息 ===", False)
                oled_print("s/start - 开始录音", False)
                oled_print("t/stop  - 停止录音", False)
                oled_print("q/quit  - 退出程序", False)
                oled_print("h/help  - 显示帮助", False)
                
            else:
                oled_print(f"未知命令: {cmd}")
                
        except (KeyboardInterrupt, EOFError):
            oled_print("键盘中断，退出")
            cleanup_oled()
            sys.exit(0)
        except Exception as e:
            oled_print(f"命令错误: {str(e)[:15]}")


def run():
    global mqtt_info, mqttc
    
    # 初始化OLED显示
    init_oled()
    oled_status("初始化")
    
    # 检测音频设备
    if not test_audio_devices():
        oled_print("音频设备检测失败")
        cleanup_oled()
        return
    
    # 获取mqtt与版本信息
    oled_print("连接小智服务器...")
    oled_status("连接中")
    get_ota_version()
    
    # ============= 键盘监听 (注释掉，后续接入键盘时启用) =============
    # listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
    # listener.start()
    
    # 创建客户端实例
    mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    mqttc.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                  tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    
    # 在后台线程中启动MQTT
    mqtt_thread = threading.Thread(target=lambda: mqttc.connect(host=mqtt_info['endpoint'], port=8883) or mqttc.loop_forever())
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    # 等待MQTT连接建立
    time.sleep(2)
    oled_print("系统就绪")
    oled_status("就绪")
    
    # 启动命令行控制
    command_line_control()


if __name__ == "__main__":
    try:
        audio = pyaudio.PyAudio()
        run()
    except Exception as e:
        oled_print(f"系统错误: {str(e)[:15]}")
        cleanup_oled()
    finally:
        if audio:
            audio.terminate()