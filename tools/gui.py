# tools/gui.py
"""
GUI-автоматизация: управление мышью, клавиатурой и окнами.
Использует pyautogui + pygetwindow.
"""
import time
from pathlib import Path

import pyautogui
import pygetwindow as gw

from core.logger import get_logger

logger = get_logger(__name__)

# === БЕЗОПАСНОСТЬ ===
# Если курсор уйдёт в левый верхний угол (0, 0) — все действия прервутся.
# Это аварийный "стоп-кран" от pyautogui.
pyautogui.FAILSAFE = True

# Пауза между действиями (сек), чтобы не спамить
pyautogui.PAUSE = 0.3

# Ограничение длины текста для печати (защита от гигантских вставок)
MAX_TYPE_LENGTH = 2000


# === МЫШЬ ===
def move_mouse(x: int, y: int, duration: float = 0.3):
    """Перемещает курсор в точку (x, y)."""
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return {"success": True, "message": f"Курсор перемещён в ({x}, {y})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def click_mouse(x: int = None, y: int = None, button: str = "left", clicks: int = 1):
    """Клик мышью. Если x/y не указаны — клик в текущей позиции."""
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return {"success": True, "message": f"Клик ({button} x{clicks}) в ({x}, {y})"}
        else:
            pyautogui.click(button=button, clicks=clicks)
            return {"success": True, "message": f"Клик ({button} x{clicks}) в текущей позиции"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def double_click(x: int = None, y: int = None):
    """Двойной клик."""
    return click_mouse(x, y, button="left", clicks=2)


def right_click(x: int = None, y: int = None):
    """Правый клик."""
    return click_mouse(x, y, button="right", clicks=1)


def drag_mouse(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5):
    """Перетаскивание: зажать ЛКМ в (x1, y1), тащить в (x2, y2), отпустить."""
    try:
        pyautogui.moveTo(x1, y1, duration=0.2)
        pyautogui.mouseDown()
        pyautogui.moveTo(x2, y2, duration=duration)
        pyautogui.mouseUp()
        return {"success": True, "message": f"Перетащено из ({x1},{y1}) в ({x2},{y2})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def scroll_mouse(amount: int, x: int = None, y: int = None):
    """Прокрутка колесом. amount > 0 — вверх, < 0 — вниз."""
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
        pyautogui.scroll(amount)
        direction = "вверх" if amount > 0 else "вниз"
        return {"success": True, "message": f"Прокрутка {direction} на {abs(amount)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_mouse_position():
    """Возвращает текущие координаты курсора."""
    try:
        x, y = pyautogui.position()
        return {"success": True, "x": x, "y": y}
    except Exception as e:
        return {"success": False, "error": str(e)}


# === КЛАВИАТУРА ===
def type_text(text: str, interval: float = 0.02):
    """Печатает текст (только ASCII). Русский текст — через clipboard."""
    if len(text) > MAX_TYPE_LENGTH:
        return {
            "success": False,
            "error": f"Текст слишком длинный ({len(text)} символов). Максимум {MAX_TYPE_LENGTH}.",
        }

    try:
        # pyautogui.write не работает с кириллицей — используем clipboard
        if any(ord(c) > 127 for c in text):
            import pyperclip
            old_clipboard = ""
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                pass

            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)

            # Возвращаем буфер обратно
            try:
                if old_clipboard:
                    pyperclip.copy(old_clipboard)
            except Exception:
                pass
        else:
            pyautogui.write(text, interval=interval)

        return {"success": True, "message": f"Напечатано: {text[:50]}..."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def press_key(key: str):
    """Нажимает одну клавишу: 'enter', 'esc', 'tab', 'f5' и т.д."""
    try:
        pyautogui.press(key)
        return {"success": True, "message": f"Нажата клавиша: {key}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def hotkey(keys: str):
    """Нажимает комбинацию клавиш. Пример: 'ctrl+c', 'alt+tab', 'win+d'."""
    try:
        combo = [k.strip().lower() for k in keys.split("+")]
        pyautogui.hotkey(*combo)
        return {"success": True, "message": f"Нажата комбинация: {'+'.join(combo)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# === ОКНА ===
def list_windows():
    """Список открытых окон."""
    try:
        windows = gw.getAllTitles()
        # Убираем пустые
        windows = [w for w in windows if w and w.strip()]
        return {"success": True, "windows": windows}
    except Exception as e:
        return {"success": False, "error": str(e)}


def activate_window(title: str):
    """Активирует окно по (части) заголовка."""
    try:
        matches = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
        if not matches:
            return {"success": False, "error": f"Окно '{title}' не найдено."}

        win = matches[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.3)
        return {"success": True, "message": f"Активировано окно: {win.title}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# === ПОИСК КАРТИНОК НА ЭКРАНЕ ===
def find_on_screen(image_path: str, confidence: float = 0.8):
    """
    Ищет изображение на экране.
    image_path — путь к PNG-файлу.
    confidence — точность совпадения (0.0-1.0).
    """
    try:
        from pathlib import Path as P
        if not P(image_path).exists():
            return {"success": False, "error": f"Файл не найден: {image_path}"}

        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if not location:
            return {
                "success": False,
                "error": f"Изображение не найдено на экране (confidence={confidence})."
            }

        center = pyautogui.center(location)
        return {
            "success": True,
            "x": center.x,
            "y": center.y,
            "left": location.left,
            "top": location.top,
            "width": location.width,
            "height": location.height,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def click_on_image(image_path: str, confidence: float = 0.8):
    """Ищет изображение на экране и кликает по нему."""
    result = find_on_screen(image_path, confidence)
    if not result.get("success"):
        return result

    try:
        pyautogui.click(result["x"], result["y"])
        return {
            "success": True,
            "message": f"Кликнул по изображению в ({result['x']}, {result['y']})"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# === АВАРИЙНАЯ ОСТАНОВКА ===
def emergency_stop():
    """Аварийная остановка — отключает FAILSAFE (полезно для тестов)."""
    pyautogui.FAILSAFE = False
    return {"success": True, "message": "Аварийный режим включён. Действия не прерываются."}