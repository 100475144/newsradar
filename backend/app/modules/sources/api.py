"""Sources API setup for Sprint 1 auth preparation."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user


router = APIRouter(
	prefix="/sources",
	tags=["sources"],
	dependencies=[Depends(get_current_user)],
)
