import time
import subprocess
import threading
import queue

from until.log import LOGGER
from .base import DisplayPlugin
from .share.component import scroll_text, draw_vu
from .share.icons import IconDrawer

class AirPlayDisplay(DisplayPlugin):
    def __init__(self, manager, width, height):
        self.name = "airplay"
        super().__init__(manager, width, height)
        
        self.icon_drawer = None
        self.current_title = "play next"
        self.current_artist = "show info"
        self.play_state = "pause"
        self.stream_volume = None
        self.last_play_time = time.time()  # record the last play time
        self.metadata_queue = queue.Queue()
        self._start_metadata_reader()
        
    
    def _start_metadata_reader(self):
        def metadata_reader_thread():
            process = subprocess.Popen(
                "shairport-sync-metadata-reader < /tmp/shairport-sync-metadata",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=False
            )
            
            while True:
                try:
                    line = process.stdout.readline()
                    if line:
                        decoded_line = line.decode('utf-8', errors='replace').strip()
                        if "Artist" in decoded_line:
                            try:
                                artist = decoded_line.split('"')[1]
                                self.metadata_queue.put(("artist", artist))
                            except:
                                pass
                        elif "Title" in decoded_line:
                            try:
                                title = decoded_line.split('"')[1]
                                self.metadata_queue.put(("title", title))
                            except:
                                pass
                        elif "Volume" in decoded_line:
                            try:
                                volume = decoded_line.split('"')[1].strip()
                                self.metadata_queue.put(("volume", volume))
                            except:
                                pass
                        elif "Play Session End." in decoded_line:
                            self.metadata_queue.put(("session_state", False))
                        elif "Play Session Begin." in decoded_line:
                            self.metadata_queue.put(("session_state", True))
                        elif "Resume." in decoded_line:
                            self.metadata_queue.put(("session_state", True))
                            self.metadata_queue.put(("play_state", "play"))
                        elif "Pause." in decoded_line:
                            self.metadata_queue.put(("play_state", "pause"))
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    LOGGER.error(f"read metadata error: {e}")
                    time.sleep(1)
        
        # start metadata reader thread
        self.metadata_thread = threading.Thread(target=metadata_reader_thread, daemon=True)
        self.metadata_thread.start()
    
    def _read_metadata(self):
        try:
            while not self.metadata_queue.empty():
                metadata_type, value = self.metadata_queue.get_nowait()
                if metadata_type == "title":
                    self.current_title = value
                elif metadata_type == "artist":
                    self.current_artist = value
                elif metadata_type == "session_state":
                    self.set_active(value)
                    if value:  # if start playing, update the last play time
                        self.last_play_time = time.time()
                elif metadata_type == "play_state":
                    if self.play_state != value:  # if play state changed
                        self.last_play_time = time.time()  # update the last play time
                    self.play_state = value
                elif metadata_type == "volume":
                    self.stream_volume = value
        except queue.Empty:
            pass
    
    def update(self):
        self.clear()
        
        # initialize the icon drawer
        if self.icon_drawer is None:
            self.icon_drawer = IconDrawer(self.draw)
        
        if self.stream_volume is None:
            volume = 0.5
        else:
            left_db, right_db, _, _ = map(float, self.stream_volume.split(','))
            volume = max(0, (min(left_db, right_db) + 100) / 100)  # convert the range of -144 to 0 to 0 to 1

        # self.icon_drawer.draw_airplay(x=24, y=0) 
        
        # draw the scrolling text
        scroll_step = self.get_step_time()
        if self.current_title and self.current_artist:
            scroll_text(self.draw, "AIRPLAY", x=24, y=0, step=scroll_step, font=self.font04b08)
            scroll_text(self.draw, self.current_title, x=24, y=10, step=scroll_step, font=self.font8)
            scroll_text(self.draw, self.current_artist, x=24, y=22, step=scroll_step, font=self.font8)
        
        # draw the VU table
        if self.play_state == "play":
            draw_vu(self.draw, volume_level=volume) 
            if self.manager.sleep:
                self.manager.turn_on_screen()
            # self.icon_drawer.draw_play(x=53, y=0)
        else:
            draw_vu(self.draw, volume_level=0.0)
            # self.icon_drawer.draw_pause(x=53, y=0)
        
        # draw the volume wave icon
        self.icon_drawer.draw_volume_wave(x=110, y=0, level=volume)
            
    def is_playing(self):
        return self.play_state == "play"

    def set_active(self, value):
        super().set_active(value)
        if value:
            self.last_play_time = time.time()
    
    def event_listener(self):
        self._read_metadata()
        
        if self.play_state == "play":
            self.manager.reset_sleep_timer() # reset the sleep timer

        # check if the pause state has been more than 5 minutes
        if self.play_state == "pause" and time.time() - self.last_play_time > self.pause_timout:  # 300 seconds = 5 minutes
            self.set_active(False)
