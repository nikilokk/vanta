# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === ПУТИ ===
BASE_DIR = Path(__file__).resolve().parent
VANTA_ROOT = BASE_DIR
DATA_DIR = BASE_DIR / "data"
LIBS_DIR = BASE_DIR / "libs"

DATA_DIR.mkdir(exist_ok=True)
LIBS_DIR.mkdir(exist_ok=True)

SANDBOX_DIR = Path(r"D:\Vanta_Sandbox")

# === МОДЕЛИ (всё через OpenAI API) ===
MAIN_MODEL = os.getenv("MAIN_MODEL", "gpt-5-mini")          # основной чат
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o-mini")     # анализ скриншотов
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === API ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# === TELEGRAM ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "disabled")
try:
    ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
except (ValueError, TypeError):
    print("⚠️ ALLOWED_USER_ID в .env не число. Поставлено 0.")
    ALLOWED_USER_ID = 0

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "disabled":
    print("⚠️ TELEGRAM_TOKEN не задан — бот отключён.")

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY не задан — Vanta не сможет отвечать!")