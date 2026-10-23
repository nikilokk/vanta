# core/settings.py
"""
Глобальные настройки Vanta.
Хранятся в data/settings.json.
"""
import json
from pathlib import Path

from config import DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULTS = {
    "lang": "ru",           # язык интерфейса и ответов
}


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception as e:
        logger.error(f"Settings: load failed: {e}")
        return dict(DEFAULTS)


def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Settings: save failed: {e}")


def get_setting(key: str, default=None):
    return load_settings().get(key, default)


def set_setting(key: str, value):
    data = load_settings()
    data[key] = value
    save_settings(data)