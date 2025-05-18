import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import musicbrainzngs as mb
import libdiscid
import json
import subprocess
import threading
import time

from until.device.input import KeyListener, ecodes
MPV_SOCKET_PATH = "/tmp/mpv_socket"
CD_DEVICE = "/dev/sr0"

class MediaPlayer:
    def __init__(self):
        self.cd = CD()
        self._mpv = None
        self._monitor_thread = None
        self._stop_cd_monitor = False
        self.MPV_COMMAND = ["mpv", "--quiet", "--vo=null",
                            "--no-audio-display",
                            "--cache=auto",
                            "--input-ipc-server=" + MPV_SOCKET_PATH]

        self.key_listener = KeyListener()
        self.key_listener.start()
        self.key_listener.on(self.key_callback)

    def key_callback(self, device_name, evt):
         if evt.value == 2 and self.cd.is_inserted:  # key down
            if evt.code == ecodes.KEY_KP1:
                    self.eject()

         if evt.value == 0:  # key up
            if self.cd.is_inserted:
                if evt.code == ecodes.KEY_KP1:
                    if self.is_running:
                        self.pause_or_play()
                    else:
                        self.play()
                
                if evt.code == ecodes.KEY_KP2:
                    self.next_track()
            else:
                self.try_to_play()

    
    def try_to_play(self):
        print("try to play")

        self.load() #try to load cd

        if self.cd.is_inserted:
            self.play()

    def load(self):
        return self.cd.load()
    
    def play(self):
        print('playing audio from CD')
        self._mpv = subprocess.Popen(self.MPV_COMMAND + ['cdda://'], 
                                     bufsize=1,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True)
        # 启动监听线程
        threading.Thread(target=self._monitor_mpv_output, 
                        args=(self._mpv.stdout,),
                        daemon=True).start()
        
    def _monitor_mpv_output(self, pipe):
        """
        监听 mpv 进程输出
        """
        for line in pipe:
            if not line:
                break
            print(f"mpv: {line.strip()}")

            if 'Exiting...' in line:
                self.stop()
            
            if '[cdda]' in line:
                self.show_track_info()

    def stop(self):
        print('stopping audio from CD')
        if self.is_running:
            self._mpv.terminate()
            self._mpv = None

    def pause_or_play(self):
        if self.is_running and self.chapter is not None:
            print(self.is_paused)
            if self.is_paused == 'pause':
                self._run_command('set', 'pause', 'no')
            else:
                self._run_command('set', 'pause', 'yes')
        self.show_track_info()
            
    def next_track(self):
        if self.is_running and self.chapter is not None:
            try:
                self._run_command('add', 'chapter', '1')
            except Exception as e:
                print("last track.")
        self.show_track_info()

    def prev_track(self):
        if self.is_running and self.chapter is not None:
            self._run_command('add', 'chapter', '-1')
        self.show_track_info()

    def show_track_info(self):
        if self.is_running:
            print(f"track: {self.chapter+1} / {self.cd.track_length}")
            print(f"artist: {self.cd.artist}")
            print(f"album: {self.cd.album}")
            print(f"track: {self.cd.tracks[self.chapter][0]}")
        else:
            print("no track info")

    def eject(self):
        self.stop()
        self.cd.eject()

    def _run_command(self, *command):
        command_dict = {
            "command": command
        }
        command_json = json.dumps(command_dict) + '\n'
        socat = subprocess.Popen(['socat', '-', MPV_SOCKET_PATH], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        socat_output = socat.communicate(command_json.encode('utf-8'))
        if socat_output[0] is not None and \
                        len(socat_output[0]) != 0 and \
                        socat_output[1] is None:
            try:
                data = json.loads(socat_output[0].decode())
                print(f"run command_dict: {command_dict}")
                if 'data' in data:
                    return data['data']
                else:
                    return None
            except Exception as e:
                print(f"run command error: {e}")
                return None
            
    @property
    def is_running(self):
        '''
        check if the mpv is running
        '''
        return self._mpv is not None
    
    @property
    def chapter(self):
        if self.is_running:
            try:
                chapter = self._run_command('get_property', 'chapter')
                chapters = self._run_command('get_property', 'chapters')

                self.cd.track_length = int(chapters) #fix track length, because the track length is not correct
                if len(self.cd.tracks) != self.cd.track_length:
                    print(f"fix track length: {self.cd.track_length}")
                    self.cd.tracks = [[f"Track {i+1}", "Unknown"] for i in range(self.cd.track_length)]
                    
                return chapter
            except:
                return 0
        else:
            return None
    
    @property
    def is_paused(self):
        '''
        check if the mpv is paused
        '''
        if self.is_running:
            pause_state = self._run_command('get_property', 'pause')
            return 'pause' if pause_state else 'playing'
        else:
            return 'stopped'

    def start_cd_monitor(self):
        """
        开始监控CD设备变化
        """
        if self._monitor_thread is not None:
            return

        self._stop_cd_monitor = False
        self._monitor_thread = threading.Thread(target=self._monitor_cd)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop_cd_monitor(self):
        """
        停止监控CD设备变化
        """
        self._stop_cd_monitor = True
        if self._monitor_thread is not None:
            self._monitor_thread.join()
            self._monitor_thread = None

    def _monitor_cd(self):
        """
        监控CD设备变化的内部方法
        """
        cmd = ['udevadm', 'monitor', '--kernel', '--subsystem-match=block']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while not self._stop_cd_monitor:
            line = process.stdout.readline()
            if not line:
                break

            if 'sr0' in line and 'change' in line:
                print("cdrom content changed")
                try:
                    self.stop()
                    time.sleep(1)
                    is_loaded = self.load()  # 尝试重新加载CD
                    if is_loaded:
                        self.play()

                except Exception as e:
                    print(f"reload cd error: {e}")
                    self.stop()

        process.terminate()
        process.wait()


class CD:
    def __init__(self):
        self.disc = None
        self._cd_info = None
        self._is_cd_inserted = False
        self.artist = None
        self.album = None
        self.tracks = []
        self.track_length = 0

    def eject(self):
        print("eject cd")
        subprocess.Popen(['eject', CD_DEVICE])
        self._is_cd_inserted = False
        self.disc = None
        self._cd_info = None
        self.artist = None
        self.album = None
        self.tracks = []
        self.track_length = 0

    @property
    def is_inserted(self):
        return self._is_cd_inserted
    
    def load(self):
        '''
        加载CD
        '''
        try:
            print("read cd")
            self.disc = libdiscid.read('/dev/sr0')
            
            #set default value
            _toc = self.disc.toc.split(' ')
            self.artist = "Unknown"
            self.album = "Unknown Album"
            self.track_length = int(_toc[1])
            self.tracks = [[f"Track {i+1}", "Unknown"] for i in range(self.track_length)]
            self._is_cd_inserted=True

            #load cd info from file
            try:
                print(f"load cd info from config/cd/{self.disc.id}.json")
                _cd_info = open(f"config/cd/{self.disc.id}.json", "r").read()
                self._set_info(json.loads(_cd_info))
                return True
            except FileNotFoundError as e:
                print(f"load file error: {e}")
                _cd_info = None
            
            #if cd info is not found, get cd info from musicbrainz
            if _cd_info is None:
                try:
                    print(f"request {self.disc.id} from musicbrainz")
                    mb.set_useragent('muspi', '1.0', 'https://github.com/puterjam/muspi')
                    _cd_info = mb.get_releases_by_discid(self.disc.id, includes=["recordings", "artists"], cdstubs=False)

                    import os
                    os.makedirs("config/cd", exist_ok=True)
                    _cd_info = json.dumps(_cd_info)
                    with open(f"config/cd/{self.disc.id}.json", "w") as f:
                        f.write(_cd_info)
                    
                    self._set_info(json.loads(_cd_info))
                except mb.ResponseError as e:
                    print(f"request {self.disc.id} from musicbrainz error: {e}")
            
            return True

        except Exception as e:
            print(f"Error loading disc: {e}")
            self._is_cd_inserted=False
            return False

    def _set_info(self, cd_info):
        print("set cd info")
        self._cd_info = cd_info

        release = self._cd_info['disc']['release-list'][0]

        self.artist = release['artist-credit-phrase']
        self.album = release['title']
        medium_list = release['medium-list']
        medium_count = release['medium-count']

        for disc_count in range(medium_count):
            count = disc_count - 1
            if medium_list[count]['disc-list'][0]['id'] == self.disc.id:
                self.track_length = medium_list[count]['track-count']
                self.tracks = [[track['recording']['title'], track['recording']['artist-credit'][0]["artist"]["name"]]
                                  for track in medium_list[count]['track-list']]
                break

if __name__ == "__main__":
    mp = MediaPlayer()

    # try:
    #     is_loaded = mp.load()

    #     if is_loaded:
    #         mp.play()
    #         # 启动CD监控
    # except Exception as e:
    #     print(f"play error: {e}")
    #     print(f"error line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")

    mp.start_cd_monitor()
        
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监控")
        mp.stop()
        mp.stop_cd_monitor()