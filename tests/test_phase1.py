import json
import logging
import pytest
from pathlib import Path
from antigravity_cli.config import ConfigManager, AppConfig
from antigravity_cli.logging import RedactFilter, setup_logger
from antigravity_cli.vault import VaultManager, SessionMetadata


def test_config_defaults(tmp_path):
    cm = ConfigManager(config_dir=str(tmp_path))
    cfg = cm.config
    assert cfg.active_provider == "chatgpt"
    assert cfg.active_model == "gpt-4o"
    assert cfg.deep_think is False
    assert Path(cfg.app_dir) == tmp_path.resolve()


def test_config_update(tmp_path):
    cm = ConfigManager(config_dir=str(tmp_path))
    cm.update(active_provider="gemini", active_model="gemini-1.5-pro", deep_think=True)
    
    # Reload from disk
    cm2 = ConfigManager(config_dir=str(tmp_path))
    assert cm2.config.active_provider == "gemini"
    assert cm2.config.active_model == "gemini-1.5-pro"
    assert cm2.config.deep_think is True


def test_logging_redaction():
    filter_ = RedactFilter()
    
    # Cookie header redaction
    raw_log = "Sending headers: Cookie: session_token=secret_12345; __Secure-next-auth.session-token=abc"
    redacted = filter_.redact_string(raw_log)
    assert "secret_12345" not in redacted
    assert "REDACTED_COOKIE_HEADER" in redacted

    # Bearer token redaction
    bearer_log = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
    redacted_bearer = filter_.redact_string(bearer_log)
    assert "eyJhbGci" not in redacted_bearer
    assert "REDACTED_TOKEN" in redacted_bearer or "REDACTED_JWT" in redacted_bearer


def test_vault_encryption(tmp_path):
    vault_file = tmp_path / "vault.enc"
    key_file = tmp_path / "vault.key"
    vm = VaultManager(vault_path=vault_file, key_path=key_file)

    secret_data = {
        "raw_cookie": "session_token=test_secret_cookie_token_val; __Secure-next-auth=xyz",
        "cookies": {"session_token": "test_secret_cookie_token_val"}
    }

    meta = vm.save_session(
        provider="chatgpt",
        secret_payload=secret_data,
        format_type="header_string",
        account_label="user@example.com"
    )

    assert meta.provider == "chatgpt"
    assert meta.is_valid is True

    # Check raw file contents on disk — MUST NOT CONTAIN PLAINTEXT SECRETS
    with open(vault_file, "r") as f:
        content = f.read()
        assert "test_secret_cookie_token_val" not in content

    # Read back decrypted secret
    retrieved = vm.get_session_secret("chatgpt")
    assert retrieved is not None
    assert retrieved["cookies"]["session_token"] == "test_secret_cookie_token_val"
