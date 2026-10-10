# interfaces/main.py
import sys
import os
from pathlib import Path

# === НАСТРОЙКА ПУТЕЙ ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# === DLL ДЛЯ WINDOWS ===
if sys.platform == "win32":
    libs_path = PROJECT_ROOT / "libs"
    if libs_path.exists():
        os.add_dll_directory(str(libs_path))

# === ЛОГИРОВАНИЕ (до всех остальных импортов) ===
from core.logger import setup_logging, get_logger
setup_logging()

logger = get_logger(__name__)

# === ОСТАЛЬНЫЕ ИМПОРТЫ ===
from core.brain import ask_ai
from core.scheduler import init_scheduler
from interfaces.tg_bot import start_telegram_bot

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]Vanta AI Assistant[/bold cyan]\n"
        "[dim]Status: Online & Ready[/dim]\n"
        "[dim]Type your message or 'exit' to quit[/dim]",
        border_style="cyan",
    ))


def main():
    # Запускаем инфраструктуру
    init_scheduler()
    start_telegram_bot()

    logger.info("Vanta запущена")
    print_banner()

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting...[/dim]")
            logger.info("Vanta остановлена пользователем")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "выход"}:
            console.print("[bold]Goodbye![/bold]")
            logger.info("Vanta остановлена командой exit")
            break

        try:
            with console.status("[bold yellow]Vanta is thinking...[/bold yellow]", spinner="dots"):
                result = ask_ai(user_input)

            md = Markdown(result["display"])
            console.print(Panel(
                md,
                title="[bold magenta]Vanta[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            ))
        except Exception as e:
            logger.error(f"CLI error: {e}")
            console.print(f"[red]❌ Ошибка: {e}[/red]")


if __name__ == "__main__":
    main()