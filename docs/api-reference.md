# API 레퍼런스

## POST `/v1/chat/completions`

OpenAI Chat Completions API와 동일한 형식.

### 요청 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|:----:|------|
| `messages` | `Message[]` | ✓ | 대화 메시지 배열 |
| `model` | `string` | | 에이전트 프로필 이름. 없으면 `default` 프로필 사용 |
| `stream` | `bool` | | `true`면 SSE 스트리밍. 기본 `false` |
| `temperature` | `float` | | 0.0 ~ 2.0. 높을수록 창의적, 낮을수록 일관적 |
| `max_tokens` | `int` | | 최대 생성 토큰 수 |
| `top_p` | `float` | | 0.0 ~ 1.0. nucleus sampling |
| `response_format` | `object` | | `{"type": "json_object"}` 으로 JSON 모드 활성화 |

> `model` 필드는 OpenAI와 달리 **프로필 이름**으로 해석됩니다. 실제 LLM 모델은 `.env`의 `LLM_DEFAULT_MODEL`로 고정됩니다.

### `messages[].role` 상세

| role | 역할 | 설명 |
|------|------|------|
| `system` | 시스템 | 모델의 행동 방식을 지시하는 설정 메시지. 에이전트 프로필의 `system_prompt`가 자동 주입됩니다. 요청에 이미 포함되어 있으면 덮어쓰지 않습니다. |
| `user` | 사용자 | 사람이 보내는 메시지. |
| `assistant` | 모델 | 모델이 이전에 생성한 응답. 멀티턴 대화 히스토리 전달 시 포함합니다. |

멀티턴 대화 예시:

```json
{
  "messages": [
    {"role": "system",    "content": "당신은 친절한 어시스턴트입니다."},
    {"role": "user",      "content": "파이썬이 뭐야?"},
    {"role": "assistant", "content": "파이썬은 프로그래밍 언어입니다..."},
    {"role": "user",      "content": "어디에 주로 쓰여?"}
  ]
}
```

### 기본 요청

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "안녕하세요"}],
    "model": "default"
  }'
```

### 응답

```jsonc
{
  "id": "chatcmpl-abc123",      // 응답 고유 ID
  "object": "chat.completion",  // 항상 "chat.completion"
  "created": 1700000000,        // 응답 생성 시각 (Unix timestamp)
  "model": "gemma-4-2b",        // 실제로 사용된 LLM 모델명 (LLM_DEFAULT_MODEL)
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "안녕하세요!"
    },
    "finish_reason": "stop"     // "stop" = 정상 완료
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

> `usage` 토큰 수는 백엔드가 제공하는 경우에만 정확합니다.

### 스트리밍 (`stream: true`)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "안녕하세요"}],
    "stream": true
  }'
```

응답은 SSE(Server-Sent Events) 형식으로 청크 단위로 전달됩니다. 마지막에 `data: [DONE]`으로 종료됩니다.

### JSON 모드 (`response_format`)

```json
{
  "messages": [{"role": "user", "content": "사용자 정보를 JSON으로 반환해줘"}],
  "response_format": {"type": "json_object"}
}
```

모델이 마크다운 코드블록(` ```json ... ``` `)으로 응답을 감싸는 경우 자동으로 펜스를 제거하고 JSON만 반환합니다.

---

## GET `/v1/models`

로컬 LLM 서버에 현재 올라와 있는 모델 목록을 그대로 프록시합니다.

```json
{
  "object": "list",
  "data": [
    {"id": "gemma-4-2b", "object": "model", "owned_by": "local"}
  ]
}
```

로컬 LLM 서버의 `GET /v1/models`를 그대로 프록시합니다.

---

## GET `/health`

LLM 서버(백엔드) 연결 상태를 확인합니다.

```json
{"status": "ok", "backend": "ok"}              // HTTP 200 — LLM 서버 정상
{"status": "degraded", "backend": "degraded"}  // HTTP 503 — LLM 서버 응답 없음
```

| 필드 | 의미 |
|------|------|
| `status` | 전체 서비스 상태. LLM 서버가 응답하면 `ok` |
| `backend` | LLM 서버 상태. `status`와 동일한 값 |

> `status` / `backend` 모두 **LLM 서버까지 연결이 되는지**를 나타냅니다. API 서버 자체의 생존 여부는 응답을 받은 것 자체로 확인됩니다.
