# core/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import DATA_DIR

LOG_FILE = DATA_DIR / "vanta.log"

_initialized = False


def setup_logging(level=logging.INFO):
    """Настраивает корневой логгер: файл + консоль."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файл с ротацией: 5 МБ × 3 бэкапа
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Консоль: только WARNING+, чтобы не спамить в CLI
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)
    root.addHandler(console)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)