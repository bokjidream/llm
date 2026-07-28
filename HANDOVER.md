# llm/ 인수인계 문서

> 작성일: 2026-07-28 / 브랜치: `develop`

이 문서는 이 저장소(`llm`)를 새로 맡는 사람을 위한 문서입니다. **왜 이렇게 만들었는지, 지금 작업 트리에 뭐가 커밋 안 된 채 남아 있는지, 실제 운영 시 챙겨야 할 것**을 중심으로 씁니다.

## 1. 이 프로젝트가 뭘 하는지

LangGraph 에이전트가 OpenAI 호환 API로 LLM을 호출할 때 중간에 끼는 **프록시 겸 프롬프트 주입 서버**입니다. FastAPI로 `/v1/chat/completions`, `/v1/models`, `/health`를 제공하고, 요청의 `model` 필드를 "실제 모델명"이 아니라 **프로필 이름**으로 해석해서 `app/profiles/profiles.yaml`에 정의된 시스템 프롬프트/파라미터/모델/백엔드 주소를 주입한 뒤 실제 백엔드(mlx_lm / vLLM / llama.cpp / Groq 등)로 전달합니다.

### 요청 흐름 (`app/services/chat_service.py` 기준)

```
LangGraph Agent
  │  POST /v1/chat/completions  { model: "<profile 이름>", messages: [...] }
  ▼
routers/chat.py
  ▼
chat_service._apply_profile()
  ├─ profiles.yaml에서 프로필 조회 (없으면 "default")
  ├─ system 메시지 없으면 profile.system_prompt 주입 (있으면 덮어쓰지 않음)
  ├─ temperature/max_tokens: 요청에 값 있으면 요청값 우선, 없으면 프로필 기본값
  └─ model/base_url: 프로필에 지정돼 있으면 그 값, 없으면 .env의 LLM_DEFAULT_MODEL/LLM_BASE_URL
  ▼
llm_client.get_backend(base_url)  # base_url별로 백엔드 인스턴스 캐싱
  ▼
OpenAICompatBackend.chat()  →  실제 백엔드로 HTTP POST, 429는 자동 재시도(최대 3회)
```

### 프로필별 백엔드 라우팅 (`app/profiles/profiles.yaml`)

프로필 7개 중 `asker`/`detail_asker`만 `model`+`base_url`을 둘 다 하드코딩(`mlx-community/gemma-4-e4b-it-4bit` @ `localhost:8080`)하고, `elig_reasoner`는 `model: llama-3.3-70b-versatile`만 지정하고 `base_url`은 지정하지 않습니다.

**여기서 실제로 챙겨야 할 부분:** `elig_reasoner`가 정상 동작하려면 `.env`의 `LLM_BASE_URL`이 Groq처럼 `llama-3.3-70b-versatile`를 서빙하는 백엔드를 가리키고 있어야 합니다. `.env.example`의 기본값(`http://localhost:8080`, 로컬 mlx 서버)을 그대로 두면 `elig_reasoner`는 로컬 서버에 존재하지 않는 모델명을 요청해서 실패합니다. 즉 **"짧고 빠른 응답이 필요한 asker류는 항상 로컬, 나머지(interviewer/elig_reasoner/field_extractor/default)는 `.env`가 가리키는 곳"**이 의도된 설계이고, `.env`를 로컬 전용으로 세팅한 채로는 절반만 동작한다는 점을 새 담당자가 인지하고 있어야 합니다.

### 눈에 잘 안 띄는 동시성 제약 (`app/services/backends/openai_compat.py`)

`OpenAICompatBackend`는 인스턴스마다 `self._groq_sem = asyncio.Semaphore(1)`을 갖고 있고, `llm_client.get_backend()`가 `base_url`별로 백엔드를 캐싱해서 재사용합니다. 즉 **같은 `base_url`을 쓰는 모든 요청은 (프로필이 달라도) 한 번에 하나씩만 처리됩니다.** 변수명은 `_groq_sem`이지만 실제로는 Groq 여부와 무관하게 로컬 mlx 서버 호출까지 전부 직렬화됩니다. Groq 429 대응(요청 간격 확보)을 위해 넣은 것으로 보이는데, 로컬 백엔드에 여러 LangGraph 노드가 동시에 요청을 보내면 이 세마포어 때문에 대기가 걸릴 수 있다는 점을 성능 이슈 디버깅 시 염두에 둘 것.

## 2. 환경변수 (`.env`, `app/config.py` 기준)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:8080` | `asker`/`detail_asker`를 제외한 모든 프로필이 쓰는 기본 백엔드 주소. **`elig_reasoner`가 요구하는 모델(`llama-3.3-70b-versatile`)을 실제로 서빙하는 곳으로 맞춰야 함** (위 라우팅 설명 참고). |
| `LLM_DEFAULT_MODEL` | `gemma4:e4b` (예시) / `gemma-4-2b` (config.py 기본값) | 프로필에 `model`이 없을 때만 쓰이는 폴백. 대부분의 프로필은 이미 자체 `model`을 갖고 있어서 실제로는 거의 안 쓰임. |
| `LLM_API_KEY` | (없음, 주석 처리) | 외부 API(Groq 등)를 `LLM_BASE_URL`로 쓸 때만 필요. 로컬 mlx_lm 서버에는 불필요. **Groq를 쓰는 순간 이 값을 채워야 인증 헤더가 실림** — 안 채우면 `Authorization` 헤더 자체가 안 붙어서 401. |
| `LLM_REQUEST_TIMEOUT` | `120`초 | 백엔드 HTTP 타임아웃. `elig_reasoner`/`field_extractor`처럼 `max_tokens`가 큰(4096~8192) 프로필은 응답이 오래 걸릴 수 있어 너무 낮추지 말 것. |
| `APP_HOST` | `0.0.0.0` | |
| `APP_PORT` | `8002` (실질 사용값) | ⚠️ `config.py`의 코드 기본값은 `8000`이지만 `.env.example`/`Makefile`은 전부 `8002`를 씀. `.env` 없이 기본값만으로 띄우면 포트가 달라지니 혼동 주의. |
| `APP_LOG_LEVEL` | `info` | 요청/응답 전체를 로깅하는 미들웨어(`middleware/logging.py`)가 있어서, 민감한 사용자 데이터가 로그에 그대로 찍힐 수 있음(복지 서비스 인터뷰 내용 등) — 운영 환경 로그 보관 정책이 있다면 확인 필요. |

## 3. 알려진 이슈 / 확인 필요 사항

- **테스트 코드 없음.** `pyproject.toml`에 `pytest`/`pytest-asyncio`가 dev 의존성으로 들어있고 `[tool.pytest.ini_options]`까지 설정돼 있는데 실제 테스트 파일은 하나도 없음. CI(`.github/`)에도 테스트 실행 스텝 여부 확인 필요.
- **`asker`/`detail_asker`를 `4bit` 모델로 바꾼 이유가 커밋/PR에 기록 안 됨.** 품질 저하 없는지 실사용 중 체크할 것.

## 4. 다음 담당자를 위한 제안 순서

1. 로컬에서 `.env`의 `LLM_BASE_URL`을 Groq로 맞추고 `elig_reasoner` 프로필이 실제로 정상 호출되는지 (401/모델 없음 에러 없이) 확인.
2. 최소한의 스모크 테스트(프로필 로딩, `_apply_profile` 라우팅 분기)라도 추가하는 것을 고려.

## 5. 향후 방향에 대한 멘토 의견 (중요 — 새 담당자가 판단할 부분)

현재 구조는 `asker`/`detail_asker` 등 일부 프로필은 로컬 LLM(mlx_lm)을, `elig_reasoner` 등 나머지는 `.env`의 `LLM_BASE_URL`을 통해 Groq를 호출하는 이원화 구조입니다. 프로젝트 멘토는 **장기적으로는 Claude API로 통합하는 것을 권장**했습니다.

- 로컬 LLM의 성능/품질 이슈 때문에 Groq를 남겨둔 현재 구조를 그대로 유지할지
- 멘토 권고대로 Claude API로 통합할지
- 아니면 지금처럼 로컬 LLM + Groq 이원화 구조를 유지할지

이 판단은 새로 들어오는 담당자가 멘토와 상의해서 결정해야 하는 사안입니다.
