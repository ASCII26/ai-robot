import logging
import time
import os
import sys
from PIL import Image, ImageDraw

LOGGER = logging.getLogger(__name__)
# 添加调试信息
current_dir = os.path.dirname(os.path.realpath(__file__))
LOGGER.info(f"working directory: \033[1m\033[37m{current_dir}\033[0m")

# 修改 libdir 路径
libdir = os.path.join(current_dir, "drive")
LOGGER.info(f"driver directory: \033[1m\033[37m{libdir}\033[0m")

if os.path.exists(libdir):
    sys.path.append(libdir)
else:
    LOGGER.error(f"error: driver directory not found: {libdir}")
    sys.exit(1)

from drive import SSD1305

disp = SSD1305.SSD1305()
disp.Init()

# disp.set_contrast(128)
disp.set_screen_rotation(1)

disp.clear()

width = 128
height = 32
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

def welcome():
    try:
        while True:
            draw.rectangle((0, 0, width-1, height-1), outline=255, width=1, fill=0)
            draw.text((width//2-10, height//2-10), "Hello", fill=255)
            disp.getbuffer(image)
            disp.ShowImage()
   
            time.sleep(0.1)
    except KeyboardInterrupt:
        LOGGER.warning("received keyboard interrupt, cleaning up...")
        clean()
    except Exception as e:
        LOGGER.error(f"runtime error: {e}")
        clean()
    finally:
        clean()
    
def clean():
    disp.clear()
    disp.reset()

if __name__ == "__main__":
    welcome()