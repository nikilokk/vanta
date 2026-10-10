# tools/file_tools.py
import os
import platform
import subprocess
from pathlib import Path

from config import VANTA_ROOT


# === РАЗРЕШЁННЫЕ КОМАНДЫ ===
ALLOWED_COMMANDS = {
    "python",
    "python3",
    "pip",
    "pip3",
    "pytest",
    "git",
}


def safe_path(path: str) -> Path:
    """Преобразует путь в абсолютный и проверяет, что он внутри VANTA_ROOT."""
    target = Path(path)

    if not target.is_absolute():
        target = VANTA_ROOT / target

    target = target.resolve()

    try:
        target.relative_to(VANTA_ROOT)
    except ValueError:
        raise PermissionError("Access denied: path is outside Vanta project.")

    return target


def run_command(command: str):
    """Запускает разрешённую команду внутри проекта Vanta."""
    FORBIDDEN_CHARS = ["&", "|", ";", ">", "<", "`", "\n"]
    if any(char in command for char in FORBIDDEN_CHARS):
        return {
            "success": False,
            "error": "Символы &, |, ;, >, <, ` запрещены."
        }

    try:
        command = command.strip()
        if not command:
            return {"success": False, "error": "Command is empty."}

        command_parts = command.split()
        executable = command_parts[0].lower()

        # Windows: убираем .exe
        if executable.endswith(".exe"):
            executable = executable[:-4]

        if executable not in ALLOWED_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{executable}' is not allowed."
            }

        if platform.system() == "Windows":
            result = subprocess.run(
                command,
                cwd=VANTA_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True,
            )
        else:
            result = subprocess.run(
                command_parts,
                cwd=VANTA_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
            )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-10000:],
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 30 seconds."}
    except FileNotFoundError:
        return {"success": False, "error": f"Command '{command_parts[0]}' not found."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_files(query: str):
    """Ищет файлы по имени внутри VANTA_ROOT."""
    query = query.lower().strip()
    results = []

    for path in VANTA_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if query in path.name.lower():
            results.append(str(path.relative_to(VANTA_ROOT)))

    return {"success": True, "results": results[:50]}


def read_file(path: str):
    """Читает файл внутри VANTA_ROOT."""
    try:
        target = safe_path(path)

        if not target.exists():
            return {"success": False, "error": f"File '{path}' does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"'{path}' is not a file."}

        content = target.read_text(encoding="utf-8")
        return {
            "success": True,
            "path": str(target.relative_to(VANTA_ROOT)),
            "content": content,
        }
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except UnicodeDecodeError:
        return {"success": False, "error": "File is not valid UTF-8 text."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str):
    """Записывает файл внутри VANTA_ROOT."""
    try:
        target = safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "path": str(target.relative_to(VANTA_ROOT)),
            "message": "File written successfully.",
        }
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def edit_file(path: str, old_text: str, new_text: str):
    """Точечно редактирует файл — заменяет old_text на new_text."""
    try:
        target = safe_path(path)

        if not target.exists():
            return {"success": False, "error": f"File '{path}' does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"'{path}' is not a file."}

        content = target.read_text(encoding="utf-8")

        if old_text not in content:
            return {
                "success": False,
                "error": "The specified old_text was not found in the file."
            }

        occurrences = content.count(old_text)
        if occurrences > 1:
            return {
                "success": False,
                "error": f"Text appears {occurrences} times. Make old_text more specific."
            }

        if old_text == new_text:
            return {"success": False, "error": "old_text and new_text are identical."}

        new_content = content.replace(old_text, new_text, 1)
        if new_content == content:
            return {"success": False, "error": "The file content did not change."}

        target.write_text(new_content, encoding="utf-8")
        return {
            "success": True,
            "path": str(target.relative_to(VANTA_ROOT)),
            "message": "File edited successfully.",
            "changes": 1,
        }
    except PermissionError as e:
        return {"success": False, "error": f"Permission denied: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}