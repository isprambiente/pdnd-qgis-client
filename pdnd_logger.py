import os
from .vendor.pdnd_client.config import Config

LOG_FILE = os.path.join(os.path.dirname(__file__), "pdnd.log")

def log_info(msg, json_path="", config=None):
    if config is None and json_path != "":
        config = Config(json_path)
    if config is not None and config.get("debug", False):
        print("[PDND][INFO]", msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[INFO] {msg}\n")

def log_error(msg):
    print("[PDND][ERROR]", msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[ERROR] {msg}\n")
