from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from until.log import LOGGER
from screen.manager import FONTS

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
        self.font_status = FONTS.size_5
        self.font8 = FONTS.size_8
        self.font10 = FONTS.size_10
        self.font12 = FONTS.size_12
        self.font16 = FONTS.size_16

        
        # Parameters
        self.is_active = False # whether the plugin is active
        self.pause_timout = 30   # 30 seconds

        LOGGER.info(f"[\033[1m{self.name}\033[0m] initialized.")

    @abstractmethod
    def update(self):
        """update the display content"""
        pass
    
    # @abstractmethod
    def event_listener(self):
        """listen to the metadata"""
        pass

    def is_playing(self):
        """check if the plugin is playing"""
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
    
    def get_image(self):
        """get the current image"""
        return self.image
    
    def clear(self):
        """clear the display"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=0) 