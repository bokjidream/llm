# 에이전트 프로필

`app/profiles/profiles.yaml`에 에이전트별 시스템 프롬프트와 파라미터 기본값을 정의합니다.

## 프로필 파라미터

현재 지원하는 파라미터는 아래 5개입니다 (`app/profiles/loader.py`의 `Profile` 데이터클래스에 정의).

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `system_prompt` | ✓ | 에이전트에게 부여할 시스템 프롬프트 |
| `temperature` | | 기본 temperature. 요청에서 명시하면 요청 값이 우선 |
| `max_tokens` | | 기본 최대 토큰 수. 요청에서 명시하면 요청 값이 우선 |
| `model` | | 이 프로필 전용 LLM 모델명. 생략 시 `.env`의 `LLM_DEFAULT_MODEL` 사용 |
| `base_url` | | 이 프로필 전용 백엔드 주소. 생략 시 `.env`의 `LLM_BASE_URL` 사용 |

`top_p`, `response_format` 등 다른 파라미터는 프로필에서 설정할 수 없고 요청마다 직접 전달해야 합니다.

`model` / `base_url`을 지정하면 해당 프로필만 다른 LLM 서버·모델로 라우팅됩니다. 예를 들어 `asker`/`detail_asker`는 로컬 mlx_lm 서버(`http://localhost:8080`)의 경량 모델을, `elig_reasoner`는 외부 Groq API의 대형 모델을 쓰도록 각각 지정할 수 있습니다.

## 예시

```yaml
default:
  system_prompt: "당신은 유능한 AI 어시스턴트입니다."
  temperature: 0.7
  max_tokens: 2048

summarizer:
  system_prompt: "당신은 문서 요약 전문가입니다. 핵심만 간결하게 정리하세요."
  temperature: 0.3
  max_tokens: 1024

planner:
  system_prompt: "당신은 작업 계획을 세우는 에이전트입니다. 단계별로 구체적으로 작성하세요."
  temperature: 0.5
  max_tokens: 4096
```

## 동작 규칙

```
요청의 model 필드 → 프로필 이름으로 해석
  ↓
프로필 없음 → "default"로 폴백
  ↓
messages에 system 없음 → system_prompt 맨 앞에 자동 주입
messages에 system 있음 → 덮어쓰지 않음 (그대로 사용)
  ↓
요청에 temperature 명시 → 프로필 값 무시, 요청 값 사용
요청에 temperature 없음 → 프로필 기본값 사용
  ↓
프로필에 model/base_url 지정 → 해당 값으로 실제 백엔드 호출
프로필에 model/base_url 생략 → .env의 LLM_DEFAULT_MODEL / LLM_BASE_URL 사용
```

## LangGraph 에이전트에서 사용 예

```python
# model 필드로 프로필 선택
client.chat.completions.create(
    model="summarizer",   # ← 프로필 이름 지정
    messages=[{"role": "user", "content": "이 문서를 요약해줘: ..."}]
)
```

---

## 프로필별 인터페이스

### `asker`

질문 생성 에이전트. `user` 메시지 본문은 JSON 직렬화된 문자열로 전달합니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `information` | ✓ | 수집할 항목 (아래 항목 목록 참고) |
| `re_ask` | ✓ | 재질문 여부 |
| `pre_assistant_message` | | 직전 봇 발화 (자연스러운 연결용) |
| `pre_user_message` | | 직전 사용자 발화 |

**`information` 항목 목록**

| 항목 | 설명 |
|------|------|
| `age` | 나이 |
| `region` | 거주 지역 (시·군 단위) |
| `household_size` | 가구원 수 |
| `marital_status` | 혼인 상태 |
| `has_children` | 자녀 유무 |
| `disability` | 장애 여부 |
| `disability_severity` | 장애 정도 |
| `employment_status` | 취업 상태 |
| `income_level` | 소득 수준 |

**출력**

질문 텍스트 (plain text).

---

### `interviewer`

사용자 답변에서 값을 추출하는 에이전트. 출력은 JSON 문자열로 반환됩니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `information` | ✓ | 추출할 항목 |
| `assistant_message` | ✓ | 봇이 했던 질문 |
| `user_message` | ✓ | 사용자 답변 |

**출력 필드**

| 필드 | 설명 |
|------|------|
| `exist` | 값 추출 성공 여부 |
| `value` | 추출값 (`exist=false`면 `null`) |
| `re_ask` | 재질문 필요 여부 |
| `reasoning` | 판단 근거 |

**`information` 항목별 `value` 타입**

| 항목 | 타입 | 값 범위 |
|------|------|---------|
| `age` | int | 나이 |
| `region` | string | 시·군 단위 (예: `"수원시"`) |
| `household_size` | int | 가구원 수 |
| `marital_status` | enum | `"미혼"` `"기혼"` `"이혼"` `"사별"` |
| `has_children` | bool | `true` / `false` |
| `disability` | bool | `true` / `false` |
| `disability_severity` | enum | `"경증"` `"중증"` |
| `employment_status` | enum | `"취업"` `"실업"` `"비경제활동"` |
| `income_level` | enum | `"기초생활수급자"` `"차상위계층"` `"저소득"` `"일반"` |

---

### `field_extractor`

서비스 수급 조건을 분석해 기본 항목(`asker`/`interviewer`가 수집하는 9개 필드)으로 커버되지 않는 추가 필드를 추출하는 에이전트. 출력은 JSON 문자열로 반환됩니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `service.serv_nm` | ✓ | 서비스명 |
| `service.tgtr_dtl_cn` | ✓ | 지원 대상 상세 |
| `service.slct_crit_cn` | ✓ | 선정 기준 |
| `service.trgter_indvdl` | ✓ | 대상자 유형 배열 |

**출력 필드 (`extra_fields` 배열의 각 항목)**

| 필드 | 설명 |
|------|------|
| `key` | snake_case 식별자 |
| `label` | 한국어 명칭 |
| `type` | `"bool"` `"enum"` (수치 조건도 bool/enum으로 변환되어 반환됨) |
| `enum_values` | `type=enum`일 때만 포함 |
| `question_hint` | `detail_asker`에게 전달할 질문 방향 힌트 |
| `reason` | 해당 정보가 필요한 이유 |

추가 필드가 없으면 `{"extra_fields": []}` 반환.

---

### `detail_asker`

`field_extractor`가 추출한 추가 필드에 대해 질문을 생성하는 에이전트. `asker`와 역할은 같지만 입력 구조가 다릅니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `field` | ✓ | `field_extractor`가 반환한 필드 객체 전체 |
| `re_ask` | ✓ | 재질문 여부 |
| `pre_assistant_message` | | 직전 봇 발화 |
| `pre_user_message` | | 직전 사용자 발화 |

**출력**

질문 텍스트 (plain text).

---

### `detail_interviewer`

`detail_asker`의 질문에 대한 사용자 답변에서 추가 필드 값을 추출하는 에이전트. `interviewer`와 역할은 같지만 `information` 대신 `field` 객체를 받습니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `field` | ✓ | `field_extractor`가 반환한 필드 객체 전체 |
| `assistant_message` | ✓ | 봇이 했던 질문 |
| `user_message` | ✓ | 사용자 답변 |

**출력 필드**

| 필드 | 설명 |
|------|------|
| `exist` | 값 추출 성공 여부 |
| `value` | 추출값 (`exist=false`면 `null`). 타입은 `field.type`을 따름 |
| `re_ask` | 재질문 필요 여부 |
| `reasoning` | 판단 근거 |

---

### `elig_reasoner`

복지 서비스 추천 근거를 설명하는 에이전트. 사용자 정보와 서비스 데이터를 받아 추천 이유를 한 문장으로 반환합니다.

**입력 필드**

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `user` | ✓ | 수집된 사용자 정보 전체 (아래 항목 참고) |
| `service.serv_nm` | ✓ | 서비스명 |
| `service.serv_dgst` | ✓ | 서비스 개요 |
| `service.trgterIndvdlArray` | ✓ | 대상자 키워드 (예: `"저소득,노인"`) |

**`user` 항목**

| 항목 | 타입 |
|------|------|
| `age` | int |
| `region` | string |
| `household_size` | int |
| `marital_status` | enum (`"미혼"` `"기혼"` `"이혼"` `"사별"`) |
| `has_children` | bool |
| `disability` | bool |
| `disability_severity` | enum (`"경증"` `"중증"`) 또는 `null` |
| `employment_status` | enum (`"취업"` `"실업"` `"비경제활동"`) |
| `income_level` | enum (`"기초생활수급자"` `"차상위계층"` `"저소득"` `"일반"`) |

**출력**

추천 이유 한 문장 (plain text).
