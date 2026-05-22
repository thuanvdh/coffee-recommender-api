import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqladmin import Admin

from app.admin import (
    CoffeeShopAdmin,
    PurposeAdmin,
    SpaceAdmin,
    AmenityAdmin,
    SuggestionAdmin,
    UserAdmin,
    authentication_backend,
)
from app.config import settings
from app.database import engine
from app.routers import shops, suggestions, auth, admin as admin_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 Starting Danang Coffee API v%s", settings.APP_VERSION)
    yield
    logger.info("🛑 Shutting down Danang Coffee API")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API quản lý quán cà phê tại Đà Nẵng",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS - cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shops.router)
app.include_router(suggestions.router)
app.include_router(auth.router)
app.include_router(admin_router.router)

# Admin setup
admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(CoffeeShopAdmin)
admin.add_view(PurposeAdmin)
admin.add_view(SpaceAdmin)
admin.add_view(AmenityAdmin)
admin.add_view(SuggestionAdmin)
admin.add_view(UserAdmin)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a structured error response."""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Đã xảy ra lỗi máy chủ. Vui lòng thử lại sau."},
    )


@app.get("/")
async def root():
    return {
        "message": "Danang Coffee API",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
