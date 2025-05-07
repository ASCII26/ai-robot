import time
import sys
import signal
import os

from PIL import Image, ImageDraw

from drive import SSD1305
from until.input import KeyListener, ecodes
from until.volume import adjust_volume, detect_pcm_controls
from until.animation import Animation
from until.log import LOGGER
from screen.fonts import Fonts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# contrast value
CONTRAST = 128
ANIMATION_DURATION = 0.3
FONTS = Fonts()

def welcome_screen(
    width, height, msg="Muspi", logo_name="logo.png", logo_size=(24, 24)
):
    """welcome screen"""
    image = Image.new("1", (width, height))
    try:
        # 使用绝对路径打开图片
        logo_path = os.path.join(BASE_DIR, "ui", logo_name)
        logo = Image.open(logo_path)
        # 调整图片大小
        logo = logo.resize(logo_size)
        # 转换为单色模式
        logo = logo.convert("1")
    except Exception as e:
        LOGGER.error(f"无法加载logo图片: {e}")
        logo = None

    draw = ImageDraw.Draw(image)

    # 绘制边框
    draw.rectangle((0, 0, width - 1, height - 1), outline=255, width=1)

    # 绘制文字
    draw.text((60, (height - 16) // 2), msg, font=FONTS.size_16, fill=255)

    # 如果logo加载成功，绘制logo
    if logo:
        x = (width - logo.width) // 5
        y = (height - logo.height) // 2
        image.paste(logo, (x, y))

    return image


class DisplayManager:
    def __init__(self):
        """Initialize the display manager"""
        # init display
        self.disp = SSD1305.SSD1305()
        self.turn_on_screen()
        self.welcome()

        # init variables
        self.key_listener = KeyListener()
        self.last_active = None
        self.active_id = 0
        self.last_screen_image = None
        self.main_screen = Image.new("1", (self.disp.width, self.disp.height), 0)
        self.anim = Animation(ANIMATION_DURATION)
        self.anim.reset("main_screen")

        # init sleep
        self.sleep = False
        self.sleep_time = 10 * 60  # 10 minutes idle time
        self.sleep_count = time.time()
        self.longpress_count = time.time()
        self.longpress_time = 3

        # initialize plugins
        self.plugins = []
        # self.add_plugin(XiaozhiDisplay, auto_hide=False)
        # self.add_plugin(ClockDisplay, auto_hide=False)
        # self.add_plugin(DinoGameDisplay, auto_hide=False)
        # self.add_plugin(LifeDisplay, auto_hide=False)
        # self.add_plugin(AirPlayDisplay, auto_hide=True)
        # self.add_plugin(RoonDisplay, auto_hide=False)

        # register signal handler
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def add_plugin(self, plugin, auto_hide=False):
        id = len(self.plugins)
        plugin_instance = plugin(self, self.disp.width, self.disp.height)
        plugin_instance.id = id

        plugin = {
            "plugin": plugin_instance,
            "auto_hide": auto_hide,
            "is_active": False,
            "id": id,
        }
        self.plugins.append(plugin)

    def active_next(self):
        """activate the next plugin"""
        if self.last_active:
            self.last_screen_image = self.last_active.get_image()
            self.anim.reset("main_screen")
            self.last_active.set_active(False)

        next_id = (self.active_id + 1) % len(self.plugins)

        # 检查下一个插件是否是播放器且未在播放
        while (
            self.plugins[next_id]["auto_hide"]
            and hasattr(self.plugins[next_id]["plugin"], "is_playing")
            and not self.plugins[next_id]["plugin"].is_playing()
        ):
            next_id = (next_id + 1) % len(self.plugins)

        self.plugins[next_id]["plugin"].set_active(True)

    def signal_handler(self, signum, frame):
        """handle the termination signal"""
        LOGGER.info(f"get signal {signum}, cleaning up...")
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
                if evt.code == ecodes.KEY_VOLUMEUP:
                    if hasattr(self.last_active, "adjust_volume"):
                        self.last_active.adjust_volume("up")
                    else:
                        adjust_volume("up")
                if evt.code == ecodes.KEY_VOLUMEDOWN:
                    if hasattr(self.last_active, "adjust_volume"):
                        self.last_active.adjust_volume("down")
                    else:
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
                    self.plugins[0]["plugin"].set_active(
                        True
                    )  # set the first plugin as default active

                try:
                    self.last_active.update()
                    image = self.last_active.get_image()
                    screen_offset = 128

                    if self.last_screen_image is not None:
                        self.main_screen.paste(self.last_screen_image, (0, 0))

                    if self.anim.is_running("main_screen"):
                        screen_offset = round(
                            self.anim.run("main_screen", self.disp.width)
                        )
                        frame_time = 1.0 / 60.0
                    else:
                        frame_time = self.last_active.get_frame_time()
                        self.last_screen_image = None

                    self.main_screen.paste(image, (128 - screen_offset, 0))
                    self.disp.getbuffer(self.main_screen)
                    self.disp.ShowImage()

                except Exception as e:
                    import traceback

                    LOGGER.error(f"错误堆栈: {traceback.format_exc()}")
                    # if error keep frame
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
        self.disp.getbuffer(
            welcome_screen(
                self.disp.width,
                self.disp.height,
                msg="Muspi",
                logo_name="heart.png",
                logo_size=(24, 24),
            )
        )
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
        self.disp.set_contrast(CONTRAST)  # 128 is the default contrast value
        self.disp.set_screen_rotation(1)  # 180 degree rotation
        self.sleep = False

    def turn_off_screen(self):
        if not self.sleep:
            LOGGER.info("\033[1m\033[37mTurn off screen\033[0m")
            # self.cleanup(reset=True)
            self.disp.command(0xAE)
            self.disp.reset()
            self.sleep = True

    def cleanup(self, reset=True):
        self.disp.clear()
        if not reset:
            self.disp.getbuffer(welcome_screen(self.disp.width, self.disp.height))
            self.disp.ShowImage()
        else:
            self.disp.ShowImage()
            self.disp.reset()
