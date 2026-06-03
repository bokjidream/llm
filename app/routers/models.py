from fastapi import APIRouter, HTTPException

from app.schemas.models import ModelList
from app.services import llm_client

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models", response_model=ModelList)
async def list_models() -> ModelList:
    try:
        return await llm_client.list_models()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {e}") from e
