import asyncio
import pytest
from pathlib import Path
from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.tui import AntigravityTUI
from antigravity_cli.providers.base import ChatMessage


@pytest.mark.asyncio
async def test_full_sandbox_tui_flow(tmp_path, monkeypatch):
    # Setup temporary sandbox paths
    app_dir = tmp_path / ".antigravitycli"
    vault_path = app_dir / "vault.enc"
    key_path = app_dir / "vault.key"

    config_mgr = ConfigManager(config_dir=str(app_dir))
    vault_mgr = VaultManager(vault_path=vault_path, key_path=key_path)

    # 1. Initialize TUI
    tui = AntigravityTUI(config_manager=config_mgr, vault_manager=vault_mgr)
    assert tui is not None

    # 2. Test status bar rendering when unauthenticated
    status_bar_unauth = await tui.render_status_bar()
    assert "CHATGPT" in status_bar_unauth
    assert "UNAUTHENTICATED" in status_bar_unauth

    # 3. Test cookie import for ChatGPT (Header String format)
    cookie_str = "session_token=test_chatgpt_token_12345; __Secure-next-auth.session-token=secret_val"
    
    async def mock_to_thread_chatgpt(func, *args, **kwargs):
        return cookie_str

    monkeypatch.setattr("asyncio.to_thread", mock_to_thread_chatgpt)
    await tui.handle_session_import_interactive("chatgpt")

    # Verify session metadata and vault state
    meta = vault_mgr.get_session_metadata("chatgpt")
    assert meta is not None
    assert meta.is_valid is True
    assert meta.validation_status == "VALID"

    # 4. Test status bar rendering when authenticated
    status_bar_auth = await tui.render_status_bar()
    assert "VALID" in status_bar_auth

    # 5. Test greeting prompt execution
    await tui.process_input("hi")
    assert len(tui.history) == 2
    assert "Hello" in tui.history[1].content

    # 6. Test multi-turn name introduction and memory retrieval ("whats my name")
    await tui.process_input("my name is Alex")
    assert len(tui.history) == 4
    assert "Alex" in tui.history[3].content

    await tui.process_input("whats my name")
    assert len(tui.history) == 6
    assert "your name is **Alex**" in tui.history[5].content

    # 7. Test Slash Command /deepthink on
    await tui.process_input("/deepthink on")
    assert config_mgr.config.deep_think is True

    # Test query with deepthink enabled
    await tui.process_input("Solve this complex math algorithm")
    assert len(tui.history) == 8
    assert "Thinking Process" in tui.history[7].content

    # 8. Test Slash Command /model to switch to Gemini
    await tui.process_input("/model gemini")
    assert config_mgr.config.active_provider == "gemini"

    # Import Gemini cookies (JSON format)
    gemini_json = '{"__Secure-1PSID": "test_psid_token_5678"}'
    
    async def mock_to_thread_gemini(func, *args, **kwargs):
        return gemini_json

    monkeypatch.setattr("asyncio.to_thread", mock_to_thread_gemini)
    await tui.handle_session_import_interactive("gemini")

    gemini_meta = vault_mgr.get_session_metadata("gemini")
    assert gemini_meta is not None
    assert gemini_meta.is_valid is True

    # Test Gemini prompt execution & multi-turn name recall
    await tui.process_input("my name is Sarah")
    await tui.process_input("whats my name")
    assert len(tui.history) == 4
    assert "your name is **Sarah**" in tui.history[3].content
