"""TUI Menu components."""
from __future__ import annotations

from typing import Callable, List, Optional
from rich.console import Console
from rich.table import Table


class MenuItem:
    """Represents a menu item."""

    def __init__(
        self,
        key: str,
        label: str,
        action: Optional[Callable] = None,
        description: str = "",
    ):
        """Initialize menu item.
        
        Args:
            key: Menu item key/shortcut.
            label: Display label.
            action: Callback function when selected.
            description: Optional description text.
        """
        self.key = key
        self.label = label
        self.action = action
        self.description = description

    def execute(self) -> None:
        """Execute the menu item action."""
        if self.action:
            self.action()


class MainMenu:
    """Main application menu."""

    def __init__(self):
        """Initialize main menu."""
        self.console = Console()
        self.items: List[MenuItem] = []
        self._setup_default_items()

    def _setup_default_items(self) -> None:
        """Setup default menu items."""
        self.items = [
            MenuItem("1", "Dashboard", description="View system dashboard"),
            MenuItem("2", "Items", description="Manage pension items"),
            MenuItem("3", "Users", description="User management"),
            MenuItem("4", "Reports", description="Generate reports"),
            MenuItem("5", "Settings", description="Application settings"),
            MenuItem("0", "Exit", description="Exit application"),
        ]

    def add_item(self, item: MenuItem) -> None:
        """Add a menu item.
        
        Args:
            item: Menu item to add.
        """
        self.items.append(item)

    def remove_item(self, key: str) -> None:
        """Remove a menu item by key.
        
        Args:
            key: Menu item key to remove.
        """
        self.items = [item for item in self.items if item.key != key]

    def display(self) -> None:
        """Display the menu."""
        table = Table(title="Main Menu", show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan", width=6)
        table.add_column("Option", style="green")
        table.add_column("Description", style="white")

        for item in self.items:
            table.add_row(item.key, item.label, item.description)

        self.console.print(table)

    def get_item(self, key: str) -> Optional[MenuItem]:
        """Get menu item by key.
        
        Args:
            key: Menu item key.
            
        Returns:
            MenuItem if found, None otherwise.
        """
        for item in self.items:
            if item.key == key:
                return item
        return None

    def handle_selection(self, key: str) -> bool:
        """Handle user menu selection.
        
        Args:
            key: Selected menu key.
            
        Returns:
            True if should continue, False to exit.
        """
        if key == "0":
            return False

        item = self.get_item(key)
        if item:
            item.execute()
        else:
            self.console.print(f"[yellow]Invalid selection: {key}[/yellow]")

        return True
