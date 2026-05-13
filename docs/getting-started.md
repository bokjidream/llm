# 빠른 시작

## 1. 설치

```bash
make install
# pip install -e ".[dev]"
```

## 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 LLM 서버 주소와 모델을 설정합니다.

```bash
LLM_BASE_URL=http://localhost:8080
LLM_DEFAULT_MODEL=gemma-4-2b
```

## 3. 로컬 LLM 서버 실행 (예: mlx_lm)

```bash
python -m mlx_lm.server --model mlx-community/gemma-3-4b-it-8bit --port 8080
```

## 4. API 서버 실행

```bash
make dev
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
