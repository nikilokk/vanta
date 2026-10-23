# tools/web.py
import subprocess
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS


def web_search(query: str, max_results: int = 5):
    """Поиск в DuckDuckGo с обработкой ошибок."""
    actual_limit = max(1, min(max_results, 15))
    results = []

    try:
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=actual_limit):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("href"),
                    "snippet": result.get("body"),
                })
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "error": f"Поиск не дал результатов: {e}",
            "note": "Попробуй более простой запрос без лишних слов.",
        }

    if not results:
        return {
            "success": True,
            "results": [],
            "note": "Ничего не найдено. Попробуй другой запрос.",
        }

    return {"success": True, "results": results}


def fetch_webpage(url: str, max_chars: int = 8000):
    """Скачивает веб-страницу и извлекает чистый текст для анализа."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return {"success": False, "error": "Разрешены только http:// и https:// ссылки."}

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())

        return {
            "success": True,
            "url": str(resp.url),
            "title": title,
            "content": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    except Exception as e:
        return {"success": False, "error": f"Не удалось загрузить страницу: {e}"}


def search_username_osint(username: str):
    """Поиск ника через Sherlock."""
    if not username or not username.strip():
        return {"success": False, "error": "Никнейм не указан."}

    try:
        cmd = [
            "sherlock", username.strip(),
            "--timeout", "5",
            "--print-found", "--no-color",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=False)

        lines = result.stdout.splitlines()
        found_links = [
            line.strip().replace("[+] ", "")
            for line in lines
            if line.startswith("[+]") or "http" in line
        ]

        return {
            "success": True,
            "username": username,
            "total_found": len(found_links),
            "links": found_links,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Превышено время ожидания (120 сек)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_current_datetime():
    """Текущая дата/время."""
    now = datetime.now()
    return {
        "success": True,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
    }