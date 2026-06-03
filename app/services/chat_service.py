import json
import logging
import re
import time
from collections.abc import AsyncIterator

from app.config import settings
from app.profiles import get_profile
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.services.backends import BaseBackend
from app.services.llm_client import get_backend

logger = logging.getLogger("llm_api")


def _log_input(request: ChatRequest) -> None:
    lines = [f"\n▶ LangGraph → {request.model}"]
    for m in request.messages:
        lines.append(f"  {m.role}:{_format_content(m.content)}")
    logger.info("\n".join(lines))


def _format_content(content: str) -> str:
    text = content.strip()
    m = re.search(r"```(?:\w+)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        return "\n" + "\n".join(f"  {line}" for line in formatted.splitlines())
    except (json.JSONDecodeError, ValueError):
        return content[:300].replace("\n", " ")


def _log_output(model: str, content: str, elapsed_ms: float = 0) -> None:
    logger.info("\n◀ %s → LangGraph  (%.1fs)\n%s", model, elapsed_ms / 1000, _format_content(content))


def _apply_profile(request: ChatRequest) -> tuple[ChatRequest, BaseBackend]:
    """model 필드를 프로필 이름으로 해석해 시스템 프롬프트와 파라미터를 주입한다."""
    profile_name = request.model or "default"
    profile = get_profile(profile_name)
    model = profile.model or settings.llm_default_model
    base_url = profile.base_url or settings.llm_base_url
    logger.debug(
        "[profile] name=%s model=%s base_url=%s temperature=%s system_prompt=%.80r",
        profile_name, model, base_url, profile.temperature, profile.system_prompt,
    )

    has_system = any(m.role == "system" for m in request.messages)
    messages = request.messages
    if not has_system:
        messages = [Message(role="system", content=profile.system_prompt), *request.messages]

    applied = ChatRequest(
        model=model,
        messages=messages,
        stream=request.stream,
        temperature=request.temperature if request.temperature is not None else profile.temperature,
        max_tokens=request.max_tokens if request.max_tokens is not None else profile.max_tokens,
        top_p=request.top_p,
        response_format=request.response_format,
    )
    return applied, get_backend(base_url)


async def chat(request: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    _log_input(request)
    applied, backend = _apply_profile(request)
    response = await backend.chat(applied)
    elapsed = (time.perf_counter() - start) * 1000
    _log_output(request.model, response.choices[0].message.content, elapsed)
    return response


async def chat_stream(request: ChatRequest) -> AsyncIterator[str]:
    start = time.perf_counter()
    _log_input(request)
    applied, backend = _apply_profile(request)
    content_parts: list[str] = []
    async for chunk in backend.chat_stream(applied):
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            try:
                data = json.loads(chunk[6:])
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    content_parts.append(delta)
            except Exception:
                pass
        yield chunk
    elapsed = (time.perf_counter() - start) * 1000
    _log_output(request.model, "".join(content_parts), elapsed)
