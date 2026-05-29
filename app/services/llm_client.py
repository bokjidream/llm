from app.config import settings
from app.services.backends import BaseBackend, OpenAICompatBackend

_backends: dict[str, BaseBackend] = {}


def get_backend(base_url: str) -> BaseBackend:
    if base_url not in _backends:
        _backends[base_url] = OpenAICompatBackend(
            base_url,
            settings.llm_default_model,
            settings.llm_request_timeout,
            settings.llm_api_key,
        )
    return _backends[base_url]


llm_client: BaseBackend = get_backend(settings.llm_base_url)
