"""TUI configuration management with persistence."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TUIConfig(BaseModel):
    """TUI configuration with persistence support."""

    # Theme settings
    theme: str = Field(default="dark", description="UI theme (dark/light)")
    accent_color: str = Field(default="cyan", description="Accent color")
    
    # Display settings
    show_timestamps: bool = Field(default=True, description="Show timestamps in logs")
    show_line_numbers: bool = Field(default=True, description="Show line numbers")
    max_log_lines: int = Field(default=1000, description="Maximum log lines to display")
    
    # Behavior settings
    auto_refresh: bool = Field(default=True, description="Auto-refresh data")
    refresh_interval: int = Field(default=5, description="Refresh interval in seconds")
    confirm_exit: bool = Field(default=True, description="Confirm before exit")
    
    # LLM settings
    default_llm_provider: str = Field(default="ollama", description="Default LLM provider")
    default_model: str = Field(default="llama3", description="Default model")
    
    # Datasette settings
    datasette_auto_open: bool = Field(default=False, description="Auto-open Datasette in browser")
    datasette_port: int = Field(default=8001, description="Datasette port")
    
    # Keyboard shortcuts (stored as reference)
    shortcuts: Dict[str, str] = Field(
        default_factory=lambda: {
            "quit": "q",
            "help": "?",
            "refresh": "r",
            "menu": "m",
            "back": "b",
            "search": "/",
            "settings": "s",
        }
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "theme": "dark",
                "accent_color": "cyan",
                "default_llm_provider": "ollama",
            }
        }
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Get the configuration file path."""
        config_dir = Path.home() / ".config" / "opengovpension"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "tui_config.json"
    
    @classmethod
    def load(cls) -> "TUIConfig":
        """Load configuration from file or create default."""
        config_path = cls.get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                # If loading fails, return default config
                return cls()
        
        # Create default config
        config = cls()
        config.save()
        return config
    
    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()
        
        try:
            with open(config_path, "w") as f:
                json.dump(self.model_dump(), f, indent=2)
        except Exception as e:
            # Silently fail if we can't save config
            pass
    
    def update(self, **kwargs: Any) -> None:
        """Update configuration and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    def reset(self) -> None:
        """Reset to default configuration."""
        default = TUIConfig()
        for field in self.model_fields:
            setattr(self, field, getattr(default, field))
        self.save()