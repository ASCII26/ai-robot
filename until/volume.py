import subprocess
import re

from until.log import LOGGER

CARD = "default"
MIN_DB = -115.0
STEP = "1.0dB"

PCM_CONTROLS = []

def detect_pcm_controls():
    global PCM_CONTROLS
    PCM_CONTROLS = []
    try:
        if CARD == "default":
            out = subprocess.check_output(["amixer", "scontrols"]).decode()
        else:
            out = subprocess.check_output(["amixer", "-c", CARD, "scontrols"]).decode()
        
        # find all controllers, including name and index
        controls = re.findall(r"'([^']*)',(\d+)", out)
        
        # filter out controllers containing PCM
        pcm_controls = [f"{name},{index}" for name, index in controls if "PCM" in name]
        LOGGER.info(pcm_controls)

        for control in pcm_controls:
            # check if each PCM controller has Playback limit
            if CARD == "default":
                info = subprocess.check_output(["amixer", "sget", control]).decode()
            else:
                info = subprocess.check_output(["amixer", "-c", CARD, "sget", control]).decode()
            
            if "Limits: Playback" in info:
                PCM_CONTROLS.append(control)
                LOGGER.info(f"find PCM controller: {control}")
    
    except Exception as e:
        LOGGER.error("detect PCM controller failed:", e)

def db_to_volume(db):
    # convert dB value (-100 to 0) to 0-100 volume percentage
    return int((db + 115) * 100 / 100)

def get_current_db(control):
    try:
        if CARD == "default":
            out = subprocess.check_output(["amixer", "get", control]).decode()
        else:
            out = subprocess.check_output(["amixer", "-c", CARD, "get", control]).decode()

        match = re.search(r'\[(\-?\d+\.\d+)dB\]', out)
        if match:
            db = float(match.group(1))
            volume = db_to_volume(db)
            LOGGER.info(f"[{control}] volume: {volume}% ({db}dB)")
            return db
    except Exception as e:
        LOGGER.error("Failed to get dB:", e)
    return None

def adjust_volume(direction):
    # set volume for all detected PCM controllers
    for control in PCM_CONTROLS:
        current_db = get_current_db(control)
        if current_db is None:
            return
        if direction == "down" and current_db <= MIN_DB:
            LOGGER.info(f"🔇 Already at minimum {MIN_DB}dB")
            return
        delta = STEP + "+" if direction == "up" else STEP + "-"

        try:
            if CARD == "default":
                subprocess.run(["amixer", "set", control, delta], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.run(["amixer", "-c", CARD, "set", control, delta], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            LOGGER.error(f"set {control} volume failed:", e)
            
