import asyncio
from typing import Dict, Any, Callable, Awaitable, List, Optional
from pydantic import BaseModel, Field

from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.registry import ModelRegistry
from antigravity_cli.session_validator import SessionValidator


class CommandResult(BaseModel):
    success: bool
    command: str
    message: str
    data: Optional[Dict[str, Any]] = None


class CommandRouter:
    """
    Slash command router for Antigravity CLI.
    Parses and dispatches slash commands cleanly.
    """

    def __init__(self, config_manager: ConfigManager, vault_manager: VaultManager, model_registry: ModelRegistry):
        self.config = config_manager
        self.vault = vault_manager
        self.registry = model_registry

    async def execute(self, input_text: str) -> CommandResult:
        input_text = input_text.strip()
        if not input_text.startswith("/"):
            return CommandResult(success=False, command="unknown", message="Not a slash command")

        parts = input_text[1:].split()
        if not parts:
            return await self._cmd_help([])

        cmd_name = parts[0].lower()
        args = parts[1:]

        if cmd_name == "users":
            return await self._cmd_users(args)
        elif cmd_name == "context":
            return await self._cmd_context(args)
        elif cmd_name == "models":
            return await self._cmd_models(args)
        elif cmd_name == "model":
            return await self._cmd_model(args)
        elif cmd_name == "deepthink":
            return await self._cmd_deepthink(args)
        elif cmd_name == "session":
            return await self._cmd_session(args)
        elif cmd_name == "status":
            return await self._cmd_status(args)
        elif cmd_name in ("help", "?"):
            return await self._cmd_help(args)
        else:
            return CommandResult(
                success=False,
                command=cmd_name,
                message=f"Unknown command '/{cmd_name}'. Type /help for available commands."
            )

    async def _cmd_users(self, args: List[str]) -> CommandResult:
        sessions = self.vault.list_sessions()
        active_prov = self.config.config.active_provider
        
        lines = ["=== User Sessions & Account Quotas ==="]
        for prov in ["chatgpt", "gemini"]:
            meta = sessions.get(prov)
            is_active = (prov == active_prov)
            active_marker = " [ACTIVE]" if is_active else ""
            if meta:
                quota = await self.registry.get_quota_info(prov)
                lines.append(f"• {prov.upper()}{active_marker}: Account={meta.account_label} | Format={meta.format_type} | Status={meta.validation_status} | Quota={quota.status} (Remaining: {quota.remaining})")
            else:
                lines.append(f"• {prov.upper()}{active_marker}: Not Authenticated (Use /session import {prov})")

        return CommandResult(success=True, command="users", message="\n".join(lines))

    async def _cmd_context(self, args: List[str]) -> CommandResult:
        prov = self.config.config.active_provider
        model = self.config.config.active_model
        ctx = await self.registry.get_context_info(prov, model)

        msg = (
            f"=== Model Context Window ===\n"
            f"Active Provider : {prov.upper()}\n"
            f"Active Model    : {model}\n"
            f"Max Context     : {ctx.max_context:,} tokens\n"
            f"Used Tokens     : {ctx.used_context:,} tokens\n"
            f"Remaining       : {ctx.remaining_context:,} tokens ({100 - ctx.percentage_used}% free)"
        )
        return CommandResult(success=True, command="context", message=msg)

    async def _cmd_models(self, args: List[str]) -> CommandResult:
        filter_str = args[0].lower() if args else ""
        prov = self.config.config.active_provider
        active_model = self.config.config.active_model
        
        models = await self.registry.get_models_for_provider(prov)
        lines = [f"=== Available Models for {prov.upper()} ==="]
        for m in models:
            if filter_str and filter_str not in m.id.lower() and filter_str not in m.name.lower():
                continue
            active_tag = " [ACTIVE]" if m.id == active_model else ""
            think_tag = " (DeepThink Supported)" if m.supports_deep_think else ""
            lines.append(f"• {m.id} - {m.name}{active_tag}{think_tag}\n  {m.description} [Context: {m.context_window:,}]")

        return CommandResult(success=True, command="models", message="\n".join(lines))

    async def _cmd_model(self, args: List[str]) -> CommandResult:
        if not args:
            curr = self.config.config.active_model
            prov = self.config.config.active_provider
            return CommandResult(success=True, command="model", message=f"Current active model: {curr} (Provider: {prov})")

        target_model = args[0].strip()
        prov = self.config.config.active_provider

        # If switching provider directly (e.g. /model gemini-1.5-pro or /model chatgpt)
        if target_model.lower() in ("chatgpt", "gemini"):
            self.config.update(active_provider=target_model.lower())
            # Default model for new provider
            default_model = "gpt-4o" if target_model.lower() == "chatgpt" else "gemini-1.5-pro"
            self.config.update(active_model=default_model)
            return CommandResult(success=True, command="model", message=f"Switched provider to {target_model.upper()} (Active model: {default_model})")

        is_valid = await self.registry.is_valid_model(prov, target_model)
        if not is_valid:
            # Check if model belongs to other provider
            other_prov = "gemini" if prov == "chatgpt" else "chatgpt"
            if await self.registry.is_valid_model(other_prov, target_model):
                self.config.update(active_provider=other_prov, active_model=target_model)
                return CommandResult(success=True, command="model", message=f"Switched provider to {other_prov.upper()} and active model to '{target_model}'.")
            return CommandResult(success=False, command="model", message=f"Model '{target_model}' not recognized for provider {prov}. Type /models to list valid models.")

        self.config.update(active_model=target_model)
        return CommandResult(success=True, command="model", message=f"Switched active model to '{target_model}'.")

    async def _cmd_deepthink(self, args: List[str]) -> CommandResult:
        curr = self.config.config.deep_think
        if not args:
            new_val = not curr
        else:
            opt = args[0].lower()
            if opt in ("on", "true", "1", "enable"):
                new_val = True
            elif opt in ("off", "false", "0", "disable"):
                new_val = False
            elif opt in ("toggle", "switch"):
                new_val = not curr
            else:
                return CommandResult(success=False, command="deepthink", message="Invalid argument. Use: /deepthink [on|off|toggle]")

        self.config.update(deep_think=new_val)
        state_str = "ENABLED" if new_val else "DISABLED"
        return CommandResult(success=True, command="deepthink", message=f"Deep Think reasoning policy is now {state_str}.")

    async def _cmd_session(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(success=False, command="session", message="Usage: /session [validate|import] [chatgpt|gemini]")

        subcmd = args[0].lower()
        target_prov = args[1].lower() if len(args) > 1 else self.config.config.active_provider

        if subcmd == "validate":
            meta = self.vault.get_session_metadata(target_prov)
            if not meta:
                return CommandResult(success=False, command="session", message=f"No stored session for {target_prov.upper()}. Use /session import {target_prov}")

            secret = self.vault.get_session_secret(target_prov)
            if not secret:
                return CommandResult(success=False, command="session", message=f"Corrupted or missing secret payload for {target_prov.upper()}.")

            # Validate structural tokens
            val_res = SessionValidator.validate_session(target_prov, secret.get("cookie_header", ""))
            status_str = "VALID" if val_res.is_valid else f"INVALID: {val_res.error_message}"
            self.vault.update_session_status(target_prov, val_res.is_valid, status_str)
            return CommandResult(success=True, command="session", message=f"Session validation for {target_prov.upper()}: {status_str}")

        elif subcmd == "import":
            return CommandResult(
                success=True,
                command="session",
                message=f"Interactive session import triggered for {target_prov.upper()}.",
                data={"action": "import_prompt", "provider": target_prov}
            )

        return CommandResult(success=False, command="session", message="Unknown sub-command. Use: /session [validate|import]")

    async def _cmd_status(self, args: List[str]) -> CommandResult:
        cfg = self.config.config
        meta = self.vault.get_session_metadata(cfg.active_provider)
        session_health = meta.validation_status if meta else "Unauthenticated"

        msg = (
            f"=== System Status ===\n"
            f"Active Provider : {cfg.active_provider.upper()}\n"
            f"Active Model    : {cfg.active_model}\n"
            f"Deep Think      : {'ON' if cfg.deep_think else 'OFF'}\n"
            f"Session Health  : {session_health}\n"
            f"Vault Path      : {cfg.get_vault_path()}\n"
            f"App Directory   : {cfg.app_dir}"
        )
        return CommandResult(success=True, command="status", message=msg)

    async def _cmd_help(self, args: List[str]) -> CommandResult:
        help_text = (
            "=== Antigravity CLI Slash Commands ===\n"
            "/users                   - View provider sessions, account health & quota\n"
            "/context                 - View model context window limits and usage\n"
            "/models [filter]         - List available models for active provider\n"
            "/model <name|provider>   - Switch active model or provider\n"
            "/deepthink [on|off]      - Toggle deep thinking reasoning policy\n"
            "/skills                  - List installed built-in & custom skills\n"
            "/session validate        - Validate active provider session cookies\n"
            "/session import <prov>   - Import session cookies (Header string or JSON)\n"
            "/status                  - Display framework runtime & vault status\n"
            "/help                    - Display command palette documentation"
        )
        return CommandResult(success=True, command="help", message=help_text)
