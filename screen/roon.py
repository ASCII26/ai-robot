import time
import threading
import queue
from roonapi import RoonApi, RoonDiscovery

from until.log import LOGGER
from .base import DisplayPlugin
from .share.component import scroll_text, draw_vu
from .share.icons import IconDrawer

class RoonDisplay(DisplayPlugin):
    def __init__(self, manager, width, height):
        self.name = "roon"
        super().__init__(manager, width, height)
        
        self.icon_drawer = None
        self.current_title = "play next"
        self.current_artist = "show info"
        self.play_state = "pause"
        self.volume = {"value": 0, "is_muted": False}
        self.last_play_time = time.time()

        self.metadata_queue = queue.Queue()
        self.is_played_yet = False
        self._start_roon_thread()

        self.need_auth = False

    def _start_roon_thread(self):
        def roon_auth():
            # self.set_active(True)
            # RoonDiscovery
            discover = RoonDiscovery(self.core_id)
            servers = discover.all()
            discover.stop()

            apis = [RoonApi(self.appinfo, None, server[0], server[1], False) for server in servers]
            auth_api = []
            while len(auth_api) == 0:
                LOGGER.info("Waiting for roon server authorisation")
                time.sleep(1)
                auth_api = [api for api in apis if api.token is not None]

            api = auth_api[0]
            LOGGER.info("Got roon server authorisation.")
            
            # This is what we need to reconnect
            self.core_id = api.core_id
            self.token = api.token

            # Save the token for next time
            with open("config/roon_core_id", "w") as f:
                f.write(self.core_id)
            with open("config/roon_token", "w") as f:
                f.write(self.token)

            for api in apis:
                api.stop()

            self.need_auth = False

        def roon_thread():
            # 初始化 Roon
            self.appinfo = {
                "extension_id": "Muspi_Extension",
                "display_name": "Muspi Roon Extension",
                "display_version": "1.0",
                "publisher": "Muspi",
                "email": "puterjam@gmail.com",
            }

            try:
                self.core_id = open("config/roon_core_id").read()
                self.token = open("config/roon_token").read()
            except OSError:
                LOGGER.warning("Please authorise first in roon app")
                self.need_auth = True

            if self.need_auth or self.core_id == '':
                self.core_id = None
                self.token = None
                roon_auth()
                
            try:
                # RoonApi
                discover = RoonDiscovery(self.core_id)
                server = discover.first()
                discover.stop()
                
                self.roon = RoonApi(self.appinfo, self.token, host=server[0], port=server[1])
                self.metadata_queue.put(("roon_init", True))  # 通知初始化完成

                LOGGER.info(f"Roon initialized in \033[1m\033[32m{self.roon.core_name}\033[0m.")
                while True:
                    try:
                        zones = self.roon.zones
                        for zone_id in zones:
                            zone = zones[zone_id]
                            zone_name = zone["display_name"]
                           
                            if "[Muspi]" in zone_name:
                                play_state = zone["state"]
                                self.metadata_queue.put(("play_state", play_state))
                                if "now_playing" in zone:
                                    if play_state == "playing":
                                        self.metadata_queue.put(("session_state", True))

                                    np = zone["now_playing"]
                                    if "three_line" in np:
                                        lines = np["three_line"]
                                        self.metadata_queue.put(("title", lines["line1"]))
                                        self.metadata_queue.put(("artist", lines["line2"]))
                                else:
                                    self.metadata_queue.put(("session_state", False))
                                 
                                        
                                # 更新音量
                                if "outputs" in zone:
                                    outputs = zone["outputs"]
                                    if outputs:  # 确保 outputs 列表不为空
                                        # 获取第一个输出的音量信息
                                        output = outputs[0]
                                        if "volume" in output:
                                            volume = output["volume"]
                                            self.metadata_queue.put(("volume", volume))
                            else:
                                pass

                        time.sleep(0.1)

                    except Exception as e:
                        LOGGER.error(f"Roon update error: {e}")
                        time.sleep(1)  # 出错时等待更长时间

                # receive state updates in your callback
                # self.roon.register_state_callback(roon_state_callback)
                
            except Exception as e:
                LOGGER.error(f"Roon initialization error: {e}")
                self.metadata_queue.put(("roon_init", False))
        
        # 启动 Roon 线程
        self.roon_thread = threading.Thread(target=roon_thread, daemon=True)
        self.roon_thread.start()


    def _read_metadata(self):
        try:
            while not self.metadata_queue.empty():
                metadata_type, value = self.metadata_queue.get_nowait()
                if metadata_type == "title":
                    self.current_title = value
                elif metadata_type == "artist":
                    self.current_artist = value
                elif metadata_type == "session_state":
                    if self.is_played_yet == False:
                        self.set_active(value)
                    if value:
                        self.last_play_time = time.time()
                        self.is_played_yet = True
                elif metadata_type == "play_state":
                    if self.play_state != value:
                        self.last_play_time = time.time()
                    self.play_state = value

                elif metadata_type == "volume":
                    self.volume = value
        except queue.Empty:
            pass
    
    def update(self):
        self.clear()
        
        if self.need_auth:
            scroll_text(self.draw, "Please authorise first in roon app", x=0, y=10, step=0, font=self.font8)
            return
        
        # initialize the icon drawer
        if self.icon_drawer is None:
            self.icon_drawer = IconDrawer(self.draw) 

        is_muted = self.volume["is_muted"]
        if is_muted:
            volume = 0
        else:
            if self.volume["type"] == "number":
                volume = self.volume["value"] / 100
            elif self.volume["type"] == "db":
                volume = (80 + self.volume["value"]) / 80
            else:
                volume = 0.5
        
        # draw the scrolling text
        scroll_step = self.get_step_time()
        if self.current_title and self.current_artist:
            scroll_text(self.draw, "ROON", x=24, y=0, step=scroll_step, font=self.font04b08)
            scroll_text(self.draw, self.current_title, x=24, y=10, step=scroll_step, font=self.font8)
            scroll_text(self.draw, self.current_artist, x=24, y=22, step=scroll_step, font=self.font8)
        
        ## draw the VU table
        if self.play_state == "playing":
            draw_vu(self.draw, volume_level=volume)

            if self.manager.sleep:
                self.manager.turn_on_screen()
            self.icon_drawer.draw_play(x=41, y=0)
        else:
            draw_vu(self.draw, volume_level=0.0)
            self.icon_drawer.draw_pause(x=41, y=0)
        
        ## draw the volume wave icon
        self.icon_drawer.draw_volume_wave(x=110, y=0, level=volume)
    
    def set_active(self, value):
        super().set_active(value)
        if value:
            self.last_play_time = time.time()
        
    def event_listener(self):
        self._read_metadata()
        
        # reset the sleep timer if the play state is playing
        if self.play_state == "playing":
            self.manager.reset_sleep_timer() # reset the sleep timer
        else:
            self.is_played_yet = False

        # check if the pause state has been more than 5 minutes
        if self.play_state == "paused" and time.time() - self.last_play_time > self.pause_timout:
            self.set_active(False)
    
    def is_playing(self):
        return self.play_state == "playing"