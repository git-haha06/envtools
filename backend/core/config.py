import json
import os

from .database import get_db

DEFAULT_CONFIG = {
    "use_mirror": False,
    "install_dir": os.path.join(os.path.expanduser("~"), ".envtools", "installed"),
    "language": "zh-CN",
    "theme": "system",
}


def get_app_config() -> dict:
    result = dict(DEFAULT_CONFIG)
    with get_db() as db:
        rows = db.execute("SELECT key, value FROM app_config").fetchall()
        for row in rows:
            key, raw = row["key"], row["value"]
            try:
                result[key] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                result[key] = raw
    return result


def save_app_config(config: dict):
    with get_db() as db:
        for key, value in config.items():
            serialized = json.dumps(value) if not isinstance(value, str) else value
            db.execute(
                "INSERT INTO app_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                (key, serialized, serialized),
            )
