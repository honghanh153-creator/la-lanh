"""POST /v1/session/data-export: the owner's own data as a private JSON file.

POST, not GET: the file is a bulk disclosure, so it takes the same proofs as a mutation (session
cookie, X-CSRF-Token and a trusted Origin, or the native client marker). A cross-site link,
prefetcher or crawler therefore cannot make a browser fetch it. The admission middleware limits
the rate per peer and globally. The private-response middleware already marks every /v1 response
``no-store``; this route repeats it with ``Pragma: no-cache``, ``nosniff`` and a fixed,
non-identifying attachment name. Nothing in the file is logged.
"""

from typing import Annotated, cast

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse

from app.domains.data_export.errors import DataExportBusy
from app.domains.data_export.models import DataExport
from app.domains.data_export.service import DataExportService
from app.domains.guest.errors import GuestDomainError
from app.domains.guest.service import GuestSessionService
from app.infrastructure.csrf import require_trusted_origin, trusted_origins

router = APIRouter()

EXPORT_FILENAME = "la-lanh-du-lieu-cua-toi.json"
EXPORT_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _problem(error: GuestDomainError | DataExportBusy) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "type": "about:blank",
            "title": "Data export request was rejected",
            "status": error.status_code,
            "code": error.code,
        },
        headers=EXPORT_HEADERS,
        media_type="application/problem+json",
    )


@router.post(
    "/session/data-export",
    response_model=DataExport,
    responses={401: {}, 403: {}, 409: {}, 429: {}},
)
async def export_my_data(
    request: Request,
    response: Response,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> DataExport | Response:
    settings = request.app.state.settings
    try:
        require_trusted_origin(request, trusted_origins(request))
        guest = await cast(
            GuestSessionService, request.app.state.guest_session_service
        ).verify_csrf(request.cookies.get(settings.guest_cookie_name), csrf_token)
        export = await cast(DataExportService, request.app.state.data_export_service).export(
            guest.id
        )
    except (GuestDomainError, DataExportBusy) as error:
        return _problem(error)
    response.headers.update(EXPORT_HEADERS)
    response.headers["Content-Disposition"] = f'attachment; filename="{EXPORT_FILENAME}"'
    return export
