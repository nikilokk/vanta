# core/usage_tracker.py
"""
Учёт расхода токенов OpenAI API.
Пишет статистику в data/usage.json.
"""
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

from config import DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)

USAGE_FILE = DATA_DIR / "usage.json"
_lock = threading.Lock()

# Цены за 1M токенов (USD)
PRICING = {
    "gpt-5-mini":               {"input": 0.25, "cached": 0.025, "output": 2.00},
    "gpt-5":                    {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5-nano":               {"input": 0.05, "cached": 0.005, "output": 0.40},
    "gpt-4o-mini":              {"input": 0.15, "cached": 0.075, "output": 0.60},
    "gpt-4o":                   {"input": 2.50, "cached": 1.25,  "output": 10.00},
    "text-embedding-3-small":   {"input": 0.02, "cached": 0.02,  "output": 0.00},
    "text-embedding-3-large":   {"input": 0.13, "cached": 0.13,  "output": 0.00},
}
DEFAULT_PRICING = {"input": 0.50, "cached": 0.05, "output": 2.00}
MAX_RECENT = 200


def _default():
    return {
        "version": 1,
        "total": {
            "requests": 0,
            "prompt_tokens": 0,
            "cached_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": 0.0,
        },
        "by_day": {},
        "recent": [],
    }


def _load():
    if not USAGE_FILE.exists():
        return _default()
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("total", _default()["total"])
        data.setdefault("by_day", {})
        data.setdefault("recent", [])
        return data
    except Exception as e:
        logger.error(f"Usage: load failed: {e}")
        return _default()


def _save(data):
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Usage: save failed: {e}")


def _calc_cost(model: str, prompt: int, cached: int, completion: int) -> float:
    pricing = PRICING.get(model, DEFAULT_PRICING)
    fresh = max(0, prompt - cached)
    cost = (
        fresh * pricing["input"] / 1_000_000
        + cached * pricing["cached"] / 1_000_000
        + completion * pricing["output"] / 1_000_000
    )
    return round(cost, 6)


def record_usage(model: str, prompt_tokens: int, cached_tokens: int = 0, completion_tokens: int = 0):
    """Записывает один API-вызов. Возвращает dict с расходом."""
    with _lock:
        cost = _calc_cost(model, prompt_tokens, cached_tokens, completion_tokens)
        data = _load()
        today = datetime.now().strftime("%Y-%m-%d")
        now_iso = datetime.now().isoformat(timespec="seconds")

        # total
        t = data["total"]
        t["requests"] += 1
        t["prompt_tokens"] += prompt_tokens
        t["cached_tokens"] += cached_tokens
        t["completion_tokens"] += completion_tokens
        t["cost_usd"] = round(t["cost_usd"] + cost, 6)

        # by_day
        day = data["by_day"].setdefault(today, {
            "requests": 0, "prompt_tokens": 0, "cached_tokens": 0,
            "completion_tokens": 0, "cost_usd": 0.0,
        })
        day["requests"] += 1
        day["prompt_tokens"] += prompt_tokens
        day["cached_tokens"] += cached_tokens
        day["completion_tokens"] += completion_tokens
        day["cost_usd"] = round(day["cost_usd"] + cost, 6)

        # recent
        data["recent"].append({
            "ts": now_iso,
            "model": model,
            "prompt": prompt_tokens,
            "cached": cached_tokens,
            "completion": completion_tokens,
            "cost": cost,
        })
        data["recent"] = data["recent"][-MAX_RECENT:]

        _save(data)

        return {
            "prompt": prompt_tokens,
            "cached": cached_tokens,
            "completion": completion_tokens,
            "total": prompt_tokens + completion_tokens,
            "cost": cost,
        }


def get_stats():
    """Агрегированная статистика для дашборда."""
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
    today_data = data["by_day"].get(today, {
        "requests": 0, "prompt_tokens": 0, "cached_tokens": 0,
        "completion_tokens": 0, "cost_usd": 0.0,
    })

    # Последние 7 дней для графика
    last_7 = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        entry = data["by_day"].get(d, {"cost_usd": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0})
        last_7.append({
            "date": d,
            "label": d[5:],
            "cost": entry.get("cost_usd", 0),
            "tokens": entry.get("prompt_tokens", 0) + entry.get("completion_tokens", 0),
            "requests": entry.get("requests", 0),
        })

    total = data["total"]
    cache_hit = 0.0
    if total["prompt_tokens"] > 0:
        cache_hit = round(100 * total["cached_tokens"] / total["prompt_tokens"], 1)

    return {
        "total": total,
        "today": today_data,
        "last_7_days": last_7,
        "recent": list(reversed(data["recent"][-30:])),
        "cache_hit_rate": cache_hit,
    }


def get_total_cost():
    return _load()["total"]["cost_usd"]


def reset_usage():
    _save(_default())