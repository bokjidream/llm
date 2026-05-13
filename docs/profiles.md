# 에이전트 프로필

`app/profiles/profiles.yaml`에 에이전트별 시스템 프롬프트와 파라미터 기본값을 정의합니다.

## 프로필 파라미터

현재 지원하는 파라미터는 아래 3개입니다 (`app/profiles/loader.py`의 `Profile` 데이터클래스에 정의).

| 파라미터 | 필수 | 설명 |
|---------|:----:|------|
| `system_prompt` | ✓ | 에이전트에게 부여할 시스템 프롬프트 |
| `temperature` | | 기본 temperature. 요청에서 명시하면 요청 값이 우선 |
| `max_tokens` | | 기본 최대 토큰 수. 요청에서 명시하면 요청 값이 우선 |

`top_p`, `response_format` 등 다른 파라미터는 프로필에서 설정할 수 없고 요청마다 직접 전달해야 합니다.

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
