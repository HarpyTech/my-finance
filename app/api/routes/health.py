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


@router.get("/health/mongo", tags=["health"])
def health_check_mongo():
    """Simple health check for MongoDB connection"""
    logger.debug("MongoDB health check requested")
    mongo_up = ping_database()
    return {"mongo": "UP" if mongo_up else "DOWN"}
