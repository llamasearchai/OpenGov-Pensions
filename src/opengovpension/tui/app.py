"""TUI Application main class."""
from __future__ import annotations

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import TUIConfig


class TUIApp:
    """Terminal User Interface Application for OpenGov-Pension."""

    def __init__(self, config: Optional[TUIConfig] = None):
        """Initialize TUI application.
        
        Args:
            config: TUI configuration. If None, uses default.
        """
        self.config = config or TUIConfig()
        self.console = Console()
        self.running = False

    def run(self) -> None:
        """Run the TUI application main loop."""
        self.running = True
        self._show_welcome()
        
        while self.running:
            try:
                self._show_main_menu()
                choice = self.console.input("\n[bold cyan]Select option:[/bold cyan] ").strip()
                self._handle_menu_choice(choice)
            except KeyboardInterrupt:
                self.running = False
                self.console.print("\n[yellow]Exiting...[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

    def _show_welcome(self) -> None:
        """Display welcome banner."""
        welcome_text = Text()
        welcome_text.append("OpenGov-Pension\n", style="bold magenta")
        welcome_text.append("Pension Management System", style="cyan")
        
        panel = Panel(
            welcome_text,
            title="Welcome",
            border_style="green",
        )
        self.console.print(panel)

    def _show_main_menu(self) -> None:
        """Display main menu options."""
        self.console.print("\n[bold]Main Menu:[/bold]")
        self.console.print("1. Dashboard")
        self.console.print("2. Manage Items")
        self.console.print("3. System Status")
        self.console.print("4. Settings")
        self.console.print("0. Exit")

    def _handle_menu_choice(self, choice: str) -> None:
        """Handle user menu selection.
        
        Args:
            choice: User's menu choice.
        """
        if choice == "0":
            self.running = False
            self.console.print("[green]Goodbye![/green]")
        elif choice == "1":
            self._show_dashboard()
        elif choice == "2":
            self._show_items()
        elif choice == "3":
            self._show_status()
        elif choice == "4":
            self._show_settings()
        else:
            self.console.print("[yellow]Invalid choice. Please try again.[/yellow]")

    def _show_dashboard(self) -> None:
        """Display dashboard view."""
        self.console.print(Panel("Dashboard - Coming Soon", style="cyan"))

    def _show_items(self) -> None:
        """Display items management view."""
        self.console.print(Panel("Items Management - Coming Soon", style="cyan"))

    def _show_status(self) -> None:
        """Display system status view."""
        self.console.print(Panel("System Status - Coming Soon", style="cyan"))

    def _show_settings(self) -> None:
        """Display settings view."""
        self.console.print(Panel("Settings - Coming Soon", style="cyan"))
