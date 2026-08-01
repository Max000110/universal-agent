import pytest
from antigravity_cli.config import ConfigManager
from antigravity_cli.vault import VaultManager
from antigravity_cli.registry import ModelRegistry
from antigravity_cli.router import CommandRouter


@pytest.fixture
def setup_router(tmp_path):
    cm = ConfigManager(config_dir=str(tmp_path))
    vm = VaultManager(vault_path=tmp_path / "v.enc", key_path=tmp_path / "v.key")
    reg = ModelRegistry(vault_manager=vm)
    router = CommandRouter(config_manager=cm, vault_manager=vm, model_registry=reg)
    return router, cm, vm


@pytest.mark.asyncio
async def test_cmd_help(setup_router):
    router, cm, vm = setup_router
    res = await router.execute("/help")
    assert res.success is True
    assert "/users" in res.message
    assert "/models" in res.message


@pytest.mark.asyncio
async def test_cmd_deepthink_toggle(setup_router):
    router, cm, vm = setup_router
    assert cm.config.deep_think is False

    res = await router.execute("/deepthink on")
    assert res.success is True
    assert cm.config.deep_think is True
    assert "ENABLED" in res.message

    res = await router.execute("/deepthink off")
    assert res.success is True
    assert cm.config.deep_think is False
    assert "DISABLED" in res.message


@pytest.mark.asyncio
async def test_cmd_model_switch(setup_router):
    router, cm, vm = setup_router
    assert cm.config.active_model == "gpt-4o"

    # Switch model to valid ChatGPT model
    res = await router.execute("/model o3-mini")
    assert res.success is True
    assert cm.config.active_model == "o3-mini"

    # Switch provider via model command
    res = await router.execute("/model gemini-1.5-pro")
    assert res.success is True
    assert cm.config.active_provider == "gemini"
    assert cm.config.active_model == "gemini-1.5-pro"

    # Invalid model rejection
    res = await router.execute("/model invalid-model-xyz")
    assert res.success is False
    assert "not recognized" in res.message


@pytest.mark.asyncio
async def test_cmd_users_and_context(setup_router):
    router, cm, vm = setup_router
    res_users = await router.execute("/users")
    assert res_users.success is True
    assert "CHATGPT" in res_users.message
    assert "GEMINI" in res_users.message

    res_ctx = await router.execute("/context")
    assert res_ctx.success is True
    assert "128,000" in res_ctx.message or "tokens" in res_ctx.message
