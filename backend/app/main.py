"""
FastAPI application factory.

Run locally with:   uvicorn app.main:app --reload
Run in production:  gunicorn -k uvicorn.workers.UvicornWorker app.main:app
                     (see backend/Dockerfile CMD)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.rag.qdrant_client import ensure_collection

configure_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.ENVIRONMENT)
    await ensure_collection()
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Multi-agent GenAI platform for financial document analysis, fraud "
    "investigation, loan underwriting, compliance review, and financial assistance.",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "local" else [],  # tighten via ALB/CloudFront in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("app_exception", path=request.url.path, detail=exc.detail, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Exposes /metrics for Prometheus/CloudWatch Container Insights scraping.
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
