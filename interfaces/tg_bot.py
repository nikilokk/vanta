# interfaces/tg_bot.py
import asyncio
import threading
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

from config import TELEGRAM_TOKEN, ALLOWED_USER_ID
from core.agents import list_agents
from core.logger import get_logger

logger = get_logger(__name__)

_bot_app = None
_bot_loop = None
_tg_current_agent = "default"


def _check_access(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER_ID


async def send_telegram_notification(text: str):
    if not _bot_app or not ALLOWED_USER_ID:
        logger.warning("TG: невозможно отправить — бот не запущен")
        return
    try:
        await _bot_app.bot.send_message(chat_id=ALLOWED_USER_ID, text=text)
    except Exception as e:
        logger.error(f"TG send error: {e}")


def send_telegram_notification_sync(text: str):
    if not _bot_loop or not _bot_app:
        logger.warning("TG: loop бота недоступен")
        return
    try:
        future = asyncio.run_coroutine_threadsafe(
            send_telegram_notification(text),
            _bot_loop,
        )
        future.result(timeout=10)
    except Exception as e:
        logger.error(f"TG sync send error: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    await update.message.reply_text(
        "👋 Привет! Я Vanta.\n\n"
        "Отправь мне вопрос или команду, и я обработаю.\n"
        "Список команд: /help"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    await update.message.reply_text(
        "📋 *Доступные команды:*\n\n"
        "/start — приветствие\n"
        "/agent — переключение профиля агента\n"
        "/clear — очистить контекст диалога\n"
        "/memory — показать память\n"
        "/jobs — список фоновых задач\n"
        "/status — состояние системы",
        parse_mode="Markdown"
    )


async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    global _tg_current_agent

    args = context.args
    agents = list_agents()

    if not args:
        lines = [f"🤖 *Текущий агент:* `{_tg_current_agent}`\n\n*Доступные агенты:*"]
        for a in agents:
            tools_info = "all" if "*" in a.allowed_tools else f"{len(a.allowed_tools)} tools"
            lines.append(f"• `{a.id}` — {a.name} ({tools_info})")
        lines.append("\n_Переключить:_ `/agent <id>`")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    target_id = args[0].lower().strip()
    if any(a.id == target_id for a in agents):
        _tg_current_agent = target_id
        await update.message.reply_text(f"✔ Агент переключен на: `{target_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Агент `{target_id}` не найден.")


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    from core.brain import clear_chat_history
    clear_chat_history()
    logger.info("TG: контекст очищен через Telegram")
    await update.message.reply_text("🧹 Контекст диалога очищен.")


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    from core.memory import recall_memory
    from core.vector_memory import get_stats

    result = recall_memory()
    memories = result.get("all_memories", {}) if result.get("success") else {}

    stats = get_stats()
    vec_count = stats.get("total_conversations", 0) if stats.get("success") else 0

    lines = []
    if memories:
        lines.append("🧠 *Факты:*\n")
        for key, value in memories.items():
            lines.append(f"• *{key}*: {value}")
    else:
        lines.append("🧠 *Факты:* пока пусто")

    lines.append(f"\n💬 *Векторная память:* {vec_count} диалогов сохранено")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    from core.scheduler import _load_jobs

    jobs = _load_jobs()
    if not jobs:
        await update.message.reply_text("📭 Нет активных задач.")
        return

    lines = ["⏰ *Активные задачи:*\n"]
    for job in jobs:
        lines.append(
            f"• *{job.get('name', 'task')}* (ID: `{job.get('id')}`)\n"
            f"  каждые {job.get('minutes')} мин."
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        return
    try:
        from tools.system import get_system_info
        info = get_system_info()
        ram = info.get("ram", {})
        text = (
            f"💻 *Система:*\n"
            f"• OS: {info.get('os', '?')}\n"
            f"• CPU: {info.get('cpu_usage_percent', '?')}%\n"
            f"• RAM: {ram.get('used_gb')}/{ram.get('total_gb')} GB "
            f"({ram.get('usage_percent')}%)"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"TG status error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _check_access(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    user_text = update.message.text
    status_msg = await update.message.reply_text(f"🧠 [{_tg_current_agent}] Думаю...")

    try:
        from core.brain import ask_ai
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: ask_ai(user_text, agent_id=_tg_current_agent),
        )

        response_text = result["display"] if isinstance(result, dict) else str(result)

        if len(response_text) > 4000:
            response_text = response_text[:4000] + "\n\n... _(обрезано)_"

        try:
            await status_msg.edit_text(response_text, parse_mode="Markdown")
        except Exception:
            await status_msg.edit_text(response_text)
    except Exception as e:
        logger.error(f"TG handle error: {e}")
        await status_msg.edit_text(f"❌ Ошибка: {e}")


def _run_bot():
    global _bot_app, _bot_loop

    if (
        not TELEGRAM_TOKEN
        or TELEGRAM_TOKEN in ("disabled", "none", "")
        or TELEGRAM_TOKEN.startswith("твой_")
    ):
        logger.warning("TG: токен не задан — бот не запущен")
        return

    try:
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)

        app = Application.builder().token(TELEGRAM_TOKEN).build()
        _bot_app = app

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("agent", cmd_agent))
        app.add_handler(CommandHandler("clear", cmd_clear))
        app.add_handler(CommandHandler("memory", cmd_memory))
        app.add_handler(CommandHandler("jobs", cmd_jobs))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        logger.info("TG: бот запущен и ждёт сообщений")
        app.run_polling(
            stop_signals=None,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )
    except Exception as e:
        logger.error(f"TG launch error: {e}")


def start_telegram_bot():
    thread = threading.Thread(target=_run_bot, daemon=True, name="tg-bot")
    thread.start()
    logger.info("TG: поток бота запущен")


def run_telegram_bot():
    _run_bot()


if __name__ == "__main__":
    from core.logger import setup_logging
    setup_logging()
    _run_bot()