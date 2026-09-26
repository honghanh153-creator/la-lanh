from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.share.models import ShareArtifactRecord


class ShareArtifactRepository(Protocol):
    async def create(self, record: ShareArtifactRecord) -> ShareArtifactRecord: ...

    async def find_by_token_hash(self, token_hash: bytes) -> ShareArtifactRecord | None: ...

    async def revoke_owned(
        self, guest_id: UUID, artifact_id: UUID, revoked_at: datetime
    ) -> bool: ...
