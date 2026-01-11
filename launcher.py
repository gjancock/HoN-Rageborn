import requests
import subprocess
import sys
import os
from packaging import version
import configparser

CONFIG_FILE = "config.ini"
CONFIG_SECTION = "settings"
CONFIG_KEY = "auto_update"

REPO = "gjancock/HoN-Rageborn"
APP_EXE = "RagebornApp.exe"
TEMP_EXE = "Rageborn.new.exe"
VERSION_FILE = "VERSION"

API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"


def auto_update_enabled():
    config = configparser.ConfigParser()

    try:
        config.read(CONFIG_FILE, encoding="utf-8")

        if config.has_section(CONFIG_SECTION) and config.has_option(CONFIG_SECTION, CONFIG_KEY):
            return config.getboolean(CONFIG_SECTION, CONFIG_KEY)

    except Exception:
        pass

    # Safe default: auto-update ON
    return True


def read_local_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"


def get_latest_release():
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    remote_version = data["tag_name"].lstrip("v")
    download_url = None

    for asset in data["assets"]:
        if asset["name"] == APP_EXE:
            download_url = asset["browser_download_url"]

    if not download_url:
        raise RuntimeError(f"{APP_EXE} not found in release assets")

    return remote_version, download_url


def download(url, dest):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)


def main():
    local = read_local_version()

    try:
        if auto_update_enabled():
            remote, url = get_latest_release()

            if version.parse(remote) > version.parse(local):
                download(url, TEMP_EXE)
                if os.path.exists(APP_EXE):
                    os.replace(TEMP_EXE, APP_EXE)
                else:
                    os.rename(TEMP_EXE, APP_EXE)

                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(remote)
        else:
            print("Auto-update disabled by user")

    except Exception as e:
        print("Update skipped:", e)

    subprocess.Popen([APP_EXE], close_fds=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
