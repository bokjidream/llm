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

```bash
# 로컬 LLM 서버 예시
LLM_BASE_URL=http://localhost:8080
LLM_DEFAULT_MODEL=mlx-community/gemma-4-e4b-it-8bit

# 외부 LLM 서버 예시 (Colab)
LLM_BASE_URL=https://sim-enormous-quarterly-executive.trycloudflare.com
LLM_DEFAULT_MODEL=gemma4:e4b
```

## 4. 로컬 LLM 서버 실행 (예: mlx_lm)

- [mlx_lm 설정 방법](./local-llm-mlx.md)

```bash
mlx_lm.server \
  --model mlx-community/gemma-4-e4b-it-8bit \
  --port 8080 \
  --host 0.0.0.0
```

## 5. API 서버 실행

```bash
make dev
# uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```
