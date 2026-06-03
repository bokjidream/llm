from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.models import ModelList


class BaseBackend(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[str]: ...

    @abstractmethod
    async def list_models(self) -> ModelList: ...

    @abstractmethod
    async def health(self) -> bool: ...
