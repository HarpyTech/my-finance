from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, users, health, web

app = FastAPI(title=settings.PROJECT_NAME)

# --------------------
# Middleware
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# --------------------
# HTML Routes
# --------------------
app.include_router(web.router, tags=["Web"])

# --------------------
# API Routes
# --------------------
app.include_router(health.router, tags=["Health"])

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Auth"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)
