from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_response(text: str, title: str = "Assistant"):
    console.print(Panel(Markdown(text), title=f"[bold cyan]{title}[/]", border_style="cyan"))


def print_user(text: str):
    console.print(Panel(Text(text, style="white"), title="[bold green]You[/]", border_style="green"))


def print_error(text: str):
    console.print(f"[bold red]Error:[/] {text}")


def print_info(text: str):
    console.print(f"[dim]{text}[/dim]")
