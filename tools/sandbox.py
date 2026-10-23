# tools/sandbox.py
import os
from config import SANDBOX_DIR
from tools.file_tools import safe_path


def list_sandbox_files():
    """Список файлов в песочнице."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    files_list = []
    for root, _, files in os.walk(SANDBOX_DIR):
        for file in files:
            if not file.endswith((".pyc", ".log")) and "__pycache__" not in root:
                rel_path = os.path.relpath(os.path.join(root, file), SANDBOX_DIR)
                files_list.append(rel_path)
    return {"success": True, "files": files_list}


def read_sandbox_file(relative_path: str):
    """Безопасно читает файл из песочницы."""
    try:
        target = safe_path(relative_path, base_dir=SANDBOX_DIR, allow_write=False)
        if not target.is_relative_to(SANDBOX_DIR.resolve()):
            return {"success": False, "error": "Access denied: path outside sandbox."}
        if not target.exists() or not target.is_file():
            return {"success": False, "error": "Файл не найден."}
        return {"success": True, "content": target.read_text(encoding="utf-8")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_sandbox_file(relative_path: str, content: str):
    """Безопасно пишет файл в песочницу."""
    try:
        target = safe_path(relative_path, base_dir=SANDBOX_DIR, allow_write=True)
        if not target.is_relative_to(SANDBOX_DIR.resolve()):
            return {"success": False, "error": "Access denied: path outside sandbox."}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"success": True, "message": f"Файл {relative_path} обновлён."}
    except Exception as e:
        return {"success": False, "error": str(e)}