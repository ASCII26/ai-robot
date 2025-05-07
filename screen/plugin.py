import json
import importlib
from pathlib import Path
from until.log import LOGGER
from screen.manager import DisplayManager

# 预加载所有插件模块
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
        self.config = self._load_config()
        
    def _load_config(self):
        """加载插件配置文件"""
        config_path = Path("config/plugins.json")
        if not config_path.exists():
            return {"plugins": []}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def load(self):
        """根据配置加载插件"""
        for plugin_info in self.config["plugins"]:
            if not plugin_info["enabled"]:
                continue
                
            try:
                plugin_name = plugin_info["name"].lower()
                if plugin_name not in PLUGIN_MODULES:
                    LOGGER.error(f"Plugin module not found: {plugin_name}")
                    continue
                    
                # 从预加载的模块中获取插件类
                module = PLUGIN_MODULES[plugin_name]
                plugin_class = getattr(module, plugin_info["name"])
                
                # 添加到插件列表
                self.plugin_classes[plugin_info["name"]] = plugin_class
                
                # 设置插件状态
                self.manager.add_plugin(plugin_class, auto_hide=plugin_info["auto_hide"])
                
            except Exception as e:
                LOGGER.error(f"Failed to load plugin {plugin_info['name']}: {e}")
                