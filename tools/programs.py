# tools/programs.py
import os
import subprocess
from pathlib import Path


PROGRAM_ALIASES = {
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "code": "visual studio code",
    "discord": "discord",
    "steam": "steam",
    "firefox": "firefox",
    "chrome": "google chrome",
}


def _find_program(program: str):
    """Внутренняя функция: ищет путь к программе."""
    program = program.lower().strip()
    search_name = PROGRAM_ALIASES.get(program, program)

    search_locations = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]

    for location in search_locations:
        if not location.exists():
            continue
        for path in location.rglob("*"):
            if not path.is_file():
                continue
            if search_name in path.stem.lower():
                return str(path)

    # Fallback: where
    result = subprocess.run(
        ["where", search_name],
        capture_output=True, text=True, shell=True
    )
    if result.returncode == 0:
        return result.stdout.strip().splitlines()[0]

    return None


def open_program(program: str):
    """Ищет и запускает программу (или открывает файл/URL)."""
    # Если это URL — просто открываем
    if program.startswith(("http://", "https://")):
        try:
            os.startfile(program)
            return {"success": True, "message": f"Opened URL: {program}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Пытаемся найти в Start Menu / where
    path = _find_program(program)

    try:
        if path:
            os.startfile(path)
            return {
                "success": True,
                "program": program,
                "path": path,
                "message": f"Launched {program}"
            }
        else:
            # Пробуем запустить напрямую (вдруг это команда в PATH)
            os.startfile(program)
            return {"success": True, "message": f"Opened {program}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to open '{program}': {e}"}


def open_website(url: str):
    """Открывает сайт в браузере по умолчанию."""
    try:
        os.startfile(url)
        return {"success": True, "message": f"Opened {url}"}
    except Exception as e:
        return {"success": False, "error": str(e)}