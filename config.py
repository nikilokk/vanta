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

# Песочница: по умолчанию D:\Vanta_Sandbox (если диск D: есть) или data/sandbox
_default_sandbox = Path(r"D:\Vanta_Sandbox") if Path("D:\\").exists() else (DATA_DIR / "sandbox")
SANDBOX_DIR = Path(os.getenv("SANDBOX_DIR", str(_default_sandbox))).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# === МОДЕЛИ ===
MAIN_MODEL = os.getenv("MAIN_MODEL", "gpt-5-mini")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o-mini")
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