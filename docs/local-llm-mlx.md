# MLX로 Gemma 4 로컬 실행

Apple Silicon Mac에서 `mlx-lm`을 사용해 Gemma 4 모델을 로컬에서 실행하는 방법입니다.

## 요구 사항

- Apple Silicon Mac (RAM 16GB 이상 권장)
- Python 3.11+

## 1. mlx-lm 설치

```bash
# 별도 디렉토리 생성 및 venv 설정 권장
mkdir ../mlx
cd ../mlx

python3.11 -m venv .venv
source .venv/bin/activate

# mlx-lm 설치
# 260514 기준 mlx-lm==0.31.2 버전 이상에서 gemma-4-e4b-it-8bit 모델 실행 시 오류 발생.
pip3 install mlx-lm==0.31.2
```

## 2. 서버 실행

```bash
mlx_lm.server \
  --model mlx-community/gemma-4-e4b-it-8bit \
  --port 8080 \
  --host 0.0.0.0
```

서버가 뜨면 `http://localhost:8080`에서 OpenAI 호환 API를 제공합니다.

## 3. API 서버 연결

`.env`에서 MLX 서버 주소와 모델명을 맞춰줍니다.

```bash
LLM_BASE_URL=http://localhost:8080
LLM_DEFAULT_MODEL=mlx-community/gemma-4-e4b-it-8bit
```

## 참고

- [mlx-lm GitHub](https://github.com/ml-explore/mlx-examples/tree/main/llms)
- [mlx-community 모델 목록](https://huggingface.co/mlx-community)
