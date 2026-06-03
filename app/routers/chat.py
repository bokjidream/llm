from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions", response_model=None)
async def chat_completions(request: ChatRequest) -> ChatResponse | StreamingResponse:
    try:
        if request.stream:
            return StreamingResponse(
                chat_service.chat_stream(request),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        return await chat_service.chat(request)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {e}") from e
