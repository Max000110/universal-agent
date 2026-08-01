from typing import Dict, List, Optional
from antigravity_cli.providers.base import BaseProviderAdapter, ModelInfo, ContextInfo, QuotaInfo
from antigravity_cli.providers.chatgpt import ChatGPTAdapter
from antigravity_cli.providers.gemini import GeminiAdapter
from antigravity_cli.vault import VaultManager


class ModelRegistry:
    """
    Central model registry normalizing ChatGPT and Gemini provider models,
    context limits, quotas, and active selection states.
    """

    def __init__(self, vault_manager: VaultManager):
        self.vault = vault_manager
        self.adapters: Dict[str, BaseProviderAdapter] = {}
        self._reload_adapters()

    def _reload_adapters(self) -> None:
        chatgpt_sec = self.vault.get_session_secret("chatgpt")
        gemini_sec = self.vault.get_session_secret("gemini")

        self.adapters["chatgpt"] = ChatGPTAdapter(session_data=chatgpt_sec)
        self.adapters["gemini"] = GeminiAdapter(session_data=gemini_sec)

    def get_adapter(self, provider: str) -> BaseProviderAdapter:
        # Always sync with latest vault session state
        self._reload_adapters()
        provider = provider.lower()
        return self.adapters.get(provider, self.adapters["chatgpt"])

    async def get_all_models(self) -> Dict[str, List[ModelInfo]]:
        res = {}
        for prov_name, adapter in self.adapters.items():
            res[prov_name] = await adapter.list_models()
        return res

    async def get_models_for_provider(self, provider: str) -> List[ModelInfo]:
        adapter = self.get_adapter(provider)
        return await adapter.list_models()

    async def is_valid_model(self, provider: str, model_id: str) -> bool:
        models = await self.get_models_for_provider(provider)
        return any(m.id == model_id for m in models)

    async def get_model_info(self, provider: str, model_id: str) -> Optional[ModelInfo]:
        models = await self.get_models_for_provider(provider)
        for m in models:
            if m.id == model_id:
                return m
        return None

    async def get_context_info(self, provider: str, model_id: str) -> ContextInfo:
        adapter = self.get_adapter(provider)
        return await adapter.get_context_window(model_id)

    async def get_quota_info(self, provider: str) -> QuotaInfo:
        adapter = self.get_adapter(provider)
        return await adapter.get_quota()
