"""Owner-only sentences of the Hợp gu invite-first consent (AL1, 20.11.2026).

The owner chose an invite-first design: the main path is a link where the other person types
their own birth date; ticking "they allowed me" becomes the secondary path. Those screens are
made of consent and privacy sentences, which only the owner approves. They are drafted here and
in ``copy_registry.json`` as pending ``privacy.radar.invite-first.*`` entries.

Nothing here is served while any entry is pending: ``invite_first_sentences`` returns None, so
the paths that need these sentences (``RadarService.invite_first_enabled``) stay closed even if
``radar_invite_first_consent`` is switched on. Approving them is the owner's act in the registry
(approver "owner"), never a code default.
"""

from __future__ import annotations

from app.domains.content.copy_approval import approved_copy

PREFIX = "privacy.radar.invite-first."

# Registry id suffix → where the sentence is shown. The text lives only in the registry.
SENTENCE_KEYS = (
    "owner-invite-heading",  # start screen, main block title (A)
    "owner-invite-body",  # start screen, main block text (A)
    "owner-attest-label",  # start screen, secondary tick label (A)
    "owner-attest-help",  # start screen, under the tick (A)
    "owner-date-only-storage",  # start screen, what happens to the date A typed (A)
    "recipient-heading",  # one-field invite page title (B)
    "recipient-body",  # one-field invite page, why one date is enough (B)
    "recipient-consent",  # one-field invite page, consent tick (B)
    "recipient-decline",  # one-field invite page, leaving without answering (B)
)


def invite_first_sentences() -> dict[str, str] | None:
    """Every approved sentence by key, or None while any of them is still pending."""

    found: dict[str, str] = {}
    for key in SENTENCE_KEYS:
        text = approved_copy(f"{PREFIX}{key}")
        if text is None:
            return None
        found[key] = text
    return found
