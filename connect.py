import time
import sys
import os
import signal

from drive import SSD1305

# add screen plugins
from screen.base import welcome_screen
from screen.roon import RoonDisplay
from screen.airplay import AirPlayDisplay
from screen.clock import ClockDisplay
from screen.dino import DinoGameDisplay
from screen.life import LifeDisplay


# add until plugins
from until.log import LOGGER
from until.input import KeyListener,ecodes
from until.volume import adjust_volume,detect_pcm_controls

# contrast value
CONTRAST = 128

# add debug information
current_dir = os.path.dirname(os.path.realpath(__file__))
LOGGER.info(f"working directory: \033[1m\033[37m{current_dir}\033[0m")

# modify the libdir path
libdir = os.path.join(current_dir, "drive")
LOGGER.info(f"driver directory: \033[1m\033[37m{libdir}\033[0m")

if os.path.exists(libdir):
    sys.path.append(libdir)
else:
    LOGGER.error(f"error: driver directory not found: {libdir}")
    sys.exit(1)

class DisplayManager:
    def __init__(self):
        """Initialize the display manager"""
        # init display
        self.disp = SSD1305.SSD1305()
        self.turn_on_screen()
        self.welcome()
        time.sleep(3)
        
        # init variables
        self.key_listener = KeyListener()
        self.last_active = None
        self.active_id = 0
        
        # init sleep
        self.sleep = False
        self.sleep_time = 10 * 60 # 10 minutes idle time
        self.sleep_count = time.time()
        self.longpress_count = time.time()
        self.longpress_time = 3
        
        # initialize plugins
        self.plugins = []
        self.add_plugin(ClockDisplay, is_player=False)
        self.add_plugin(DinoGameDisplay, is_player=False)
        self.add_plugin(LifeDisplay, is_player=False)
        self.add_plugin(AirPlayDisplay, is_player=True)
        self.add_plugin(RoonDisplay, is_player=True)
        
        
        # register signal handler
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def add_plugin(self, plugin, is_player=False):
        id = len(self.plugins)
        plugin_instance = plugin(self, self.disp.width, self.disp.height)
        plugin_instance.id = id
        
        
        plugin = {
            "plugin": plugin_instance,
            "is_player": is_player,
            "is_active": False,
            "id": id
        }
        self.plugins.append(plugin)
        
    def active_next(self):
        """activate the next plugin"""
        if self.last_active:
            self.last_active.set_active(False)
            
        next_id = (self.active_id + 1) % len(self.plugins)
        LOGGER.info(f"activate next plugin: {not self.plugins[next_id]['plugin'].is_playing()}")    
        # 检查下一个插件是否是播放器且未在播放
        while self.plugins[next_id]["is_player"] and \
              hasattr(self.plugins[next_id]["plugin"], 'is_playing') and \
              not self.plugins[next_id]["plugin"].is_playing():
            next_id = (next_id + 1) % len(self.plugins)
        
        self.plugins[next_id]["plugin"].set_active(True)
        
    def signal_handler(self, signum, frame):
        """handle the termination signal"""
        print(f"get signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)

    def key_callback(self, device_name, evt):
        """handle the key event"""

        if evt.value == 2:
            if evt.code == ecodes.KEY_FORWARD:
                if time.time() - self.longpress_count > self.longpress_time:
                    self.turn_off_screen()
                
        if evt.value == 1:  # key down
            if self.sleep:
                self.turn_on_screen()
            else:
                if evt.code == ecodes.KEY_FORWARD:
                    self.active_next()
                    self.longpress_count = time.time()
                elif evt.code == ecodes.KEY_VOLUMEUP:
                    adjust_volume("up")
                elif evt.code == ecodes.KEY_VOLUMEDOWN:
                    adjust_volume("down")

    def run(self):
        detect_pcm_controls()
        self.key_listener.start()
        self.key_listener.on(self.key_callback)

        try:
            while True:
                frame_start = time.time()
                self.sleep_check()

                for plugin in self.plugins:
                    plugin["plugin"].event_listener()
                
                if self.last_active is None:
                    self.plugins[0]["plugin"].set_active(True) # set the first plugin as default active
                
                try:
                    self.last_active.update()
                    image = self.last_active.get_image()
                    self.disp.getbuffer(image)
                    self.disp.ShowImage()
                    frame_time = self.last_active.get_frame_time()
                except Exception as e:
                    #if error keep frame
                    LOGGER.error(f"error: {e}")
                    frame_time = 0.1

                elapsed = time.time() - frame_start
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                
        except KeyboardInterrupt:
            LOGGER.warning("received keyboard interrupt, cleaning up...")
            self.cleanup(reset=False)
        except Exception as e:
            LOGGER.error(f"runtime error: {e}")
            self.cleanup(reset=False)
        finally:
            self.cleanup(reset=True)
    
    def welcome(self):
        self.disp.getbuffer(welcome_screen(self.disp.width, self.disp.height ,msg = "Hi.",logo_name="heart.png",logo_size=(24, 24)))
        self.disp.ShowImage()

    def reset_sleep_timer(self):
        self.sleep_count = time.time()

    def sleep_check(self):
        if time.time() - self.sleep_count > self.sleep_time:
            self.turn_off_screen()

    def turn_on_screen(self):
        LOGGER.info("\033[1m\033[37mTurn on screen\033[0m")
        self.reset_sleep_timer()
        self.disp.Init()
        self.disp.clear()        
        self.disp.set_contrast(CONTRAST) # 128 is the default contrast value
        self.disp.set_screen_rotation(1) # 180 degree rotation
        self.sleep = False
        

    def turn_off_screen(self):
        if self.sleep == False:
            LOGGER.info("\033[1m\033[37mTurn off screen\033[0m")
            # self.cleanup(reset=True)
            self.disp.command(0xAE)
            self.disp.reset()
            self.sleep = True

    def cleanup(self,reset=True):
        self.disp.clear()
        if reset==False:
            self.disp.getbuffer(welcome_screen(self.disp.width, self.disp.height))
            self.disp.ShowImage()
        else:
            self.disp.ShowImage()
            self.disp.reset()

if __name__ == "__main__":
    manager = DisplayManager()
    manager.run()