# 설정 레퍼런스

## 환경 변수

| 환경변수 | 기본값 | 설명 |
|---------|--------|------|
| `LLM_BASE_URL` | `http://localhost:8080` | 로컬 LLM 서버 주소 |
| `LLM_DEFAULT_MODEL` | `gemma-4-2b` | 기본 모델명 |
| `LLM_REQUEST_TIMEOUT` | `120` | 요청 타임아웃 (초) |
| `APP_HOST` | `0.0.0.0` | 서버 바인드 주소 |
| `APP_PORT` | `8000` | 서버 포트 |
| `APP_LOG_LEVEL` | `info` | 로그 레벨 |

## 호환 LLM 서버

OpenAI Chat Completions API(`/v1/chat/completions`)를 지원하는 서버라면 모두 연결 가능합니다.

| 서버 | 환경 | 기본 포트 | 실행 예시 |
|------|------|-----------|----------|
| `mlx_lm` | Apple Silicon | 8080 | `python -m mlx_lm.server --model <model> --port 8080` |
| `vllm` | CUDA GPU | 8000 | `python -m vllm.entrypoints.openai.api_server --model <model>` |
| `llama.cpp` | CPU / Metal | 8080 | `llama-server -m <model.gguf> --port 8080` |
