# 아키텍처

## 요청 흐름

```
LangGraph Agent
      │  OpenAI API 형식
      ▼
┌─────────────────────────────┐
│   FastAPI (bokjidream-llm)  │
│                             │
│  POST /v1/chat/completions  │
│  GET  /v1/models            │
│  GET  /health               │
│                             │
│  Profile System (YAML)      │
│  → 시스템 프롬프트 주입       │
│  → 파라미터 기본값 적용       │
└────────────┬────────────────┘
             │
   mlx_lm / vLLM / llama.cpp
   (OpenAI 호환 API)
```

**요청 흐름:** HTTP 요청 → 라우터 → 프로필 적용 (시스템 프롬프트 주입) → 백엔드 전달

## 프로젝트 구조

```
app/
├── main.py              # FastAPI 앱 진입점
├── config.py            # 환경변수 설정
├── middleware/
│   └── logging.py       # 요청/응답 로깅 미들웨어
├── routers/
│   ├── chat.py          # POST /v1/chat/completions
│   ├── health.py        # GET /health
│   └── models.py        # GET /v1/models
├── schemas/
│   ├── chat.py          # 요청/응답 Pydantic 모델
│   └── models.py        # 모델 목록 Pydantic 모델
├── services/
│   ├── chat_service.py  # 프로필 적용 후 백엔드 호출
│   ├── llm_client.py    # 백엔드 팩토리
│   └── backends/
│       ├── base.py          # 추상 베이스 클래스
│       └── openai_compat.py # OpenAI 호환 백엔드 (mlx_lm / vLLM / llama.cpp)
└── profiles/
    ├── loader.py        # YAML 로더 (LRU 캐시)
    └── profiles.yaml    # 에이전트 프로필 정의
```

## 기술 스택

- **Python 3.11+**
- **FastAPI** — API 서버
- **Pydantic v2** — 스키마 검증 및 설정 관리
- **httpx** — 비동기 HTTP 클라이언트
- **PyYAML** — 프로필 설정
- **pytest + pytest-asyncio** — 테스트
- **Ruff** — 린트 및 포맷
