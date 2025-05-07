import sys
import os

from screen.manager import DisplayManager

# add screen plugins
from screen.plugins.clock import ClockDisplay
from screen.plugins.roon import RoonDisplay
from screen.plugins.airplay import AirPlayDisplay
from screen.plugins.dino import DinoGameDisplay
from screen.plugins.life import LifeDisplay
from screen.plugins.xiaozhi import XiaozhiDisplay

# add until plugins
from until.log import LOGGER

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

if __name__ == "__main__":
    # init manager
    manager = DisplayManager()

    # add plugins
    manager.add_plugin(XiaozhiDisplay, auto_hide=False)
    manager.add_plugin(ClockDisplay, auto_hide=False)
    manager.add_plugin(DinoGameDisplay, auto_hide=False)
    manager.add_plugin(LifeDisplay, auto_hide=False)
    manager.add_plugin(AirPlayDisplay, auto_hide=True)
    manager.add_plugin(RoonDisplay, auto_hide=False)

    # run
    manager.run()
