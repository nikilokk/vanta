# tools/web.py
import subprocess
from datetime import datetime
from ddgs import DDGS


# tools/web.py
def web_search(query: str, max_results: int = 5):
    """Поиск в DuckDuckGo с обработкой ошибок."""
    actual_limit = max(max_results, 5)
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
        # DDGS кидает исключение, когда ничего не нашёл
        return {
            "success": False,
            "results": [],
            "error": f"Поиск не дал результатов: {e}",
            "note": "Попробуй другой, более простой запрос без года и лишних слов."
        }

    if not results:
        return {
            "success": True,
            "results": [],
            "note": "Ничего не найдено. Попробуй другой запрос."
        }

    return {"success": True, "results": results}


def search_username_osint(username: str):
    """Поиск ника через Sherlock."""
    if not username:
        return {"success": False, "error": "Никнейм не указан."}

    try:
        cmd = [
            "sherlock", username,
            "--timeout", "5",
            "--print-found", "--no-color",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

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
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
    }