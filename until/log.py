import logging

LOG_FORMAT = logging.Formatter(
    "%(asctime)-15s %(levelname)-3s \033[36m%(module)s\033[0m -- %(message)s"
)

LOGGER = logging.getLogger("MuspiDisplay")
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(CONSOLE_HANDLER)
LOGGER.setLevel(logging.INFO)