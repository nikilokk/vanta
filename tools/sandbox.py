# tools/sandbox.py
import os
from config import SANDBOX_DIR


def list_sandbox_files():
    """Список файлов в песочнице."""
    files_list = []
    for root, _, files in os.walk(SANDBOX_DIR):
        for file in files:
            if not file.endswith((".pyc", ".log")) and "__pycache__" not in root:
                rel_path = os.path.relpath(os.path.join(root, file), SANDBOX_DIR)
                files_list.append(rel_path)
    return {"files": files_list}


def read_sandbox_file(relative_path: str):
    """Читает файл из песочницы."""
    full_path = os.path.join(SANDBOX_DIR, relative_path)
    if not os.path.exists(full_path):
        return {"error": "Файл не найден."}
    with open(full_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


def write_sandbox_file(relative_path: str, content: str):
    """Пишет файл в песочницу."""
    full_path = os.path.join(SANDBOX_DIR, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"success": True, "message": f"Файл {relative_path} обновлён."}