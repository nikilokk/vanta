# core/scheduler.py
import json
import os
import asyncio
import uuid
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from rich.console import Console

from config import DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)
console = Console()

scheduler = BackgroundScheduler()
JOBS_FILE = DATA_DIR / "scheduled_jobs.json"


# === РАБОТА С ФАЙЛОМ ЗАДАЧ ===
def _load_jobs():
    """Загружает список задач из JSON."""
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Scheduler: не удалось загрузить задачи: {e}")
        return []


def _save_jobs(jobs):
    """Сохраняет список задач в JSON."""
    try:
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Scheduler: не удалось сохранить задачи: {e}")


# === ВЫПОЛНЕНИЕ ЗАДАЧ ===
async def _execute_scheduled_task_async(task_name, prompt, task_type="ai_task"):
    from interfaces.tg_bot import send_telegram_notification_sync   # <-- SYNC!
    from core.brain import ask_ai

    logger.info(f"Scheduler: сработала задача '{task_name}' ({task_type})")
    console.print(
        f"\n[bold magenta]⏰ [SCHEDULER]:[/bold magenta] [white]{task_name}[/white]"
    )

    if task_type == "notification":
        # Простое напоминание — текст отправляется как есть, без LLM
        response = prompt
    else:
        # AI-задача — спрашиваем модель
        try:
            result = ask_ai(prompt)
            response = result["display"] if isinstance(result, dict) else str(result)
        except Exception as e:
            response = f"Ошибка выполнения задачи: {e}"
            logger.error(f"Scheduler: ошибка при выполнении '{task_name}': {e}")

    console.print(f"[bold magenta]🔔 [VANTA]:[/bold magenta] {response}\n")

    try:
        # Уведомление — теперь синхронное
        send_telegram_notification_sync(f"⏰ **{task_name}**\n\n{response}")
    except Exception as e:
        logger.error(f"Scheduler: TG error: {e}")


def _run_async(coro):
    """Запускает корутину в новом event loop из синхронного контекста."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Scheduler: ошибка выполнения корутины: {e}")
    finally:
        try:
            loop.close()
        except Exception:
            pass


def execute_scheduled_task(
    task_name: str,
    prompt: str,
    task_type: str = "ai_task",
):
    """Синхронная обёртка для APScheduler."""
    _run_async(_execute_scheduled_task_async(task_name, prompt, task_type))


# === УПРАВЛЕНИЕ ЗАДАЧАМИ ===
def add_interval_task(
    name: str,
    minutes: int,
    prompt: str,
    task_type: str = "ai_task",
):
    """Добавляет задачу, повторяющуюся каждые N минут."""
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    scheduler.add_job(
        execute_scheduled_task,
        "interval",
        minutes=minutes,
        id=job_id,
        args=[name, prompt, task_type],
        replace_existing=True,
    )

    jobs = _load_jobs()
    jobs.append({
        "id": job_id,
        "type": "interval",
        "name": name,
        "minutes": minutes,
        "prompt": prompt,
        "task_type": task_type,
    })
    _save_jobs(jobs)

    logger.info(
        f"Scheduler: добавлена задача '{name}' ({job_id}) "
        f"каждые {minutes} мин. Тип: {task_type}"
    )
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Задача '{name}' будет запускаться каждые {minutes} мин.",
    }


def list_scheduled_tasks():
    """Возвращает список задач."""
    return {"success": True, "tasks": _load_jobs()}


def remove_scheduled_task(job_id: str):
    """Удаляет задачу по ID."""
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    jobs = _load_jobs()
    _save_jobs([j for j in jobs if j["id"] != job_id])
    logger.info(f"Scheduler: удалена задача {job_id}")
    return {"success": True, "message": f"Задача {job_id} удалена."}


# === ИНИЦИАЛИЗАЦИЯ ===
def init_scheduler():
    """Запускает планировщик и восстанавливает задачи из файла."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler: запущен")
        console.print("[dim green]✔ Планировщик задач успешно запущен.[/dim green]")

    jobs = _load_jobs()
    restored = 0

    for job in jobs:
        try:
            job_type = job.get("type")

            if job_type == "interval":
                scheduler.add_job(
                    execute_scheduled_task,
                    "interval",
                    minutes=job["minutes"],
                    id=job["id"],
                    args=[
                        job["name"],
                        job["prompt"],
                        job.get("task_type", "ai_task"),
                    ],
                    replace_existing=True,
                )
                restored += 1

            elif job_type == "date":
                run_date = datetime.fromisoformat(job["run_date"])
                if run_date > datetime.now():
                    scheduler.add_job(
                        execute_scheduled_task,
                        "date",
                        run_date=run_date,
                        id=job["id"],
                        args=[
                            job["name"],
                            job["prompt"],
                            job.get("task_type", "ai_task"),
                        ],
                        replace_existing=True,
                    )
                    restored += 1

        except Exception as e:
            logger.error(
                f"Scheduler: ошибка восстановления задачи {job.get('id')}: {e}"
            )

    if restored:
        logger.info(f"Scheduler: восстановлено задач — {restored}")