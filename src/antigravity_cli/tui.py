import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.live import Live

from antigravity_cli import __version__
from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.registry import ModelRegistry
from antigravity_cli.router import CommandRouter, CommandResult
from antigravity_cli.skills.manager import SkillManager
from antigravity_cli.session_validator import SessionValidator
from antigravity_cli.providers.base import ChatMessage, ModelInfo
from antigravity_cli.platform import PlatformEnvironment
from antigravity_cli.workspace import WorkspaceManager, WorkspaceInfo
from antigravity_cli.permissions import PermissionManager, PermissionRequest


class AntigravityTUI:
    """
    Production Terminal User Interface using Rich for Antigravity CLI.
    Supports top banner workspace awareness, bottom status metrics,
    interactive slash command palette, model picker, and permission-gated shell execution.
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
        self.permission_manager = PermissionManager(mode="ask")
        self.console = Console()
        self.history: List[ChatMessage] = self.load_history()

    def load_history(self) -> List[ChatMessage]:
        p = Path(self.config.config.app_dir) / "history.json"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [ChatMessage(**item) for item in data]
            except Exception:
                return []
        return []

    def save_history(self) -> None:
        p = Path(self.config.config.app_dir) / "history.json"
        try:
            max_h = self.config.config.max_history
            recent = self.history[-max_h:] if len(self.history) > max_h else self.history
            with open(p, "w", encoding="utf-8") as f:
                json.dump([m.model_dump() for m in recent], f, indent=2)
        except Exception:
            pass

    def clear_history(self) -> None:
        self.history.clear()
        p = Path(self.config.config.app_dir) / "history.json"
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    def render_header(self) -> None:
        ws: WorkspaceInfo = WorkspaceManager.get_workspace_info()
        platform_info = PlatformEnvironment.get_platform_name()
        cfg = self.config.config
        meta = self.vault.get_session_metadata(cfg.active_provider)

        git_str = f"git:({ws.git_branch})" if ws.is_git_repo and ws.git_branch else "no-git"
        mod_str = f" | +{ws.modified_files_count} modified" if ws.modified_files_count > 0 else ""
        account_str = meta.account_label if meta else "guest"

        title = f"[bold cyan]Antigravity CLI[/bold cyan] [dim]v{__version__}[/dim] — [yellow]{platform_info}[/yellow]"
        meta_info = (
            f"[bold yellow]Account:[/bold yellow] {account_str} | "
            f"[bold yellow]Provider:[/bold yellow] {cfg.active_provider.upper()} | "
            f"[bold yellow]Model:[/bold yellow] {cfg.active_model} | "
            f"[bold yellow]Workspace:[/bold yellow] [cyan]{ws.workspace_name}[/cyan] ({git_str}{mod_str})"
        )
        sub = "[dim]Type prompts directly, run shell commands (!cmd), or use slash commands (/help, /models, /deepthink, /session, /skills, /clear)[/dim]"
        
        panel = Panel(Text.from_markup(f"{title}\n{meta_info}\n{sub}"), border_style="cyan")
        self.console.print(panel)

    async def render_status_bar(self) -> str:
        cfg = self.config.config
        ws: WorkspaceInfo = WorkspaceManager.get_workspace_info()
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
            f"[bold yellow]Perms:[/bold yellow] [white]{self.permission_manager.mode.upper()}[/white] | "
            f"[bold yellow]Health:[/bold yellow] [{health_color}]{health_str}[/{health_color}]"
        )
        return bar

    async def display_status_bar(self) -> None:
        bar_text = await self.render_status_bar()
        panel = Panel(Text.from_markup(bar_text), border_style="blue", padding=(0, 1))
        self.console.print(panel)

    async def show_command_palette(self, search_query: str = "") -> None:
        """
        Searchable interactive slash command palette.
        Displays categorized commands with shortcut indices and descriptions.
        """
        self.console.print("\n[bold cyan]=== Antigravity Slash Command Palette ===[/bold cyan]")
        commands = [
            ("1", "models", "Open keyboard-navigable model & provider picker"),
            ("2", "users", "View sessions, account health, and quota limits"),
            ("3", "context", "View context window usage & remaining token budget"),
            ("4", "deepthink", "Toggle multi-step reasoning policy wrap [on/off]"),
            ("5", "skills", "Browse installed built-in and custom skills"),
            ("6", "session validate", "Validate active session cookies"),
            ("7", "session import <prov>", "Import session cookies (Header or JSON)"),
            ("8", "status", "View system framework status & vault paths"),
            ("9", "clear", "Clear conversation context history"),
            ("0", "help", "Display command palette documentation"),
        ]

        table = Table(show_header=True, header_style="bold yellow", border_style="dim")
        table.add_column("Key", style="bold cyan", width=4)
        table.add_column("Command", style="bold white", width=22)
        table.add_column("Description", style="dim")

        for key, cmd, desc in commands:
            if search_query and search_query not in cmd and search_query not in desc:
                continue
            table.add_row(f"[{key}]", f"/{cmd}", desc)

        self.console.print(table)
        
        try:
            choice = await asyncio.to_thread(lambda: input("\nSelect Command Key [0-9] or press Enter to cancel > "))
            choice = choice.strip()
        except (EOFError, KeyboardInterrupt):
            return

        cmd_map = {
            "1": "/models",
            "2": "/users",
            "3": "/context",
            "4": "/deepthink",
            "5": "/skills",
            "6": "/session validate",
            "7": "/session import chatgpt",
            "8": "/status",
            "9": "/clear",
            "0": "/help"
        }

        if choice in cmd_map:
            await self.process_input(cmd_map[choice])

    async def show_interactive_model_picker(self) -> None:
        prov = self.config.config.active_provider
        models: List[ModelInfo] = await self.registry.get_models_for_provider(prov)
        quota = await self.registry.get_quota_info(prov)
        active_model = self.config.config.active_model

        self.console.print(f"\n[bold cyan]=== Select Model for {prov.upper()} (Quota: {quota.status} | Remaining: {quota.remaining}) ===[/bold cyan]")
        for idx, m in enumerate(models, 1):
            active_marker = " [bold green][ACTIVE][/bold green]" if m.id == active_model else ""
            think_marker = " [magenta](DeepThink)[/magenta]" if m.supports_deep_think else ""
            self.console.print(f"  [bold yellow][{idx}][/bold yellow] [bold white]{m.id}[/bold white]{active_marker}{think_marker} - {m.description} [dim](Context: {m.context_window:,})[/dim]")
        
        other_prov = "gemini" if prov == "chatgpt" else "chatgpt"
        self.console.print(f"  [bold yellow][P][/bold yellow] [dim]Switch Active Provider to {other_prov.upper()}[/dim]")
        self.console.print("  [bold yellow][C][/bold yellow] [dim]Cancel[/dim]")

        try:
            choice = await asyncio.to_thread(lambda: input("\nSelect Option [1-4 / P / C] > "))
            choice = choice.strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print("[dim]Model selection cancelled.[/dim]")
            return

        if choice.upper() == "P":
            default_model = "gpt-4o" if other_prov == "chatgpt" else "gemini-1.5-pro"
            self.config.update(active_provider=other_prov, active_model=default_model)
            self.clear_history()
            self.console.print(f"[bold green]✓ Switched provider to {other_prov.upper()} (Active model: {default_model})[/bold green]")
        elif choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(models):
                selected = models[num - 1]
                self.config.update(active_model=selected.id)
                self.console.print(f"[bold green]✓ Switched active model to '{selected.id}' ({selected.name})[/bold green]")
            else:
                self.console.print("[red]Invalid selection number.[/red]")
        elif choice.upper() == "C" or not choice:
            self.console.print("[dim]Model selection cancelled.[/dim]")
        else:
            is_valid = await self.registry.is_valid_model(prov, choice)
            if is_valid:
                self.config.update(active_model=choice)
                self.console.print(f"[bold green]✓ Switched active model to '{choice}'[/bold green]")
            else:
                self.console.print(f"[red]Option '{choice}' not recognized.[/red]")

    async def execute_shell_command(self, cmd_line: str) -> None:
        """
        Executes native shell development commands through permission gates.
        """
        req = PermissionRequest(
            action_type="shell_execution",
            target=cmd_line,
            reason=f"Execute shell command '{cmd_line}'"
        )
        
        granted = self.permission_manager.is_permission_granted(req)
        if granted is None:
            self.console.print(f"\n[bold yellow]=== Permission Requested ===[/bold yellow]")
            self.console.print(f"Action: Shell Execution\nTarget: {cmd_line}")
            self.console.print("[1] Allow Once | [2] Allow Session | [3] Deny")
            try:
                dec = await asyncio.to_thread(lambda: input("Choice [1/2/3] > "))
                dec = dec.strip()
            except (EOFError, KeyboardInterrupt):
                dec = "3"
            
            if dec == "1":
                granted = self.permission_manager.grant_permission(req, "allow_once")
            elif dec == "2":
                granted = self.permission_manager.grant_permission(req, "allow_session")
            else:
                granted = self.permission_manager.grant_permission(req, "deny")

        if not granted:
            self.console.print(f"[bold red]Permission Denied:[/bold red] Execution of '{cmd_line}' cancelled.")
            return

        self.console.print(f"[dim]Executing: {cmd_line}[/dim]")
        try:
            res = await asyncio.to_thread(
                lambda: subprocess.run(cmd_line, shell=True, capture_output=True, text=True, timeout=30)
            )
            if res.stdout:
                self.console.print(res.stdout)
            if res.stderr:
                self.console.print(f"[yellow]{res.stderr}[/yellow]")
            self.console.print(f"[dim]Exit code: {res.returncode}[/dim]")
        except Exception as e:
            self.console.print(f"[bold red]Execution error:[/bold red] {e}")

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
        
        self.config.update(active_provider=provider)
        self.registry._reload_adapters()

    async def process_input(self, user_input: str) -> bool:
        user_input = user_input.strip()
        if not user_input:
            return True

        if user_input.lower() in ("exit", "quit", "/quit"):
            self.console.print("[yellow]Exiting Antigravity CLI. Goodbye![/yellow]")
            return False

        # Native shell command execution prefix (!)
        if user_input.startswith("!"):
            await self.execute_shell_command(user_input[1:].strip())
            return True

        # Slash commands
        if user_input.startswith("/"):
            if user_input == "/":
                await self.show_command_palette()
                return True
            elif user_input in ("/models", "/model"):
                await self.show_interactive_model_picker()
                return True
            elif user_input in ("/clear", "/reset"):
                self.clear_history()
                self.console.print(Panel("Conversation context history cleared.", border_style="yellow", title="Command: clear"))
                return True
            elif user_input == "/skills" or user_input.startswith("/skills "):
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
            
            if self.config.config.active_provider != prev_prov:
                self.clear_history()

            if res.data and res.data.get("action") == "import_prompt":
                await self.handle_session_import_interactive(res.data.get("provider", "chatgpt"))
            else:
                border_color = "green" if res.success else "red"
                self.console.print(Panel(res.message, border_style=border_color, title=f"Command: {res.command}"))
            return True

        # Regular Chat Execution
        cfg = self.config.config
        adapter = self.registry.get_adapter(cfg.active_provider)

        # Verify authentication state strictly
        health = await adapter.validate_session()
        if not health.is_authenticated:
            self.console.print(f"[bold red]Error:[/bold red] Active provider {cfg.active_provider.upper()} is unauthenticated.")
            self.console.print(f"[yellow]Run `/session import {cfg.active_provider}` to provide your valid session cookies.[/yellow]")
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
            error_msg = f"\n[bold red]Live Stream Error:[/bold red] {e}\n"
            self.console.print(error_msg)
            response_text += f"\n[Error: {e}]"

        sys.stdout.write("\n\n")
        self.history.append(ChatMessage(role="assistant", content=response_text))
        self.save_history()
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
