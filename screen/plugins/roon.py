import time
import threading
import queue
from roonapi import RoonApi, RoonDiscovery

from screen.base import DisplayPlugin
from ui.component import draw_scroll_text, draw_vu
from assets.icons import IconDrawer

from until.log import LOGGER
from until.device.input import ecodes
from until.config import config

# config path
CONFIG_PATH = "config/roon.json"

ROON_PLUGIN_INFO = {
    "extension_id": "Muspi_Extension",
    "display_name": "Muspi Roon Extension",
    "display_version": "1.0",
    "publisher": "Muspi",
    "email": "puterjam@gmail.com",
}

SUFFIX = "[roon]" # 后缀, 监听 roon 的 output 名字
 
class roon(DisplayPlugin):
    def __init__(self, manager, width, height):
        self.name = "roon"
        super().__init__(manager, width, height)
        
        self.icon_drawer = None
        self.zone_id = None
        self.current_title = "play next"
        self.current_artist = "show info"
        self.play_state = "pause"
        self.volume = {"value": 0, "is_muted": False}
        self.last_play_time = time.time()

        self.metadata_queue = queue.Queue()
        self.is_played_yet = False
        self._start_roon_thread()

        self.need_auth = False
        self.pause_timout = 30
        
        self.ready = False

    def _start_roon_thread(self):
        def roon_thread():
            # initialize Roon
            try:
                # load core_id and token from config file
                config_data = config.open(CONFIG_PATH)
                self.core_id = config_data["core_id"]
                self.token = config_data["token"]
            except Exception:
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
                
                self.roon = RoonApi(ROON_PLUGIN_INFO, self.token, host=server[0], port=server[1])                

                LOGGER.info(f"Roon initialized in \033[1m\033[32m{self.roon.core_name}\033[0m.")

                # Save the token for next time
                config.save(CONFIG_PATH, {
                    "core_id": self.roon.core_id,
                    "token": self.roon.token
                })       
                
                self.ready = True
                self.need_auth = False
        
                while True:
                    try:
                        zones = self.roon.zones
                        
                        for zone_id in zones:
                            zone = zones[zone_id]

                            if "outputs" in zone:
                                outputs = zone["outputs"]
                                if outputs:  # 确保 outputs 列表不为空
                                    # 获取第一个输出的音量信息
                                    for output in outputs:
                                        zone_name = output["display_name"]
                                        
                                        if zone_name.endswith(SUFFIX):
                                            play_state = zone["state"]
                                            self.metadata_queue.put(("zone_id", zone_id))
                                            self.metadata_queue.put(("play_state", play_state))
                                            self.metadata_queue.put(("zone_name", zone_name))

                                            if "volume" in output:
                                                volume = output["volume"]
                                                self.metadata_queue.put(("volume", volume))

                                            if "now_playing" in zone:
                                                if play_state == "playing":
                                                    self.metadata_queue.put(("session_state", True))

                                                np = zone["now_playing"]
                                                self.metadata_queue.put(("seek_position", np["seek_position"]))
                                                self.metadata_queue.put(("length", np["length"]))
                                                
                                                if "three_line" in np:
                                                    lines = np["three_line"]
                                                    self.metadata_queue.put(("title", lines["line1"]))
                                                    self.metadata_queue.put(("artist", lines["line2"]))
                                                    self.metadata_queue.put(("album", lines["line3"]))
                                            else:
                                                self.metadata_queue.put(("session_state", False))
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
                self.ready = False
        
        def roon_auth():
            # self.set_active(True)
            # RoonDiscovery
            discover = RoonDiscovery(self.core_id)
            servers = discover.all()
            discover.stop()

            apis = [RoonApi(ROON_PLUGIN_INFO, None, server[0], server[1], False) for server in servers]
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

            for api in apis:
                api.stop()
        
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
                elif metadata_type == "album":
                    self.current_album = value
                elif metadata_type == "zone_id":
                    self.zone_id = value
                elif metadata_type == "zone_name":
                    self.zone_name = value
                elif metadata_type == "session_state":
                    if not self.is_played_yet:
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
                elif metadata_type == "seek_position":
                    self.seek_position = value
                elif metadata_type == "length":
                    self.media_length = value
        except queue.Empty:
            pass
    
    def update(self):
        self.clear()
        
        if self.need_auth:
            draw_scroll_text(self.draw, "Need Authorise", (0, 8), font=self.font8, width=128, align="center")
            draw_scroll_text(self.draw, "Please Open Roon App", (0, 18), font=self.font8, width=128, align="center")
            return
        
        # initialize the icon drawer
        if self.icon_drawer is None:
            self.icon_drawer = IconDrawer(self.draw) 

        is_muted = self.volume["is_muted"]
        if is_muted:
            volume = 0
        else:
            volume_type = self.volume.get("type", "none")
            
            if volume_type == "number":
                volume = self.volume["value"] / 100
            elif volume_type == "db":
                volume = (80 + self.volume["value"]) / 80
            else:
                volume = 0.5
        
        if not self.ready:
            self.need_auth = True
            return
        
        # draw the scrolling text
        zone_name = (self.zone_name or "no output").replace(SUFFIX, "")
        
        offset = 28
        draw_scroll_text(self.draw, self.current_title, (offset, 10), width=100, font=self.font10, align="center")
        draw_scroll_text(self.draw, self.current_artist + " - " + self.current_album, (offset, 24), width=100, font=self.font8,align="center")
        # draw_scroll_text(self.draw, "♪" + zone_name, (58+offset, 0), width=48, font=self.font_status)
        draw_scroll_text(self.draw,  "♪" + zone_name, (6+offset, 0), width=90, font=self.font_status, align="center")
        draw_scroll_text(self.draw, "R", (95+offset, 0), font=self.font_status)
       
        ## draw the VU table
        if self.play_state == "playing":
            draw_vu(self.draw, volume_level=volume)
            if self.manager.sleep:
                self.manager.turn_on_screen()
            draw_scroll_text(self.draw, "⏵", (offset, 0), font=self.font_status)
        else:
            draw_vu(self.draw, volume_level=0.0)
            draw_scroll_text(self.draw, "⏸", (offset, 0), font=self.font_status)
        
        ## draw the volume wave icon
        # self.icon_drawer.draw_volume_wave(x=112, y=0, level=volume)
    
    def set_active(self, value):
        super().set_active(value)
        if value:
            self.last_play_time = time.time()
            self.manager.key_listener.on(self.key_callback)
        else:
            self.manager.key_listener.off(self.key_callback)
    
    # def adjust_volume(self, value):
    #     zone = self.roon.zones[self.zone_id]
    #     outputs = zone["outputs"]
        
    #     for output in outputs:
    #         if "volume" in output:
    #             output_id = output["output_id"]
    #             if value == "up":
    #                 self.roon.change_volume_percent(output_id, 5)
    #             elif value == "down":
    #                 self.roon.change_volume_percent(output_id, -5)
                

    def key_callback(self, device_name, evt):
        if evt.value == 1:  # key down
            if evt.code == ecodes.KEY_KP1 or evt.code == ecodes.KEY_PLAYPAUSE:
                self.roon.playback_control(self.zone_id, control="playpause")
            if evt.code == ecodes.KEY_KP2 or evt.code == ecodes.KEY_NEXTSONG:
                self.roon.playback_control(self.zone_id, control="next")
            if evt.code == ecodes.KEY_PREVIOUSSONG:   
                self.roon.playback_control(self.zone_id, control="previous")

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