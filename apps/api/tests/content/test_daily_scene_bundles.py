"""Daily scenes ship only inside whole bundles (Codex review of #685, 19.11.2026).

A Daily situation without an approved bundle rotates its scenes and its actions independently
(``daily_psychology.py``). A loose scene that names a concrete moment ("a coworker's document")
then lands next to unrelated advice ("cooking"), which breaks the same-situation rule of the
Daily content contract. So a scene is served only as part of a bundle whose headline, scene and
action were written and approved together (owner 10.11.2026), and the copy batch never approves
a loose ``daily.scene.*`` entry (``scripts/codex-copy-review.mjs`` ``bundleOnly``).
"""

from __future__ import annotations

from app.domains.content.copy_approval import approved_texts, load_registry


def test_no_loose_daily_scene_is_approved_in_the_registry() -> None:
    approved = sorted(
        key
        for key, entry in load_registry().items()
        if key.startswith("daily.scene.") and entry.status == "approved"
    )
    assert approved == [], (
        "a loose Daily scene would rotate apart from its advice; approve it as part of a whole "
        f"daily.bundle instead: {approved[:5]}"
    )


def test_the_served_pool_gets_no_loose_scene_from_the_registry() -> None:
    assert approved_texts("daily.scene.") == ()
