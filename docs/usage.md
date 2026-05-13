# 사용 예시

## Python 클라이언트 예시

```python
import json
import httpx

BASE_URL = "http://localhost:8000"


def ask_question(client: httpx.Client, field: str, re_ask: bool, timeout: int,
                 pre_assistant_message: str = "", pre_user_message: str = "") -> str:
    payload: dict = {"information": field, "re_ask": re_ask}
    if pre_assistant_message:
        payload["pre_assistant_message"] = pre_assistant_message
        payload["pre_user_message"] = pre_user_message
    resp = client.post("/v1/chat/completions", json={
        "model": "asker",
        "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    }, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_value(client: httpx.Client, field: str, assistant_message: str,
                  user_message: str, timeout: int) -> dict:
    payload = {
        "information": field,
        "assistant_message": assistant_message,
        "user_message": user_message,
    }
    resp = client.post("/v1/chat/completions", json={
        "model": "interviewer",
        "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    }, timeout=timeout)
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])


with httpx.Client(base_url=BASE_URL) as client:
    question = ask_question(client, "age", re_ask=False, timeout=120)
    result = extract_value(client, "age", question, "저 26살이에요", timeout=120)
    # {"exist": True, "value": 26, "re_ask": False, "reasoning": "..."}
```