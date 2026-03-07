from fastapi import APIRouter
import logging

from app.core.config import settings
from app.db.mongo import ping_database

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    """Basic health check"""
    logger.debug("Basic health check requested")
    return {"status": "UP"}


@router.get("/api/v1/health")
def api_health_check():
    """API health check"""
    logger.debug("API health check requested")
    return {
        "status": "UP",
        "service": settings.PROJECT_NAME,
    }


@router.get("/api/v1/health/build")
def build_health_check():
    """Detailed health check including database connectivity"""
    logger.info("Build health check requested")
    try:
        mongo_up = ping_database()
        if mongo_up:
            logger.info("Health check: All systems operational")
        else:
            logger.warning("Health check: MongoDB is DOWN")
        return {
            "status": "UP" if mongo_up else "DEGRADED",
            "build_ready": mongo_up,
            "mongo": "UP" if mongo_up else "DOWN",
            "service": settings.PROJECT_NAME,
            "build_version": settings.BUILD_VERSION,
        }
    except Exception as exc:
        logger.error(f"Health check failed with error: {str(exc)}", exc_info=True)
        return {
            "status": "DOWN",
            "build_ready": False,
            "mongo": "ERROR",
            "service": settings.PROJECT_NAME,
            "build_version": settings.BUILD_VERSION,
            "error": str(exc),
        }
