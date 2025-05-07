import importlib
from until.log import LOGGER
from screen.manager import DisplayManager
from until.config import config

# config path
CONFIG_PATH = "config/plugins.json"

# preload all plugin modules
PLUGIN_MODULES = {
    'xiaozhi': importlib.import_module('screen.plugins.xiaozhi'),
    'clock': importlib.import_module('screen.plugins.clock'),
    'dino': importlib.import_module('screen.plugins.dino'),
    'life': importlib.import_module('screen.plugins.life'),
    'airplay': importlib.import_module('screen.plugins.airplay'),
    'roon': importlib.import_module('screen.plugins.roon'),
}

class PluginManager:
    def __init__(self, manager: DisplayManager):
        self.manager = manager
        self.plugin_classes = {}
        self.config = config.open(CONFIG_PATH)
        
            
    def load(self):
        """load plugins according to the config"""
        for plugin_info in self.config["plugins"]:
            if not plugin_info["enabled"]:
                continue
                
            try:
                plugin_name = plugin_info["name"].lower()
                if plugin_name not in PLUGIN_MODULES:
                    LOGGER.error(f"Plugin module not found: {plugin_name}")
                    continue
                    
                # get plugin class from the preloaded module
                module = PLUGIN_MODULES[plugin_name]
                plugin_class = getattr(module, plugin_info["name"])
                
                # add to plugin list
                self.plugin_classes[plugin_info["name"]] = plugin_class
                
                # set plugin status
                self.manager.add_plugin(plugin_class, auto_hide=plugin_info["auto_hide"])
                
            except Exception as e:
                LOGGER.error(f"Failed to load plugin {plugin_info['name']}: {e}")
                