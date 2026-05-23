"""MLX LM / vLLM / llama.cpp — OpenAI 호환 백엔드."""

import asyncio
import logging
import math
import re
import time
import uuid
from collections.abc import AsyncIterator

import httpx

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Choice,
    Message,
    Usage,
)
from app.schemas.models import ModelInfo, ModelList
from app.services.backends.base import BaseBackend

logger = logging.getLogger("llm_api")


class OpenAICompatBackend(BaseBackend):
    """
    OpenAI /v1 API 형식을 그대로 사용하는 백엔드.
    - MLX LM  : mlx_lm.server (기본 포트 8080)
    - vLLM    : vllm.entrypoints.openai.api_server (기본 포트 8000)
    - llama.cpp: llamafile / server (기본 포트 8080)
    """

    def __init__(self, base_url: str, default_model: str, timeout: int | None, api_key: str | None = None, min_interval: float = 0.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._min_interval = min_interval
        self._last_request_at: float = 0.0
        self._throttle_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def _throttle(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._throttle_lock:
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        await self._throttle()
        model = request.model or self._default_model
        payload = self._build_payload(request, model, stream=False)

        json_mode = (
            request.response_format is not None and request.response_format.type == "json_object"
        )
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers) as client:
            for attempt in range(3):
                resp = await client.post(f"{self._base_url}/v1/chat/completions", json=payload)
                if resp.status_code == 429:
                    wait = self._parse_retry_after(resp.text)
                    logger.warning("[Groq 429] %ds 후 재시도 (%d/3)", wait, attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                if resp.is_error:
                    logger.warning("[Groq %d] %s", resp.status_code, resp.text[:500])
                    raise httpx.HTTPStatusError(
                        f"[{resp.status_code}] {resp.text[:300]}",
                        request=resp.request,
                        response=resp,
                    )
                return self._parse_response(resp.json(), model, json_mode=json_mode)
            logger.warning("[Groq 429] 재시도 3회 초과: %s", resp.text[:300])
            raise httpx.HTTPStatusError(
                "[429] rate limit — gave up after 3 retries",
                request=resp.request,
                response=resp,
            )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        await self._throttle()
        model = request.model or self._default_model
        payload = self._build_payload(request, model, stream=True)

        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers) as client:
            for attempt in range(3):
                async with client.stream(
                    "POST", f"{self._base_url}/v1/chat/completions", json=payload
                ) as resp:
                    if resp.status_code == 429:
                        body = await resp.aread()
                        wait = self._parse_retry_after(body.decode())
                        logger.warning("[Groq 429] %ds 후 재시도 (%d/3)", wait, attempt + 1)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            yield line + "\n\n"
                    yield "data: [DONE]\n\n"
                    return
            logger.warning("[Groq 429] 재시도 3회 초과")
            raise RuntimeError("[429] rate limit — gave up after 3 retries")

    async def list_models(self) -> ModelList:
        async with httpx.AsyncClient(timeout=10, headers=self._headers) as client:
            resp = await client.get(f"{self._base_url}/v1/models")
            resp.raise_for_status()
            data = resp.json()

        models = [ModelInfo(id=m["id"]) for m in data.get("data", [])]
        return ModelList(data=models)

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5, headers=self._headers) as client:
                resp = await client.get(f"{self._base_url}/v1/models")
                return resp.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_retry_after(text: str) -> int:
        m = re.search(r'try again in (\d+\.?\d*)s', text)
        return math.ceil(float(m.group(1))) if m else 60

    def _build_payload(self, request: ChatRequest, model: str, *, stream: bool) -> dict:
        payload: dict = {
            "model": model,
            "messages": [m.model_dump() for m in request.messages],
            "stream": stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_format is not None:
            payload["response_format"] = request.response_format.model_dump()
        return payload

    @staticmethod
    def _strip_think_blocks(text: str) -> str:
        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()

    @staticmethod
    def _strip_json_fences(text: str) -> str:
        """모델이 JSON을 마크다운 코드블록으로 감싸 반환하는 경우 펜스를 제거한다."""
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            return "\n".join(inner).strip()
        return text

    def _parse_response(self, data: dict, model: str, *, json_mode: bool = False) -> ChatResponse:
        choice = data["choices"][0]
        content = self._strip_think_blocks(choice["message"]["content"] or "")
        if json_mode:
            content = self._strip_json_fences(content)
        usage_data = data.get("usage", {})

        return ChatResponse(
            id=data.get("id", f"chatcmpl-{uuid.uuid4().hex}"),
            created=data.get("created", int(time.time())),
            model=model,
            choices=[Choice(message=Message(role="assistant", content=content))],
            usage=Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
        )
