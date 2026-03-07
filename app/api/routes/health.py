from fastapi import APIRouter
from app.core.config import settings
from app.db.mongo import ping_database

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "UP"}


@router.get("/api/v1/health")
def api_health_check():
    return {
        "status": "UP",
        "service": settings.PROJECT_NAME,
    }


@router.get("/api/v1/health/build")
def build_health_check():
    mongo_up = ping_database()
    return {
        "status": "UP" if mongo_up else "DEGRADED",
        "build_ready": mongo_up,
        "mongo": "UP" if mongo_up else "DOWN",
        "service": settings.PROJECT_NAME,
        "build_version": settings.BUILD_VERSION,
    }
