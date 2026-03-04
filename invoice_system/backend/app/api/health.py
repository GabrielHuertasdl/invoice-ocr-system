"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text
from app.services.storage.database import engine

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check():
    """Return service liveness and basic DB connectivity status."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}
