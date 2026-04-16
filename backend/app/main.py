from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.core.config import settings
from app.core.database import init_db, engine

# Import all API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.debtors import router as debtors_router
from app.api.h5 import router as h5_router
from app.api.h5_auth import router as h5_auth_router
from app.api.partner import router as partner_router
from app.api.partners import router as partners_router
from app.api.captcha import router as captcha_router
from app.api.batches import router as batches_router
from app.api.channels import router as channels_router
from app.api.config_endpoints import router as config_router
from app.api.vouchers import router as vouchers_router
from app.api.import_endpoints import router as import_router
from app.api.partner_api import router as partner_api_router
from app.api.admin_auth import router as admin_auth_router
from app.api.sms import router as sms_router
from app.api.sms_templates import router as sms_templates_router
from app.api.sms_tasks import router as sms_tasks_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting up {settings.APP_NAME} v{settings.VERSION}...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    yield
    logger.info("Shutting down...")
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Debtor Payment Account Query System - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Mount all routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(debtors_router, prefix="/api")
app.include_router(h5_router, prefix="/api")
app.include_router(h5_auth_router, prefix="/api")
app.include_router(partner_router, prefix="/api")
app.include_router(partners_router, prefix="/api")
app.include_router(captcha_router, prefix="/api")
app.include_router(batches_router, prefix="/api")
app.include_router(channels_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(vouchers_router, prefix="/api")
app.include_router(import_router, prefix="/api")
app.include_router(partner_api_router, prefix="/api")
app.include_router(admin_auth_router, prefix="/api")
app.include_router(sms_router, prefix="/api")
app.include_router(sms_templates_router, prefix="/api")
app.include_router(sms_tasks_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
