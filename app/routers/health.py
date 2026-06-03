from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services import llm_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    backend_ok = await llm_client.health()
    status = "ok" if backend_ok else "degraded"
    return JSONResponse(
        content={"status": status, "backend": status},
        status_code=200 if backend_ok else 503,
    )
