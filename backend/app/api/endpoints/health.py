from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }