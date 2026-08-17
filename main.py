import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from brain import ask_ai
from voice_input import listen_and_transcribe

console = Console()


def main():
    console.print(
        Panel.fit(
            "[bold cyan]Vanta AI Assistant[/bold cyan]\n"
            "[dim]Status: Online & Ready[/dim]\n"
            "[yellow]Type text or enter 'v'/'voice' for Voice Input[/yellow]",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting...[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "выход"}:
            console.print("[dim]Goodbye![/dim]")
            break

        # Режим голосового ввода
        if user_input.lower() in {"v", "voice", "голос"}:
            recognized_text = listen_and_transcribe()

            if not recognized_text:
                console.print(
                    "[yellow]No speech detected or understood. Try again.[/yellow]"
                )
                continue

            console.print(f"[bold cyan]You (Voice):[/bold cyan] {recognized_text}")
            user_input = recognized_text

        # Обработка команды нейросетью
        with console.status(
            "[bold yellow]Vanta is thinking...[/bold yellow]", spinner="dots"
        ):
            response = ask_ai(user_input)

        console.print(
            Panel(
                response,
                title="[bold magenta]Vanta[/bold magenta]",
                title_align="left",
                border_style="magenta",
                padding=(1, 2),
            )
        )


if __name__ == "__main__":
    main()