import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    active_provider: str = Field(default="chatgpt", description="Active provider (chatgpt or gemini)")
    active_model: str = Field(default="gpt-4o", description="Active model name")
    deep_think: bool = Field(default=False, description="Deep thinking reasoning policy enabled")
    theme: str = Field(default="dark", description="UI theme mode")
    max_history: int = Field(default=50, description="Max conversation context history items")
    debug: bool = Field(default=False, description="Debug mode flag")
    app_dir: str = Field(default_factory=lambda: str(Path.home() / ".antigravitycli"))

    def get_skills_dir(self) -> Path:
        p = Path(self.app_dir) / "skills"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_vault_path(self) -> Path:
        p = Path(self.app_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p / "vault.enc"

    def get_key_path(self) -> Path:
        p = Path(self.app_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p / "vault.key"


class ConfigManager:
    """
    Manages loading, validating, updating, and saving configuration for Antigravity CLI.
    Supports environment variable overrides and path portability for Ubuntu and Termux.
    """

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.app_dir = Path(config_dir).expanduser().resolve()
        else:
            self.app_dir = Path.home() / ".antigravitycli"
        
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.app_dir / "config.json"
        self.config = self.load_config()

    def load_config(self) -> AppConfig:
        data = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        # Environment variable overrides
        if "ANTIGRAVITY_PROVIDER" in os.environ:
            data["active_provider"] = os.environ["ANTIGRAVITY_PROVIDER"]
        if "ANTIGRAVITY_MODEL" in os.environ:
            data["active_model"] = os.environ["ANTIGRAVITY_MODEL"]
        if "ANTIGRAVITY_DEEPTHINK" in os.environ:
            data["deep_think"] = os.environ["ANTIGRAVITY_DEEPTHINK"].lower() in ("1", "true", "yes")

        data["app_dir"] = str(self.app_dir)
        return AppConfig(**data)

    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config.model_dump(), f, indent=2)

    def update(self, **kwargs) -> AppConfig:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self.save_config()
        return self.config
