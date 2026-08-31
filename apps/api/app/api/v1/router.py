from fastapi import APIRouter

from app.api.v1.routes.birth_profiles import router as birth_profiles_router
from app.api.v1.routes.guest_sessions import router as guest_sessions_router
from app.api.v1.routes.system import router as system_router

router = APIRouter()
router.include_router(system_router, tags=["system"])
router.include_router(guest_sessions_router, tags=["guest"])
router.include_router(birth_profiles_router, tags=["birth-chart"])
