# tools/web_apps.py
"""
Специализированные функции для популярных сайтов.
Работают через webbrowser.open — надёжно, без зависимости от фокуса.
"""
import os
import time
import urllib.parse
import webbrowser

from core.logger import get_logger
from tools.system import get_screen_size, take_screenshot

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ
# ═══════════════════════════════════════════════════════════════

def _open_url(url: str, wait: float = 3.0):
    """
    Открывает URL в браузере по умолчанию.
    НЕ требует, чтобы браузер был уже открыт.
    """
    try:
        webbrowser.open(url, new=2, autoraise=True)
    except Exception as e:
        logger.error(f"webbrowser.open failed: {e}")
        try:
            os.startfile(url)
        except Exception as e2:
            logger.error(f"os.startfile failed: {e2}")
            return
    time.sleep(wait)


def _click_at_percent(x_pct: float, y_pct: float, pause: float = 0.5):
    """Клик по координатам, заданным в процентах от размера экрана."""
    try:
        import pyautogui
        size = get_screen_size()
        if not size.get("success"):
            return
        x = int(size["width"] * x_pct)
        y = int(size["height"] * y_pct)
        pyautogui.click(x, y)
        time.sleep(pause)
    except Exception as e:
        logger.error(f"click failed: {e}")


# ═══════════════════════════════════════════════════════════════
# ПОИСКОВИКИ
# ═══════════════════════════════════════════════════════════════

def google_search(query: str, open_first: bool = False):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://www.google.com/search?q={q}", wait=3)
        if open_first:
            _click_at_percent(0.20, 0.42, pause=2.5)
        shot = take_screenshot()
        return {
            "success": True,
            "message": f"Google: '{query}'",
            "image_path": shot.get("image_path"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def youtube_search(query: str, open_first: bool = True):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://www.youtube.com/results?search_query={q}", wait=4)

        if open_first:
            # Клик по первому видео — координаты в % от экрана
            _click_at_percent(0.25, 0.40, pause=4)

        shot = take_screenshot()
        msg = f"YouTube: '{query}'"
        if open_first:
            msg += " — видео должно быть открыто"
        return {"success": True, "message": msg, "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def wikipedia_search(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://ru.wikipedia.org/wiki/Special:Search?search={q}", wait=3)
        shot = take_screenshot()
        return {"success": True, "message": f"Wikipedia: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def github_search(query: str, search_type: str = "repositories"):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://github.com/search?q={q}&type={search_type}", wait=3)
        shot = take_screenshot()
        return {"success": True, "message": f"GitHub: '{query}' ({search_type})", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stackoverflow_search(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://stackoverflow.com/search?q={q}", wait=3)
        shot = take_screenshot()
        return {"success": True, "message": f"Stack Overflow: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def reddit_search(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://www.reddit.com/search/?q={q}", wait=3)
        shot = take_screenshot()
        return {"success": True, "message": f"Reddit: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def maps_search(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://www.google.com/maps/search/{q}", wait=4)
        shot = take_screenshot()
        return {"success": True, "message": f"Google Maps: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def translate_text(text: str, to_lang: str = "en"):
    try:
        q = urllib.parse.quote_plus(text)
        _open_url(f"https://translate.google.com/?sl=auto&tl={to_lang}&text={q}", wait=3)
        shot = take_screenshot()
        return {"success": True, "message": f"Перевод на '{to_lang}': {text[:40]}...", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# СОЦСЕТИ / МЕССЕНДЖЕРЫ
# ═══════════════════════════════════════════════════════════════

def discord_open(channel_name: str = None):
    try:
        _open_url("https://discord.com/channels/@me", wait=5)

        if channel_name:
            import pyautogui
            pyautogui.hotkey("ctrl", "k")
            time.sleep(0.5)
            import pyperclip
            pyperclip.copy(channel_name)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.8)
            pyautogui.press("enter")
            time.sleep(2)

        shot = take_screenshot()
        msg = "Discord открыт"
        if channel_name:
            msg += f" (канал '{channel_name}')"
        return {"success": True, "message": msg, "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def discord_send(message: str, channel_name: str = None):
    try:
        if channel_name:
            result = discord_open(channel_name)
            if not result.get("success"):
                return result
            time.sleep(1)

        _click_at_percent(0.45, 0.95, pause=0.5)

        import pyperclip
        import pyautogui
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(1)

        shot = take_screenshot()
        return {
            "success": True,
            "message": f"Сообщение отправлено в Discord" + (f" (канал {channel_name})" if channel_name else ""),
            "image_path": shot.get("image_path"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# МЕДИА
# ═══════════════════════════════════════════════════════════════

def spotify_play(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://open.spotify.com/search/{q}", wait=4)
        shot = take_screenshot()
        return {"success": True, "message": f"Spotify: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def twitch_search(query: str):
    try:
        q = urllib.parse.quote_plus(query)
        _open_url(f"https://www.twitch.tv/search?term={q}", wait=4)
        shot = take_screenshot()
        return {"success": True, "message": f"Twitch: '{query}'", "image_path": shot.get("image_path")}
    except Exception as e:
        return {"success": False, "error": str(e)}