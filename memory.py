import json
from pathlib import Path

MEMORY_FILE = Path("D:/Vanta/memory.json")


def _load_memory() -> dict:
    if not MEMORY_FILE.exists():
        return {}
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_memory_data(data: dict):
    MEMORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def save_memory(key: str, value: str):
    try:
        data = _load_memory()
        data[key.lower().strip()] = value
        _save_memory_data(data)
        return {
            "success": True,
            "message": f"Saved to long-term memory: '{key}' = '{value}'.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def recall_memory(key: str = None):
    try:
        data = _load_memory()
        if key:
            value = data.get(key.lower().strip())
            if value:
                return {"success": True, "key": key, "value": value}
            return {
                "success": False,
                "error": f"No memory found for key: '{key}'.",
            }
        return {"success": True, "all_memories": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def forget_memory(key: str):
    try:
        data = _load_memory()
        key_clean = key.lower().strip()
        if key_clean in data:
            del data[key_clean]
            _save_memory_data(data)
            return {
                "success": True,
                "message": f"Removed '{key}' from memory.",
            }
        return {
            "success": False,
            "error": f"Key '{key}' not found in memory.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}