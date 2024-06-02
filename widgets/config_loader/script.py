#!/usr/bin/env python3
"""
Load the configuration file, eww.json(c)
"""


def notify_send(msg):
    subprocess.run(["notify-send", msg])


import subprocess
import sys
import json
from pathlib import Path
from os import environ


def load_config():
    """
    Load eww.json(c) from ${EWW_CONFIG_DIR}/eww.json(c).
    Priority: eww.jsonc > eww.json
    """
    eww_home = Path(
        environ.get("EWW_CONFIG_DIR", "{}/.config/eww".format(environ.get("HOME")))
    )
    eww_jsonc = eww_home / "eww.jsonc"
    eww_json = eww_home / "eww.json"
    eww_config = None
    if eww_jsonc.exists():
        try:
            import json5
        except ImportError:
            notify_send("EWW error - Please install json5 Python package.'")
            sys.exit(1)
        eww_config = eww_jsonc
    elif eww_json.exists():
        eww_config = eww_json
    else:
        err_msg = "EWW error - No configuration file found.\n"
        err_msg += "Please create a configuration file eww.json(c) at: {}".format(eww_home)
        notify_send(err_msg)


    if eww_config is None:
        print("{}")
    else:
        with open(eww_config, "r") as f:
            eww_config_dict = json5.load(f)
        eww_config_jsons = json.dumps(eww_config_dict)
        eww_config_jsons = eww_config_jsons.replace("\n", "")
        print(eww_config_jsons)


if __name__ == "__main__":
    load_config()
