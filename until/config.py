import json
from pathlib import Path
from until.log import LOGGER

class config:
    def open(path):
        """open the config file"""
        config_path = Path(path)
        if not config_path.exists():
            LOGGER.error(f"can't find config file: {path}")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                LOGGER.info(f"loading config file: \033[2m{path}\033[0m")
                return json.load(f)
        except Exception:
            LOGGER.error(f"can't load config file: \033[2m{path}\033[0m")
            return {}
        
    def save(path, data):
        """save the config file"""
        config_path = Path(path)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                LOGGER.info(f"saved config file: \033[2m{path}\033[0m")
            
        except Exception:
            LOGGER.error(f"can't save config file: \033[2m{path}\033[0m")
