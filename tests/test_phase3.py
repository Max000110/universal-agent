import pytest
from antigravity_cli.vault import VaultManager
from antigravity_cli.registry import ModelRegistry
from antigravity_cli.providers.chatgpt import ChatGPTAdapter
from antigravity_cli.providers.gemini import GeminiAdapter
from antigravity_cli.providers.base import ChatMessage


@pytest.mark.asyncio
async def test_chatgpt_adapter_models(monkeypatch):
    monkeypatch.setenv('UAG_TEST_MODE', '1')
    adapter = ChatGPTAdapter()
    models = await adapter.list_models()
    assert len(models) >= 3
    assert any(m.id == "gpt-4o" for m in models)


@pytest.mark.asyncio
async def test_gemini_adapter_models(monkeypatch):
    monkeypatch.setenv('UAG_TEST_MODE', '1')
    adapter = GeminiAdapter()
    models = await adapter.list_models()
    assert len(models) >= 3
    assert any(m.id == "gemini-1.5-pro" for m in models)


@pytest.mark.asyncio
async def test_model_registry(tmp_path, monkeypatch):
    monkeypatch.setenv('UAG_TEST_MODE', '1')
    vm = VaultManager(vault_path=tmp_path / "v.enc", key_path=tmp_path / "v.key")
    reg = ModelRegistry(vault_manager=vm)
    
    chatgpt_models = await reg.get_models_for_provider("chatgpt")
    assert len(chatgpt_models) > 0

    gemini_models = await reg.get_models_for_provider("gemini")
    assert len(gemini_models) > 0

    assert await reg.is_valid_model("chatgpt", "gpt-4o") is True
    assert await reg.is_valid_model("gemini", "gemini-1.5-pro") is True
    assert await reg.is_valid_model("chatgpt", "non-existent-model") is False


@pytest.mark.asyncio
async def test_streaming_chat_with_deepthink(monkeypatch):
    monkeypatch.setenv('UAG_TEST_MODE', '1')
    adapter = ChatGPTAdapter(session_data={"cookies": {"session_token": "valid"}})
    messages = [ChatMessage(role="user", content="Hello test prompt")]

    # Stream with deep_think=True
    chunks = []
    async for chunk in adapter.stream_chat(messages=messages, model="gpt-4o", deep_think=True):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert "gpt-4o" in full_response
    assert "Thinking Process" in full_response or "REASONING POLICY" in full_response
    assert "Hello test prompt" in full_response
