from app.config import settings
from app.services.backends import BaseBackend, OpenAICompatBackend


def _create_backend() -> BaseBackend:
    return OpenAICompatBackend(
        settings.llm_base_url,
        settings.llm_default_model,
        settings.llm_request_timeout,
    )


llm_client: BaseBackend = _create_backend()
