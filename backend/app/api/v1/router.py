from fastapi import APIRouter

from app.api.v1 import agents, auth, documents, fraud, health, underwriting

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(agents.router)
api_router.include_router(fraud.router)
api_router.include_router(underwriting.router)
