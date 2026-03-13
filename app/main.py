from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import shops, suggestions, auth, admin as admin_router
from app.database import engine
from app.admin import CoffeeShopAdmin, PurposeAdmin, SpaceAdmin, AmenityAdmin, SuggestionAdmin, UserAdmin
from sqladmin import Admin

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API quản lý quán cà phê tại Đà Nẵng",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
from app.admin import authentication_backend
admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(CoffeeShopAdmin)
admin.add_view(PurposeAdmin)
admin.add_view(SpaceAdmin)
admin.add_view(AmenityAdmin)
admin.add_view(SuggestionAdmin)
admin.add_view(UserAdmin)


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
