"""Builds the owner's own data file ("Tải dữ liệu của tôi").

The caller has already proven ownership of the guest session (cookie + CSRF + trusted origin).
Every query below is scoped to that guest, or to the principal whose ``source_guest_id`` is that
guest. Nothing is cached and nothing is logged: the file is assembled from a fresh read and
returned once.

Inventory, inclusions and exclusions: docs/plans/2026-10-29-privacy-export-and-b-rights.md.
"""

import json
from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.accounts.tables import AccountDeviceRow, AccountRow
from app.domains.astro.models import DateOnlySunResult
from app.domains.birth.models import BirthSnapshotRecord, BirthSupplementStored
from app.domains.birth.repository import BirthRepository
from app.domains.daily.postgres import _content as daily_content
from app.domains.daily.tables import DailyNoteRow
from app.domains.data_export.errors import DataExportBusy
from app.domains.data_export.models import (
    MAX_ITEMS_PER_SECTION,
    DataExport,
    ExportAccount,
    ExportBirthProfile,
    ExportConsent,
    ExportDailyExperiment,
    ExportDailyNote,
    ExportDevice,
    ExportHistoryRetention,
    ExportLaChungInvite,
    ExportMatching,
    ExportMatchingProfile,
    ExportNoteFeedback,
    ExportProfile,
    ExportRadarReceived,
    ExportRadarSent,
    ExportReadingEvidence,
    ExportReadingSections,
    ExportSavedNote,
    ExportSavedReading,
    ExportShareLink,
    ExportTarotCard,
    ExportTarotPosition,
    ExportTarotReading,
    ExportTarotSession,
)
from app.domains.experiments.postgres import _payload_context as experiment_context
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.errors import GuestExpired
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.history.postgres import unavailable_daily
from app.domains.history.tables import HistoryRetentionPolicyRow
from app.domains.identity.tables import PrincipalRow
from app.domains.la_chung.tables import LaChungRequestRow, LaChungResponseRow
from app.domains.matching.tables import (
    MatchingConsentRow,
    MatchingProfileRow,
    MatchingVerificationRow,
)
from app.domains.mood.tables import MoodCheckInRow
from app.domains.radar.models import RadarStatus
from app.domains.radar.service import RECEIPT_TTL
from app.domains.radar.tables import RadarRequestRow
from app.domains.readings.application import _content_projection as content_projection
from app.domains.readings.models import ReadingContentProjection, ReadingPurpose
from app.domains.readings.postgres import _projection_record as projection_record
from app.domains.readings.postgres import _revision_record as revision_record
from app.domains.readings.tables import ReadingProjectionRow, ReadingRevisionRow
from app.domains.resonance.postgres import _payload_context as resonance_context
from app.domains.resonance.tables import ResonanceFeedbackRow
from app.domains.saved.postgres import _snapshot_payload as saved_snapshot
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow
from app.domains.tarot.models import TarotSessionView
from app.domains.tarot.service import TarotSessionService
from app.infrastructure.crypto import EnvelopeCipher

NOTICE = (
    "Đây là bản sao dữ liệu Lá Lành đang giữ cho hồ sơ của bạn, tại thời điểm tải. "
    "Tệp chứa ngày sinh và có thể có giờ sinh, nơi sinh: hãy cất ở nơi riêng tư và "
    "đừng gửi cho người khác nếu bạn không muốn họ biết. Tệp không có mật khẩu, "
    "khoá đăng nhập hay link chia sẻ, và không chứa dữ liệu sinh của người khác."
)

NOT_INCLUDED = (
    "Mã phiên, khoá CSRF, mã đăng nhập, mã link chia sẻ và receipt: là chìa khoá truy cập, "
    "không phải nội dung; tệp không mang chúng để không ai dùng tệp mở được hồ sơ của bạn.",
    "Kết quả Hợp gu (Radar) và câu trả lời Lá Chứng: có dữ liệu suy ra từ người khác; tệp chỉ "
    "ghi phần của bạn (biệt danh bạn đặt, bối cảnh, trạng thái, thời hạn). Bạn vẫn xem kết quả "
    "trong app khi còn hạn.",
    "Ngày, giờ, nơi sinh của người khác: không được lưu thành hồ sơ nên không có để xuất.",
    "Tọa độ trung tâm thành phố nơi sinh: là dữ liệu danh mục suy từ nơi bạn chọn; tệp ghi "
    "tên nơi sinh và múi giờ.",
    "Note ngày đã quá hạn hiển thị, Tarot đã hết hạn và lời mời đã hết hạn/rút: đang chờ "
    "dọn và không còn mở được trong app.",
    "Bản nháp xử lý nội bộ (kế hoạch bản đọc, bản sửa, hàng đợi AI viết lại, nhật ký xoá): "
    "là dữ liệu kỹ thuật; nội dung bạn đã thấy nằm trong note, Tarot và note đã lưu.",
)


# A birth change landing during assembly re-reads the birth section; more than this many in a row
# answer 409 so the client can ask again.
_BIRTH_RETRIES = 3


class DataExportService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        envelope: EnvelopeCipher,
        birth_repository: BirthRepository,
        tarot: TarotSessionService,
        *,
        max_items: int = MAX_ITEMS_PER_SECTION,
    ) -> None:
        self._sessions = sessions
        self._envelope = envelope
        self._birth = birth_repository
        self._tarot = tarot
        self._max_items = max_items

    async def export(self, guest_id: UUID, *, now: datetime | None = None) -> DataExport:
        current = now or datetime.now(UTC)
        truncated: list[str] = []
        birth_profile, birth_key = await self._birth_profile(guest_id)
        tarot_views = await self._tarot.export_views(
            guest_id, limit=self._max_items + 1, now=current
        )
        tarot_sessions = [
            _tarot(view) for view in self._bound(tarot_views, "tarot_sessions", truncated)
        ]
        async with self._sessions() as session:
            guest = await session.get(GuestSessionRow, guest_id)
            if guest is None:
                raise GuestExpired
            principal_id = await session.scalar(
                select(PrincipalRow.id).where(PrincipalRow.source_guest_id == guest_id)
            )
            account = await self._account(session, guest_id, truncated)
            consents = await self._consents(session, guest_id, truncated)
            history_retention = await self._history(session, guest_id)
            daily_notes = await self._daily_notes(session, guest_id, current, truncated)
            saved_notes = await self._saved_notes(session, guest_id, truncated)
            share_links = await self._share_links(session, guest_id, current, truncated)
            note_feedback = await self._feedback(session, guest_id, current, truncated)
            daily_experiments = await self._experiments(session, guest_id, current, truncated)
            radar_sent = (
                await self._radar_sent(session, principal_id, current, truncated)
                if principal_id is not None
                else []
            )
            radar_received = await self._radar_received(session, guest_id, current, truncated)
            la_chung_invites = (
                await self._la_chung(session, principal_id, current, truncated)
                if principal_id is not None
                else []
            )
            matching = (
                await self._matching(session, principal_id, truncated)
                if principal_id is not None
                else None
            )
        # Codex r55: a time/place removal (or any birth change) that committed while the file was
        # being assembled must not leave the erased precision or its chart in the file. The birth
        # section is re-read until its revision held from read to end of assembly.
        for _ in range(_BIRTH_RETRIES):
            if await self._birth_key(guest_id) == birth_key:
                break
            birth_profile, birth_key = await self._birth_profile(guest_id)
        else:
            raise DataExportBusy
        return DataExport(
            generated_at=current,
            notice=NOTICE,
            profile=ExportProfile(
                state=guest.state,
                onboarding_status=guest.onboarding_status,
                created_at=guest.created_at,
                last_active_at=guest.last_active_at,
                expires_at=guest.expires_at,
            ),
            birth_profile=birth_profile,
            tarot_sessions=tarot_sessions,
            account=account,
            consents=consents,
            history_retention=history_retention,
            daily_notes=daily_notes,
            saved_notes=saved_notes,
            share_links=share_links,
            note_feedback=note_feedback,
            daily_experiments=daily_experiments,
            radar_sent=radar_sent,
            radar_received=radar_received,
            la_chung_invites=la_chung_invites,
            matching=matching,
            not_included=list(NOT_INCLUDED),
            truncated=truncated,
        )

    def _bound[T](self, items: tuple[T, ...] | list[T], name: str, truncated: list[str]) -> list[T]:
        if len(items) > self._max_items:
            truncated.append(name)
        return list(items[: self._max_items])

    async def _rows[T](
        self, session: AsyncSession, query: Select[tuple[T]], name: str, truncated: list[str]
    ) -> list[T]:
        rows = tuple(await session.scalars(query.limit(self._max_items + 1)))
        return self._bound(rows, name, truncated)

    def _json(self, envelope: str, context: bytes) -> dict[str, Any]:
        payload = json.loads(self._envelope.decrypt(envelope, context=context))
        if not isinstance(payload, dict):
            raise ValueError("invalid encrypted export payload")
        return cast(dict[str, Any], payload)

    async def _birth_key(self, guest_id: UUID) -> tuple[UUID, datetime | None] | None:
        """Which chart is current and the profile revision it belongs to (a time, no content)."""

        snapshot = await self._birth.find_current(guest_id)
        return (snapshot.id, snapshot.profile_revision) if snapshot is not None else None

    async def _birth_profile(
        self, guest_id: UUID
    ) -> tuple[ExportBirthProfile | None, tuple[UUID, datetime | None] | None]:
        """The chart and the time/place layer from one profile revision (Codex r55).

        Two reads that straddle a removal would pair a time-derived chart with cleared fields.
        The pair is accepted only when the supplement carries the chart's profile revision and the
        current chart did not move meanwhile.
        """

        for _ in range(_BIRTH_RETRIES):
            snapshot = await self._birth.find_current(guest_id)
            if snapshot is None:
                return None, None
            supplement = await self._birth.find_supplement(guest_id)
            key = (snapshot.id, snapshot.profile_revision)
            if (
                supplement is not None
                and supplement.updated_at == snapshot.profile_revision
                and await self._birth_key(guest_id) == key
            ):
                return self._birth_section(guest_id, snapshot, supplement), key
        raise DataExportBusy

    def _birth_section(
        self, guest_id: UUID, snapshot: BirthSnapshotRecord, supplement: BirthSupplementStored
    ) -> ExportBirthProfile:
        birth_date = self._envelope.decrypt(
            snapshot.birth_date_ciphertext, context=f"birth-date:{guest_id}".encode()
        ).decode()
        time_mode, local_time, window = "unknown", None, None
        place_name, timezone_id = None, None
        if supplement.birth_time_ciphertext:
            raw_time = self._envelope.decrypt(
                supplement.birth_time_ciphertext, context=f"birth-time:{guest_id}".encode()
            ).decode()
            time_mode, value = raw_time.split(":", maxsplit=1)
            if time_mode == "exact":
                local_time = value
            elif time_mode == "approx_window":
                window = value or None
        if supplement.birth_place_ciphertext:
            raw_place = self._envelope.decrypt(
                supplement.birth_place_ciphertext, context=f"birth-place:{guest_id}".encode()
            ).decode()
            # place_id|display name|timezone|latitude|longitude: the catalog centroid stays out.
            _, place_name, timezone_id, _, _ = raw_place.split("|", maxsplit=4)
        return ExportBirthProfile(
            birth_date=date.fromisoformat(birth_date),
            profile_level=supplement.profile_level,
            time_precision=supplement.time_precision,
            birth_time_mode=time_mode,
            birth_time_local=local_time,
            approx_window=window,
            place_display_name=place_name,
            timezone_id=timezone_id,
            supplement_consent_version=supplement.supplement_consent_version,
            calculated_at=snapshot.created_at,
            calculation_kind=(
                "date_only_sun" if isinstance(snapshot.result, DateOnlySunResult) else "natal_chart"
            ),
            calculation=snapshot.result,
        )

    async def _account(
        self, session: AsyncSession, guest_id: UUID, truncated: list[str]
    ) -> ExportAccount | None:
        account = await session.scalar(select(AccountRow).where(AccountRow.guest_id == guest_id))
        if account is None:
            return None
        devices = await self._rows(
            session,
            select(AccountDeviceRow)
            .where(AccountDeviceRow.guest_id == guest_id)
            .order_by(AccountDeviceRow.created_at.desc(), AccountDeviceRow.id),
            "account.devices",
            truncated,
        )
        return ExportAccount(
            masked_email=account.masked_email,
            linked_at=account.created_at,
            devices=[
                ExportDevice(
                    created_at=row.created_at,
                    last_active_at=row.last_active_at,
                    expires_at=row.expires_at,
                    revoked_at=row.revoked_at,
                )
                for row in devices
            ],
        )

    async def _consents(
        self, session: AsyncSession, guest_id: UUID, truncated: list[str]
    ) -> list[ExportConsent]:
        rows = await self._rows(
            session,
            select(ConsentRow)
            .where(ConsentRow.guest_id == guest_id)
            .order_by(ConsentRow.accepted_at.desc(), ConsentRow.id),
            "consents",
            truncated,
        )
        return [
            ExportConsent(
                purpose=row.purpose,
                version=row.version,
                accepted_at=row.accepted_at,
                revoked_at=row.revoked_at,
            )
            for row in rows
        ]

    @staticmethod
    async def _history(session: AsyncSession, guest_id: UUID) -> ExportHistoryRetention | None:
        row = await session.get(HistoryRetentionPolicyRow, guest_id)
        if row is None:
            return None
        return ExportHistoryRetention(
            consent_version=row.consent_version, activated_at=row.activated_at
        )

    async def _daily_notes(
        self, session: AsyncSession, guest_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportDailyNote]:
        # Same visibility as the app: notes past their history window are hidden and pending
        # cleanup, so the file does not resurrect what the person was told is gone.
        rows = await self._rows(
            session,
            select(DailyNoteRow)
            .where(DailyNoteRow.guest_id == guest_id, ~unavailable_daily(now))
            .order_by(DailyNoteRow.note_date.desc(), DailyNoteRow.created_at.desc()),
            "daily_notes",
            truncated,
        )
        moods = {
            mood.daily_note_id: mood
            for mood in await session.scalars(
                select(MoodCheckInRow).where(
                    MoodCheckInRow.guest_id == guest_id,
                    MoodCheckInRow.daily_note_id.in_([row.id for row in rows]),
                )
            )
        }
        readings = await self._visible_daily_readings(session, guest_id, rows)
        notes: list[ExportDailyNote] = []
        for row in rows:
            content = daily_content(row, self._envelope)
            mood = moods.get(row.id)
            notes.append(
                ExportDailyNote(
                    note_date=row.note_date,
                    title=str(content["title"]),
                    body=str(content["body"]),
                    full_body=str(content["full_body"]),
                    context_label=str(content["context_label"]),
                    persona_mode=row.persona_mode,
                    persona_label=row.persona_label,
                    created_at=row.created_at,
                    mood=mood.mood if mood is not None else None,
                    mood_checked_in_at=mood.checked_in_at if mood is not None else None,
                    readings=readings.get(row.note_date, []),
                )
            )
        return notes

    async def _visible_daily_readings(
        self, session: AsyncSession, guest_id: UUID, notes: list[DailyNoteRow]
    ) -> dict[date, list[ExportSavedReading]]:
        """The Daily reading text the person sees: the active revision of each visible note's
        projection (Codex r55). Never an available draft, an id, a key or evaluation metadata, and
        nothing is generated here."""

        dates = {row.note_date for row in notes}
        if not dates:
            return {}
        pairs = await session.execute(
            select(ReadingProjectionRow, ReadingRevisionRow)
            .join(
                ReadingRevisionRow,
                (ReadingRevisionRow.id == ReadingProjectionRow.active_revision_id)
                & (ReadingRevisionRow.guest_id == ReadingProjectionRow.guest_id),
            )
            .where(
                ReadingProjectionRow.guest_id == guest_id,
                ReadingProjectionRow.purpose == ReadingPurpose.DAILY_NOTE.value,
                ReadingProjectionRow.local_date.in_(dates),
            )
            .order_by(ReadingProjectionRow.local_date.desc(), ReadingProjectionRow.created_at)
        )
        found: dict[date, list[ExportSavedReading]] = {}
        for projection_row, revision_row in pairs.tuples():
            if projection_row.local_date is None:
                continue
            content = content_projection(
                revision_record(revision_row, self._envelope), projection_record(projection_row)
            )
            found.setdefault(projection_row.local_date, []).append(_reading(content))
        return found

    async def _saved_notes(
        self, session: AsyncSession, guest_id: UUID, truncated: list[str]
    ) -> list[ExportSavedNote]:
        rows = await self._rows(
            session,
            select(SavedNoteRow)
            .where(SavedNoteRow.guest_id == guest_id)
            .order_by(SavedNoteRow.saved_at.desc()),
            "saved_notes",
            truncated,
        )
        saved: list[ExportSavedNote] = []
        for row in rows:
            payload = saved_snapshot(row, self._envelope)
            note = payload.get("note_snapshot")
            note = cast(dict[str, object], note) if isinstance(note, dict) else {}
            raw_reading = payload.get("reading_snapshot")
            reading = None
            if raw_reading is not None:
                reading = _reading(ReadingContentProjection.model_validate(raw_reading))
            saved.append(
                ExportSavedNote(
                    saved_at=row.saved_at,
                    note_date=_text(note.get("note_date")),
                    title=_text(note.get("title")),
                    body=_text(note.get("body")),
                    full_body=_text(note.get("full_body")),
                    context_label=_text(note.get("context_label")),
                    persona_label=_text(note.get("persona_label")),
                    reading=reading,
                )
            )
        return saved

    async def _share_links(
        self, session: AsyncSession, guest_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportShareLink]:
        rows = await self._rows(
            session,
            select(ShareArtifactRow)
            .where(ShareArtifactRow.guest_id == guest_id)
            .order_by(ShareArtifactRow.created_at.desc()),
            "share_links",
            truncated,
        )
        return [
            ExportShareLink(
                format=row.format,
                status=(
                    "revoked"
                    if row.revoked_at is not None
                    else "expired"
                    if row.expires_at <= now
                    else "active"
                ),
                created_at=row.created_at,
                expires_at=row.expires_at,
                revoked_at=row.revoked_at,
            )
            for row in rows
        ]

    async def _feedback(
        self, session: AsyncSession, guest_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportNoteFeedback]:
        rows = await self._rows(
            session,
            select(ResonanceFeedbackRow)
            .where(
                ResonanceFeedbackRow.guest_id == guest_id,
                ResonanceFeedbackRow.expires_at > now,
            )
            .order_by(ResonanceFeedbackRow.created_at.desc()),
            "note_feedback",
            truncated,
        )
        feedback: list[ExportNoteFeedback] = []
        for row in rows:
            payload = self._json(row.payload_ciphertext, resonance_context(row.id))
            lens = payload.get("background_lens")
            feedback.append(
                ExportNoteFeedback(
                    choice=str(payload["choice"]),
                    background_lens=str(lens) if lens is not None else None,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                )
            )
        return feedback

    async def _experiments(
        self, session: AsyncSession, guest_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportDailyExperiment]:
        rows = await self._rows(
            session,
            select(DailyExperimentRow)
            .where(DailyExperimentRow.guest_id == guest_id, DailyExperimentRow.expires_at > now)
            .order_by(DailyExperimentRow.created_at.desc()),
            "daily_experiments",
            truncated,
        )
        experiments: list[ExportDailyExperiment] = []
        for row in rows:
            # The stored action key is an opaque digest of catalog copy, not the person's data.
            payload = self._json(row.payload_ciphertext, experiment_context(row.id))
            outcome = payload.get("outcome")
            experiments.append(
                ExportDailyExperiment(
                    state=row.state,
                    background_lens=str(payload["background_lens"]),
                    outcome=str(outcome) if outcome is not None else None,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    reflected_at=row.reflected_at,
                )
            )
        return experiments

    async def _radar_sent(
        self, session: AsyncSession, principal_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportRadarSent]:
        # Only requests A can still open or act on; the result prose is never copied out, so
        # the file cannot outlive the result window B agreed to (or A attested to for B).
        rows = await self._rows(
            session,
            select(RadarRequestRow)
            .where(
                RadarRequestRow.principal_id == principal_id,
                RadarRequestRow.status.in_(
                    (RadarStatus.PENDING.value, RadarStatus.COMPLETED.value)
                ),
                RadarRequestRow.withdrawn_at.is_(None),
                RadarRequestRow.revoked_at.is_(None),
                RadarRequestRow.expires_at > now,
            )
            .order_by(RadarRequestRow.created_at.desc()),
            "radar_sent",
            truncated,
        )
        return [
            ExportRadarSent(
                nickname=self._envelope.decrypt(
                    row.recipient_label_ciphertext, context=f"radar-label:{row.id}".encode()
                ).decode(),
                context=row.context,
                voice=row.voice,
                mode=row.mode,
                status=row.status,
                permission_attested_at=row.authorization_attested_at,
                created_at=row.created_at,
                expires_at=row.expires_at,
            )
            for row in rows
        ]

    async def _radar_received(
        self, session: AsyncSession, guest_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportRadarReceived]:
        # The same eligibility as GET /v1/radar/received (P09 D2), without the sender's label.
        rows = await self._rows(
            session,
            select(RadarRequestRow)
            .where(
                RadarRequestRow.recipient_guest_id == guest_id,
                RadarRequestRow.status == RadarStatus.COMPLETED.value,
                RadarRequestRow.withdrawn_at.is_(None),
                RadarRequestRow.result_ciphertext.is_not(None),
                RadarRequestRow.completed_at.is_not(None),
                RadarRequestRow.completed_at > now - RECEIPT_TTL,
            )
            .order_by(RadarRequestRow.completed_at.desc()),
            "radar_received",
            truncated,
        )
        return [
            ExportRadarReceived(
                context=row.context,
                consent_version=row.consent_version,
                accepted_at=cast(datetime, row.completed_at),
                expires_at=row.expires_at,
            )
            for row in rows
        ]

    async def _la_chung(
        self, session: AsyncSession, principal_id: UUID, now: datetime, truncated: list[str]
    ) -> list[ExportLaChungInvite]:
        rows = await self._rows(
            session,
            select(LaChungRequestRow)
            .where(LaChungRequestRow.principal_id == principal_id)
            .order_by(LaChungRequestRow.created_at.desc()),
            "la_chung_invites",
            truncated,
        )
        answered = set(
            await session.scalars(
                select(LaChungResponseRow.request_id).where(
                    LaChungResponseRow.request_id.in_([row.id for row in rows]),
                    LaChungResponseRow.deleted_at.is_(None),
                    LaChungResponseRow.withdrawn_at.is_(None),
                    LaChungResponseRow.hidden_at.is_(None),
                )
            )
        )
        invites: list[ExportLaChungInvite] = []
        for row in rows:
            if row.recipient_label_ciphertext is not None:
                nickname = self._envelope.decrypt(
                    row.recipient_label_ciphertext,
                    context=f"la-chung-recipient-label:{row.id}".encode(),
                ).decode()
            else:
                nickname = row.recipient_label or ""
            status = row.status
            if status == "pending" and row.expires_at <= now:
                status = "expired"
            invites.append(
                ExportLaChungInvite(
                    nickname=nickname,
                    context=row.context,
                    status=status,
                    has_response=row.id in answered,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                )
            )
        return invites

    async def _matching(
        self, session: AsyncSession, principal_id: UUID, truncated: list[str]
    ) -> ExportMatching | None:
        profile_row = await session.scalar(
            select(MatchingProfileRow).where(MatchingProfileRow.principal_id == principal_id)
        )
        consent_rows = await self._rows(
            session,
            select(MatchingConsentRow)
            .where(MatchingConsentRow.principal_id == principal_id)
            .order_by(MatchingConsentRow.accepted_at.desc(), MatchingConsentRow.id),
            "matching.consents",
            truncated,
        )
        # The verification provider reference is an external identifier; only the status goes out.
        verification = await session.scalar(
            select(MatchingVerificationRow.status).where(
                MatchingVerificationRow.principal_id == principal_id
            )
        )
        if profile_row is None and not consent_rows and verification is None:
            return None
        profile = None
        if profile_row is not None:
            profile = ExportMatchingProfile(
                display_name=self._envelope.decrypt(
                    profile_row.display_name_ciphertext,
                    context=f"matching-profile:{principal_id}".encode(),
                ).decode(),
                gender_identity=profile_row.gender_identity,
                intent=profile_row.intent,
                gender_preference=profile_row.gender_preference,
                min_age=profile_row.min_age,
                max_age=profile_row.max_age,
                region_code=profile_row.region_code,
                weekly_intent=profile_row.weekly_intent,
                active=profile_row.active,
                joined_at=profile_row.joined_at,
                created_at=profile_row.created_at,
                updated_at=profile_row.updated_at,
            )
        return ExportMatching(
            profile=profile,
            consents=[
                ExportConsent(
                    purpose=row.purpose,
                    version=row.version,
                    accepted_at=row.accepted_at,
                    revoked_at=row.revoked_at,
                )
                for row in consent_rows
            ],
            verification_status=verification,
        )


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _tarot(view: TarotSessionView) -> ExportTarotSession:
    reading = view.reading
    return ExportTarotSession(
        state=view.state.value,
        context=view.context.value,
        spread=view.spread.value,
        voice=view.voice.value,
        question=view.question,
        cards=[
            ExportTarotCard(position=card.position_label, card=card.card.title_vi)
            for card in view.selected_cards
        ],
        reading=(
            ExportTarotReading(
                headline=reading.headline,
                summary=reading.summary,
                positions=[
                    ExportTarotPosition(
                        position=position.label,
                        card=position.card.title_vi,
                        meaning_here=position.meaning_here,
                        everyday_scene=position.everyday_scene,
                        reflection_question=position.reflection_question,
                        small_action=position.small_action,
                    )
                    for position in reading.positions
                ],
                conclusion=reading.stance.conclusion if reading.stance is not None else None,
                closing_prompt=reading.closing_prompt,
                disclaimer=reading.disclaimer,
            )
            if reading is not None
            else None
        ),
        created_at=view.created_at,
        expires_at=view.expires_at,
    )


def _reading(projection: ReadingContentProjection) -> ExportSavedReading:
    return ExportSavedReading(
        sections=ExportReadingSections.model_validate(projection.sections.model_dump()),
        evidence=ExportReadingEvidence(
            title=projection.evidence.title,
            claims=list(projection.evidence.claims),
            framework_disclosure=projection.evidence.framework_disclosure,
        ),
        disclaimer=projection.disclaimer,
    )
