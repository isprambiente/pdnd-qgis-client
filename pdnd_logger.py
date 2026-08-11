import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "pdnd.log")

def log_info(msg):
    print("[PDND][INFO]", msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[INFO] {msg}\n")

def log_error(msg):
    print("[PDND][ERROR]", msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[ERROR] {msg}\n")
