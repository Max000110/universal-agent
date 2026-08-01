from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    context_window: int = 128000
    supports_deep_think: bool = True
    description: str = ""
    is_active: bool = False


class QuotaInfo(BaseModel):
    provider: str
    limit: Optional[int] = None
    used: Optional[int] = None
    remaining: Optional[int] = None
    reset_at: Optional[str] = None
    status: str = "OK"  # "OK", "WARNING", "EXHAUSTED"


class ContextInfo(BaseModel):
    model_id: str
    max_context: int
    used_context: int = 0
    remaining_context: int = 128000

    @property
    def percentage_used(self) -> float:
        if self.max_context <= 0:
            return 0.0
        return round((self.used_context / self.max_context) * 100, 1)


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class SessionHealth(BaseModel):
    provider: str
    is_authenticated: bool
    status_message: str
    last_checked: str


class BaseProviderAdapter(ABC):
    """
    Abstract base class for ChatGPT and Gemini provider adapters.
    """

    def __init__(self, provider_name: str, session_data: Optional[Dict[str, Any]] = None):
        self.provider_name = provider_name
        self.session_data = session_data or {}
        self.cookies = self.session_data.get("cookies", {})

    @abstractmethod
    async def validate_session(self) -> SessionHealth:
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        pass

    @abstractmethod
    async def get_quota(self) -> QuotaInfo:
        pass

    @abstractmethod
    async def get_context_window(self, model_id: str) -> ContextInfo:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        deep_think: bool = False
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
