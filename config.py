# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# === ПУТИ ===
BASE_DIR = Path(__file__).resolve().parent
VANTA_ROOT = BASE_DIR
DATA_DIR = BASE_DIR / "data"
LIBS_DIR = BASE_DIR / "libs"

# Создаем папки, если их вдруг нет
DATA_DIR.mkdir(exist_ok=True)
LIBS_DIR.mkdir(exist_ok=True)

# Песочница (можешь изменить путь, если она у тебя в другом месте)
SANDBOX_DIR = Path(r"D:\Vanta_Sandbox")

# === МОДЕЛИ ===
MODEL = os.getenv("MODEL", "qwen3:8b")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3-vl:8b")
CODER_MODEL = os.getenv("CODER_MODEL", "qwen2.5-coder:7b")

# === TELEGRAM ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

# Проверка, что токен вообще есть
if not TELEGRAM_TOKEN:
    print("⚠️ ВНИМАНИЕ: TELEGRAM_TOKEN не найден в .env файле!")