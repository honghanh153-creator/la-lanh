"""Shared synthetic flow for the US-23 copy-lifecycle and correction tests (SQLite, real app).

A guest with a date-only profile, today's Daily note, one saved copy and one live share link,
all through the public API so every repository, cipher and journal is the production wiring.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
BIRTH_DATE = "1990-01-01"


def make_app(database_path: Path) -> FastAPI:
    return create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )


def start_guest(client: TestClient, birth_date: str = BIRTH_DATE) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": f"copy-flow-{uuid4().hex}",
        },
    )
    assert guest.status_code == 200
    headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
    birth = client.post("/v1/birth-profile", json={"birth_date": birth_date}, headers=headers)
    assert birth.status_code == 200
    return headers


@dataclass(frozen=True)
class Copies:
    note_id: str
    revision_id: str
    saved_id: str
    share_id: str
    public_path: str


def save_and_share(client: TestClient, headers: dict[str, str]) -> Copies:
    daily = client.get("/v1/daily-note")
    assert daily.status_code == 200
    note_id = daily.json()["id"]
    saved = client.put(f"/v1/daily-note/{note_id}/saved", headers=headers)
    assert saved.status_code == 200
    share = client.post(
        f"/v1/daily-note/{note_id}/share-artifacts", json={"format": "story_9_16"}, headers=headers
    )
    assert share.status_code == 200
    return Copies(
        note_id=note_id,
        revision_id=saved.json()["revision_id"],
        saved_id=saved.json()["id"],
        share_id=share.json()["id"],
        public_path=share.json()["public_path"].replace("/share/", "/v1/share-artifacts/"),
    )


def raw(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def count(database_path: Path, table: str, where: str = "1=1", *args: Any) -> int:
    with raw(database_path) as connection:
        query = f"SELECT COUNT(*) FROM {table} WHERE {where}"  # noqa: S608 - fixed test names
        return int(connection.execute(query, args).fetchone()[0])


def hex_id(value: str) -> str:
    """SQLite stores SQLAlchemy UUIDs as 32 hex characters."""

    return value.replace("-", "")


def delete_sources(database_path: Path) -> None:
    """What a correction does to the sources, applied directly: notes, plans, revisions."""

    with raw(database_path) as connection:
        connection.execute("DELETE FROM daily_notes")
        connection.execute("DELETE FROM reading_plans")
        assert connection.execute("SELECT COUNT(*) FROM reading_revisions").fetchone()[0] == 0
