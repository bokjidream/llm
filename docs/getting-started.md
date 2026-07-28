# 빠른 시작

## 1. 가상 환경 설정

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 2. 설치

```bash
make install
# pip3 install -e ".[dev]"
```

## 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 LLM 서버 주소와 모델을 설정합니다.

**로컬 LLM 서버 (mlx_lm / llama.cpp 등)**

```bash
LLM_BASE_URL=http://localhost:8080
LLM_DEFAULT_MODEL=mlx-community/gemma-4-e4b-it-8bit
```

**외부 API 사용 (Groq 등)**

```bash
LLM_BASE_URL=https://api.groq.com/openai
LLM_DEFAULT_MODEL=qwen/qwen3-32b
LLM_API_KEY=your_api_key_here
```

## 4. API 서버 실행

```bash
make dev
# uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload --reload-include '*.yaml'
```
