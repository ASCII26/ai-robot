import os
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
import time
from until.log import LOGGER

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_5 = ImageFont.truetype("./fonts/QuinqueFive.ttf", 5)
FONT_8 = ImageFont.truetype("./fonts/QuanPixel.ttf", 8)
FONT_16 = ImageFont.truetype("./fonts/QuanPixel.ttf", 16)


def welcome_screen(width, height,msg = "Muspi", logo_name="logo.png",logo_size=(24, 24)):
    """welcome screen"""
    image = Image.new('1', (width, height))
    try:
        # 使用绝对路径打开图片
        logo_path = os.path.join(BASE_DIR, "share", logo_name)
        logo = Image.open(logo_path)
        # 调整图片大小
        logo = logo.resize(logo_size)
        # 转换为单色模式
        logo = logo.convert('1')
    except Exception as e:
        LOGGER.error(f"无法加载logo图片: {e}")
        logo = None
    
    draw = ImageDraw.Draw(image)
    
    # 绘制边框
    draw.rectangle((0, 0, width-1, height-1), outline=255, width=1)
    
     # 绘制文字
    draw.text((60, (height - 16) // 2), msg, font=FONT_16, fill=255)

    # 如果logo加载成功，绘制logo
    if logo:
        x = (width - logo.width) // 5
        y = (height - logo.height) // 2
        image.paste(logo, (x, y))
    
    return image
    
DEFAULT_FRAME_TIME = 1.0 / 8.0  

class DisplayPlugin(ABC):
    """Base class for display plugins"""
    
    def __init__(self, manager, width, height):
        """Initialize the display plugin"""
        # Manager
        self.manager = manager
        self.width = width
        self.height = height
        
        # ID
        self.name = self.name or "base"
        
        # Image Buffer
        self.image = Image.new('1', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Fonts
        self.font5 = FONT_5
        self.font8 = FONT_8
        self.font16 = FONT_16

        
        # Parameters
        self.start_time = time.time()
        self.is_active = False # whether the plugin is active
        self.speed = 0.2  # speed parameter, default 1.0, means 1 unit per second
        self.pause_timout = 30   # 30 seconds

        LOGGER.info(f"[\033[1m{self.name}\033[0m] initialized.")

    @abstractmethod
    def update(self):
        """update the display content"""
        pass
    

    def is_playing(self):
        """check if the plugin is playing"""
        pass

    def event_listener(self):
        """listen to the metadata"""
        pass

    def get_active(self):
        """check if the plugin should be activated"""
        return self.is_active
    
    def get_frame_time(self):
        """get the current frame time"""
        return DEFAULT_FRAME_TIME

    def set_active(self, active):
        """set the active state of the plugin"""
        if self.manager.last_active != self and active:
            if self.manager.last_active:
                self.manager.last_active.set_active(False)
            self.manager.last_active = self
            LOGGER.info(f"[\033[1m\033[37m{self.name}\033[0m] set active. register id: {self.id}")
            self.manager.active_id = self.id
            if self.manager.sleep:
                self.manager.turn_on_screen()

        if self.manager.last_active == self and not active:
            self.manager.last_active = None

        self.is_active = active
    
    def get_step_time(self):
        """get the current step time, adjust according to the speed parameter"""
        elapsed = time.time() - self.start_time
        return int(elapsed * self.speed * 1000 / 16)  # 16ms is a unit

    def get_image(self):
        """get the current image"""
        return self.image
    
    def clear(self):
        """clear the display"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=0) 