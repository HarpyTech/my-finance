from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api.routes import auth, users, health, expenses
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.csrf import CSRFProtectionMiddleware

app = FastAPI(title=settings.PROJECT_NAME)

# --------------------
# Middleware
# --------------------
# CSRF Protection middleware (must be before authentication)
app.add_middleware(CSRFProtectionMiddleware)

# Authentication & Authorization middleware
app.add_middleware(AuthenticationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

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

app.include_router(
    expenses.router,
    prefix=f"{settings.API_V1_STR}/expenses",
    tags=["Expenses"],
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"
ASSETS_DIR = STATIC_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json", "health"}:
        raise HTTPException(status_code=404, detail="Not Found")

    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)

    return {
        "detail": "Frontend build not found. Run `npm install` and `npm run build` to generate app/static.",
    }
