import sys
import asyncio
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live

from antigravity_cli import __version__
from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.registry import ModelRegistry
from antigravity_cli.router import CommandRouter, CommandResult
from antigravity_cli.skills.manager import SkillManager
from antigravity_cli.session_validator import SessionValidator
from antigravity_cli.providers.base import ChatMessage
from antigravity_cli.platform import PlatformEnvironment


class AntigravityTUI:
    """
    Terminal User Interface using Rich for Antigravity CLI.
    Runs cleanly on both Ubuntu workstations and Termux constrained terminals.
    """

    def __init__(self, config_manager: ConfigManager, vault_manager: VaultManager):
        self.config = config_manager
        self.vault = vault_manager
        self.registry = ModelRegistry(vault_manager=self.vault)
        self.router = CommandRouter(
            config_manager=self.config,
            vault_manager=self.vault,
            model_registry=self.registry
        )
        self.skills_manager = SkillManager(user_skills_dir=self.config.config.get_skills_dir())
        self.console = Console()
        self.history: List[ChatMessage] = []

    def render_header(self) -> None:
        platform_info = PlatformEnvironment.get_platform_name()
        title = f"[bold cyan]Antigravity CLI[/bold cyan] [dim]v{__version__}[/dim] — [yellow]{platform_info}[/yellow]"
        sub = "[dim]Type prompts directly or use slash commands (/help, /models, /deepthink, /session, /skills)[/dim]"
        panel = Panel(Text.from_markup(f"{title}\n{sub}"), border_style="cyan")
        self.console.print(panel)

    async def render_status_bar(self) -> str:
        cfg = self.config.config
        meta = self.vault.get_session_metadata(cfg.active_provider)
        health_str = meta.validation_status if meta else "UNAUTHENTICATED"
        
        health_color = "green" if (meta and meta.is_valid) else "red"
        think_color = "magenta" if cfg.deep_think else "dim"
        
        ctx = await self.registry.get_context_info(cfg.active_provider, cfg.active_model)
        quota = await self.registry.get_quota_info(cfg.active_provider)

        bar = (
            f"[bold yellow]Provider:[/bold yellow] [white]{cfg.active_provider.upper()}[/white] | "
            f"[bold yellow]Model:[/bold yellow] [white]{cfg.active_model}[/white] | "
            f"[bold yellow]DeepThink:[/bold yellow] [{think_color}]{'ON' if cfg.deep_think else 'OFF'}[/{think_color}] | "
            f"[bold yellow]Context:[/bold yellow] [white]{ctx.used_context:,}/{ctx.max_context:,}[/white] | "
            f"[bold yellow]Quota:[/bold yellow] [white]{quota.status}[/white] | "
            f"[bold yellow]Health:[/bold yellow] [{health_color}]{health_str}[/{health_color}]"
        )
        return bar

    async def display_status_bar(self) -> None:
        bar_text = await self.render_status_bar()
        panel = Panel(Text.from_markup(bar_text), border_style="blue", padding=(0, 1))
        self.console.print(panel)

    async def handle_session_import_interactive(self, provider: str) -> None:
        self.console.print(f"\n[bold yellow]=== Import Session Cookies for {provider.upper()} ===[/bold yellow]")
        self.console.print("[dim]Paste Cookie Header string (e.g. 'key=val; key2=val2') OR JSON cookie export blob:[/dim]")
        
        try:
            raw_input = await asyncio.to_thread(lambda: input("Cookie Data > "))
            raw_input = raw_input.strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print("[red]Import cancelled.[/red]")
            return

        if not raw_input:
            self.console.print("[red]No input provided. Import cancelled.[/red]")
            return

        val_res = SessionValidator.validate_session(provider, raw_input)
        if not val_res.is_valid:
            self.console.print(f"[bold red]Validation Failed:[/bold red] {val_res.error_message}")
            return

        meta = self.vault.save_session(
            provider=provider,
            secret_payload=val_res.normalized_session,
            format_type=val_res.format_type,
            is_valid=True,
            validation_status="VALID"
        )

        self.console.print(f"[bold green]✓ Session successfully imported and encrypted for {provider.upper()}![/bold green]")
        self.console.print(f"[dim]Format: {val_res.format_type} | Cookies parsed: {val_res.normalized_session['cookie_count']}[/dim]")
        
        # Switch active provider to newly imported session & refresh registry adapters
        self.config.update(active_provider=provider)
        self.registry._reload_adapters()

    async def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        if not user_input:
            return True

        if user_input.lower() in ("exit", "quit", "/quit"):
            self.console.print("[yellow]Exiting Antigravity CLI. Goodbye![/yellow]")
            return False

        # Slash commands
        if user_input.startswith("/"):
            if user_input == "/skills" or user_input.startswith("/skills "):
                skills = self.skills_manager.list_skills()
                self.console.print("\n[bold cyan]=== Installed Antigravity Skills ===[/bold cyan]")
                for s in skills:
                    self.console.print(f"• [bold yellow]/{s.command}[/bold yellow] - {s.name} (v{s.version}): {s.description}")
                return True
            elif user_input.startswith("/skill "):
                skill_name = user_input[7:].strip()
                res_text = self.skills_manager.execute_skill_action(skill_name)
                self.console.print(Panel(res_text, border_style="green", title=f"Skill: {skill_name}"))
                return True

            prev_prov = self.config.config.active_provider
            res: CommandResult = await self.router.execute(user_input)
            
            # Reset conversation history if provider changed
            if self.config.config.active_provider != prev_prov:
                self.history.clear()

            if res.data and res.data.get("action") == "import_prompt":
                await self.handle_session_import_interactive(res.data.get("provider", "chatgpt"))
            else:
                border_color = "green" if res.success else "red"
                self.console.print(Panel(res.message, border_style=border_color, title=f"Command: {res.command}"))
            return True

        # Regular Chat Execution
        cfg = self.config.config
        adapter = self.registry.get_adapter(cfg.active_provider)

        # Check authentication health
        health = await adapter.validate_session()
        if not health.is_authenticated:
            self.console.print(f"[bold red]Error:[/bold red] Active provider {cfg.active_provider.upper()} is not authenticated.")
            self.console.print(f"[yellow]Run `/session import {cfg.active_provider}` to provide your session cookies.[/yellow]")
            return True

        self.history.append(ChatMessage(role="user", content=user_input))

        self.console.print(f"\n[bold green]User:[/bold green] {user_input}")
        self.console.print(f"[bold cyan]Assistant ({cfg.active_provider.upper()} / {cfg.active_model}):[/bold cyan] ", end="")

        response_text = ""
        try:
            async for chunk in adapter.stream_chat(
                messages=self.history,
                model=cfg.active_model,
                deep_think=cfg.deep_think
            ):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                response_text += chunk
        except Exception as e:
            error_msg = f"\n[Streaming error: {e}]"
            sys.stdout.write(error_msg)
            sys.stdout.flush()
            response_text += error_msg

        sys.stdout.write("\n\n")
        self.history.append(ChatMessage(role="assistant", content=response_text))
        return True

    async def run_loop(self) -> None:
        self.render_header()
        await self.display_status_bar()

        while True:
            try:
                user_input = await asyncio.to_thread(lambda: input("\nantigravity > "))
                should_continue = await self.process_input(user_input)
                if not should_continue:
                    break
                await self.display_status_bar()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
                break
