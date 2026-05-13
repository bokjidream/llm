import json
import logging
import re
import time
from collections.abc import AsyncIterator

from app.config import settings
from app.profiles import get_profile
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.services.llm_client import llm_client

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


def _apply_profile(request: ChatRequest) -> ChatRequest:
    """model 필드를 프로필 이름으로 해석해 시스템 프롬프트와 파라미터를 주입한다."""
    profile_name = request.model or "default"
    profile = get_profile(profile_name)
    logger.debug(
        "[profile] name=%s temperature=%s system_prompt=%.80r",
        profile_name, profile.temperature, profile.system_prompt,
    )

    # 시스템 프롬프트 주입 (이미 system 메시지가 있으면 덮어쓰지 않음)
    has_system = any(m.role == "system" for m in request.messages)
    messages = request.messages
    if not has_system:
        messages = [Message(role="system", content=profile.system_prompt), *request.messages]

    return ChatRequest(
        model=settings.llm_default_model,
        messages=messages,
        stream=request.stream,
        temperature=request.temperature if request.temperature is not None else profile.temperature,
        max_tokens=request.max_tokens if request.max_tokens is not None else profile.max_tokens,
        top_p=request.top_p,
        response_format=request.response_format,
    )


async def chat(request: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    _log_input(request)
    response = await llm_client.chat(_apply_profile(request))
    elapsed = (time.perf_counter() - start) * 1000
    _log_output(request.model, response.choices[0].message.content, elapsed)
    return response


async def chat_stream(request: ChatRequest) -> AsyncIterator[str]:
    start = time.perf_counter()
    _log_input(request)
    content_parts: list[str] = []
    async for chunk in llm_client.chat_stream(_apply_profile(request)):
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
