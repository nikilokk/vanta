# tools/web_apps.py
"""
Специализированные функции для открытия популярных сайтов в браузере.
Работают через webbrowser.open — быстро, без слепых кликов и лишних скриншотов.
"""
import os
import urllib.parse
import webbrowser

from core.logger import get_logger
from core.settings import get_setting

logger = get_logger(__name__)


def _open_url(url: str) -> bool:
    try:
        if webbrowser.open(url, new=2, autoraise=True):
            return True
    except Exception as e:
        logger.error(f"webbrowser.open failed: {e}")

    try:
        if hasattr(os, "startfile"):
            os.startfile(url)
            return True
    except Exception as e2:
        logger.error(f"os.startfile failed: {e2}")
    return False


def google_search(query: str, open_first: bool = False):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт поиск Google: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def youtube_search(query: str, open_first: bool = False):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт поиск YouTube: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def wikipedia_search(query: str):
    lang = get_setting("lang", "ru")
    wiki_lang = lang if lang in ("ru", "en", "uk", "pl") else "ru"
    q = urllib.parse.quote_plus(query)
    url = f"https://{wiki_lang}.wikipedia.org/wiki/Special:Search?search={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыта Wikipedia ({wiki_lang}): '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def github_search(query: str, search_type: str = "repositories"):
    q = urllib.parse.quote_plus(query)
    url = f"https://github.com/search?q={q}&type={search_type}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт GitHub: '{query}' ({search_type})", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def stackoverflow_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://stackoverflow.com/search?q={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт Stack Overflow: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def reddit_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.reddit.com/search/?q={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт Reddit: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def maps_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/maps/search/{q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыты Google Maps: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def translate_text(text: str, to_lang: str = "en"):
    q = urllib.parse.quote_plus(text)
    url = f"https://translate.google.com/?sl=auto&tl={to_lang}&text={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт Google Translate ('{to_lang}')", "url": url}
    return {"success": False, "error": "Не удалось открыть браузер."}


def discord_open(channel_name: str = None):
    url = "https://discord.com/channels/@me"
    if _open_url(url):
        return {"success": True, "message": "Discord открыт в браузере.", "url": url}
    return {"success": False, "error": "Не удалось открыть Discord."}


def discord_send(message: str, channel_name: str = None):
    return {
        "success": False,
        "error": "Автоматическая отправка в Discord отключена из соображений безопасности. Используй discord_open.",
    }


def spotify_play(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://open.spotify.com/search/{q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт Spotify: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть Spotify."}


def twitch_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.twitch.tv/search?term={q}"
    if _open_url(url):
        return {"success": True, "message": f"Открыт Twitch: '{query}'", "url": url}
    return {"success": False, "error": "Не удалось открыть Twitch."}