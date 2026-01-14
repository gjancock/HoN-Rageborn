import configparser
import os
import core.state as state

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "config.ini"
)

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        return

    config.read(CONFIG_FILE)

    state.AUTO_START_ENDLESS = config.getboolean(
        "endless", "auto_start", fallback=False
    )

    state.AUTO_EMAIL_VERIFICATION = config.getboolean(
        "verification", "auto_email", fallback=False
    )

    state.AUTO_MOBILE_VERIFICATION = config.getboolean(
        "verification", "auto_mobile", fallback=False
    )

    state.AUTO_RESTART_DNS = config.getboolean(
        "network", "auto_restart_dns", fallback=False
    )

    state.SLOWER_PC_MODE = config.getboolean(
        "performance", "slower_pc_mode", fallback=False
    )

    state.AUTO_UPDATE = config.getboolean(
        "settings", "auto_update", fallback=True 
    )

    state.GAME_EXECUTABLE = config.get(
        "paths", "game_executable", fallback=""
    )


