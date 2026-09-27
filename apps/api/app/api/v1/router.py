from fastapi import APIRouter

from app.api.v1.routes.birth_profiles import router as birth_profiles_router
from app.api.v1.routes.daily_notes import router as daily_notes_router
from app.api.v1.routes.guest_sessions import router as guest_sessions_router
from app.api.v1.routes.identity import router as identity_router
from app.api.v1.routes.insights import router as insights_router
from app.api.v1.routes.la_chung import public_router as la_chung_public_router
from app.api.v1.routes.la_chung import router as la_chung_router
from app.api.v1.routes.matching import router as matching_router
from app.api.v1.routes.radar import public_router as radar_public_router
from app.api.v1.routes.radar import router as radar_router
from app.api.v1.routes.saved_notes import router as saved_notes_router
from app.api.v1.routes.share_artifacts import router as share_artifacts_router
from app.api.v1.routes.system import router as system_router
from app.api.v1.routes.tarot import router as tarot_router

router = APIRouter()
router.include_router(system_router, tags=["system"])
router.include_router(guest_sessions_router, tags=["guest"])
router.include_router(identity_router, tags=["identity"])
router.include_router(birth_profiles_router, tags=["birth-chart"])
router.include_router(insights_router, tags=["insights"])
router.include_router(la_chung_router, tags=["la-chung"])
router.include_router(la_chung_public_router, tags=["la-chung-public"])
router.include_router(matching_router, tags=["matching"])
router.include_router(radar_router, tags=["radar"])
router.include_router(radar_public_router, tags=["radar-public"])
router.include_router(daily_notes_router, tags=["daily-note"])
router.include_router(saved_notes_router, tags=["saved-notes"])
router.include_router(share_artifacts_router, tags=["share"])
router.include_router(tarot_router, tags=["tarot"])
