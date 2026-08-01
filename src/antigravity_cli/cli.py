import sys
import asyncio
import typer
from rich.console import Console
from rich.panel import Panel

from antigravity_cli import __version__, __app_name__
from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.session_validator import SessionValidator
from antigravity_cli.tui import AntigravityTUI

app = typer.Typer(
    name=__app_name__,
    help="Local-first agentic framework CLI with session cookie login for ChatGPT and Gemini",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Default entrypoint: Launches interactive TUI shell if no subcommand is passed.
    """
    if ctx.invoked_subcommand is None:
        config_mgr = ConfigManager()
        vault_mgr = VaultManager(
            vault_path=config_mgr.config.get_vault_path(),
            key_path=config_mgr.config.get_key_path()
        )
        tui = AntigravityTUI(config_manager=config_mgr, vault_manager=vault_mgr)
        try:
            asyncio.run(tui.run_loop())
        except (KeyboardInterrupt, SystemExit):
            pass


@app.command("version")
def version():
    """Display version and platform build details."""
    console.print(f"[bold cyan]{__app_name__}[/bold cyan] version [bold yellow]v{__version__}[/bold yellow]")


@app.command("status")
def status():
    """Display framework status, active model, and session health."""
    config_mgr = ConfigManager()
    vault_mgr = VaultManager(
        vault_path=config_mgr.config.get_vault_path(),
        key_path=config_mgr.config.get_key_path()
    )
    cfg = config_mgr.config
    meta = vault_mgr.get_session_metadata(cfg.active_provider)
    health = meta.validation_status if meta else "UNAUTHENTICATED"

    console.print(Panel(
        f"[bold yellow]Provider:[/bold yellow] {cfg.active_provider.upper()}\n"
        f"[bold yellow]Active Model:[/bold yellow] {cfg.active_model}\n"
        f"[bold yellow]Deep Think:[/bold yellow] {'ON' if cfg.deep_think else 'OFF'}\n"
        f"[bold yellow]Session Health:[/bold yellow] {health}\n"
        f"[bold yellow]App Dir:[/bold yellow] {cfg.app_dir}",
        title="Antigravity Status",
        border_style="cyan"
    ))


@app.command("import-session")
def import_session(
    provider: str = typer.Argument("chatgpt", help="Target provider: 'chatgpt' or 'gemini'"),
    session_data: str = typer.Option(None, "--data", "-d", help="Raw Cookie Header string or JSON payload")
):
    """Import session cookies for ChatGPT or Gemini."""
    config_mgr = ConfigManager()
    vault_mgr = VaultManager(
        vault_path=config_mgr.config.get_vault_path(),
        key_path=config_mgr.config.get_key_path()
    )

    if not session_data:
        console.print("[dim]Paste Cookie Header string OR JSON cookie export blob:[/dim]")
        session_data = input("Cookie Data > ").strip()

    val_res = SessionValidator.validate_session(provider, session_data)
    if not val_res.is_valid:
        console.print(f"[bold red]Validation Failed:[/bold red] {val_res.error_message}")
        sys.exit(1)

    meta = vault_mgr.save_session(
        provider=provider,
        secret_payload=val_res.normalized_session,
        format_type=val_res.format_type,
        is_valid=True,
        validation_status="VALID"
    )

    console.print(f"[bold green]✓ Session successfully imported and encrypted for {provider.upper()}![/bold green]")
    console.print(f"[dim]Format: {val_res.format_type} | Cookies: {val_res.normalized_session['cookie_count']}[/dim]")


@app.command("exec")
def execute_prompt(
    prompt: str = typer.Argument(..., help="Prompt or slash command to execute"),
):
    """Execute a single prompt or slash command non-interactively."""
    config_mgr = ConfigManager()
    vault_mgr = VaultManager(
        vault_path=config_mgr.config.get_vault_path(),
        key_path=config_mgr.config.get_key_path()
    )
    tui = AntigravityTUI(config_manager=config_mgr, vault_manager=vault_mgr)
    asyncio.run(tui.process_input(prompt))


if __name__ == "__main__":
    app()
