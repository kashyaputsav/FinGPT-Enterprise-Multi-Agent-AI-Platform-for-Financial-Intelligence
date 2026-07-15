from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness/readiness probe for ECS/ALB")
async def health_check():
    return {"status": "ok"}
