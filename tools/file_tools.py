# tools/file_tools.py
import os
import shlex
import subprocess
from pathlib import Path

from config import VANTA_ROOT, SANDBOX_DIR

ALLOWED_COMMANDS = {"python", "python3", "pytest", "git"}

SENSITIVE_NAMES = {".env", ".env.local", ".git"}
PROTECTED_DIRS = {"core", "tools", "interfaces", "vanta.egg-info", ".venv", "venv"}
PROTECTED_FILES = {"config.py", "requirements.txt", "pyproject.toml"}


def safe_path(path: str, base_dir: Path = VANTA_ROOT, allow_write: bool = False) -> Path:
    """
    Преобразует путь в абсолютный, проверяет отсутствие выхода за пределы base_dir,
    защищает секреты (.env) и исходный код Vanta от перезаписи.
    """
    raw_path = Path(path)
    target = (base_dir / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

    in_base = target.is_relative_to(base_dir.resolve())
    in_sandbox = target.is_relative_to(SANDBOX_DIR.resolve())

    if not (in_base or in_sandbox):
        raise PermissionError(f"Access denied: path '{path}' is outside allowed directories.")

    for part in target.parts:
        if part.lower() in SENSITIVE_NAMES or part.lower().endswith(".env"):
            raise PermissionError("Access denied: access to secret/configuration files is forbidden.")

    if allow_write and in_base and not in_sandbox:
        allow_self_modify = os.getenv("ALLOW_SELF_MODIFY", "0") == "1"
        if not allow_self_modify:
            rel = target.relative_to(VANTA_ROOT.resolve())
            top_part = rel.parts[0] if rel.parts else ""
            if top_part in PROTECTED_DIRS or rel.name in PROTECTED_FILES:
                raise PermissionError(
                    f"Access denied: modifying Vanta source code ('{rel}') is blocked for safety. "
                    f"Use sandbox directory for writing files."
                )

    return target


def run_command(command: str):
    """Запускает разрешённую команду без shell-инъекций."""
    FORBIDDEN_CHARS = ["&", "|", ";", ">", "<", "`", "\n", "\r", "$"]
    if any(char in command for char in FORBIDDEN_CHARS):
        return {
            "success": False,
            "error": "Запрещённые спецсимволы оболочки в команде.",
        }

    try:
        command = command.strip()
        if not command:
            return {"success": False, "error": "Command is empty."}

        parts = shlex.split(command, posix=(os.name != "nt"))
        if not parts:
            return {"success": False, "error": "Command is empty."}

        executable = Path(parts[0]).stem.lower()
        if executable not in ALLOWED_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{executable}' is not allowed. Allowed: {sorted(ALLOWED_COMMANDS)}",
            }

        if executable in {"python", "python3"}:
            if any(arg in {"-c", "-m", "-"} for arg in parts[1:]):
                return {
                    "success": False,
                    "error": "Flags '-c' and '-m' are forbidden in run_command for security reasons.",
                }

        if executable == "git":
            allowed_git_subcommands = {"status", "log", "diff", "branch", "show"}
            if len(parts) > 1 and parts[1] not in allowed_git_subcommands:
                return {
                    "success": False,
                    "error": f"Only read-only git commands are allowed: {sorted(allowed_git_subcommands)}",
                }

        result = subprocess.run(
            parts,
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
        return {"success": False, "error": f"Executable '{parts[0]}' not found."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_files(query: str):
    """Ищет файлы по имени внутри VANTA_ROOT (исключая .git и .venv)."""
    query = query.lower().strip()
    results = []
    ignored_dirs = {".git", ".venv", "venv", "__pycache__", "chroma_db"}

    for path in VANTA_ROOT.rglob("*"):
        if any(part in ignored_dirs for part in path.parts):
            continue
        if not path.is_file() or path.name.lower() in SENSITIVE_NAMES:
            continue
        if query in path.name.lower():
            results.append(str(path.relative_to(VANTA_ROOT)))
            if len(results) >= 50:
                break

    return {"success": True, "results": results}


def read_file(path: str):
    """Читает файл внутри VANTA_ROOT или SANDBOX_DIR."""
    try:
        target = safe_path(path, base_dir=VANTA_ROOT, allow_write=False)

        if not target.exists():
            return {"success": False, "error": f"File '{path}' does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"'{path}' is not a file."}

        content = target.read_text(encoding="utf-8")
        return {
            "success": True,
            "path": str(target),
            "content": content[:50000],
        }
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except UnicodeDecodeError:
        return {"success": False, "error": "File is not valid UTF-8 text."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str):
    """Записывает файл (защищено от перезаписи системного кода Vanta)."""
    try:
        target = safe_path(path, base_dir=VANTA_ROOT, allow_write=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "path": str(target),
            "message": "File written successfully.",
        }
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def edit_file(path: str, old_text: str, new_text: str):
    """Точечно редактирует файл (защищено от перезаписи системного кода Vanta)."""
    try:
        target = safe_path(path, base_dir=VANTA_ROOT, allow_write=True)

        if not target.exists():
            return {"success": False, "error": f"File '{path}' does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"'{path}' is not a file."}

        content = target.read_text(encoding="utf-8")

        if old_text not in content:
            return {
                "success": False,
                "error": "The specified old_text was not found in the file.",
            }

        occurrences = content.count(old_text)
        if occurrences > 1:
            return {
                "success": False,
                "error": f"Text appears {occurrences} times. Make old_text more specific.",
            }

        if old_text == new_text:
            return {"success": False, "error": "old_text and new_text are identical."}

        new_content = content.replace(old_text, new_text, 1)
        target.write_text(new_content, encoding="utf-8")
        return {
            "success": True,
            "path": str(target),
            "message": "File edited successfully.",
            "changes": 1,
        }
    except PermissionError as e:
        return {"success": False, "error": f"Permission denied: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}