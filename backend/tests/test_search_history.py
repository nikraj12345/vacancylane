"""Saved search history for signed-in users."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import SavedSearch, User, utcnow
from app.services.auth import create_access_token
from app.services.search_history import DEDUPE_WINDOW, persist_saved_search


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def user(db) -> User:
    existing = db.query(User).filter(User.email == "history@example.com").one_or_none()
    if existing:
        return existing
    row = User(
        google_sub="history-user",
        email="history@example.com",
        name="Historian",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def test_save_and_list_searches(client, user):
    payload = {
        "role": "Backend Engineer",
        "alternate_role": "SDE",
        "location_label": "Bengaluru, India",
        "skills": "Python, FastAPI",
        "company": "",
        "experience_bands": ["2-5"],
        "sources": ["lever"],
        "payload": {"role": "Backend Engineer", "sources": ["lever"]},
        "result_count": 12,
    }
    created = client.post("/history", json=payload, headers=_auth(user))
    assert created.status_code == 201
    body = created.json()
    assert body["role"] == "Backend Engineer"
    assert body["result_count"] == 12

    listed = client.get("/history", headers=_auth(user))
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert listed.json()["searches"][0]["location_label"] == "Bengaluru, India"


def test_delete_search(client, user):
    created = client.post(
        "/history",
        json={
            "role": "AI Engineer",
            "payload": {"role": "AI Engineer"},
            "result_count": 3,
        },
        headers=_auth(user),
    ).json()
    deleted = client.delete(f"/history/{created['id']}", headers=_auth(user))
    assert deleted.status_code == 204


def test_dedupe_only_within_window(db, user):
    payload = {"role": "Backend Engineer", "sources": ["lever"]}
    first = persist_saved_search(
        db,
        user,
        role="Backend Engineer",
        payload=payload,
        result_count=4,
    )
    second = persist_saved_search(
        db,
        user,
        role="Backend Engineer",
        payload=payload,
        result_count=9,
    )
    assert second.id == first.id
    assert second.result_count == 9

    # Outside the window a new row is created even for the same filters.
    first.created_at = utcnow() - DEDUPE_WINDOW - timedelta(minutes=1)
    db.commit()

    third = persist_saved_search(
        db,
        user,
        role="Backend Engineer",
        payload=payload,
        result_count=11,
    )
    assert third.id != first.id


def test_search_endpoint_saves_history_when_signed_in(client, user, db):
    fake_result = {
        "total": 2,
        "jobs": [],
        "queries_used": [],
        "query_count": 0,
        "removed_closed": 0,
        "search_providers": [],
        "google_enabled": False,
        "raw_results": False,
        "variables": {},
    }
    before = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == user.id, SavedSearch.role == "Platform Engineer")
        .count()
    )
    with patch("app.routers.search.search_jobs", return_value=fake_result):
        response = client.post(
            "/search",
            json={
                "role": "Platform Engineer",
                "alternate_role": "",
                "location": "",
                "locations": [
                    {
                        "label": "Pune",
                        "city": "Pune",
                        "state": "Maharashtra",
                        "country": "India",
                        "remote": False,
                    }
                ],
                "skills": "Python OR Go",
                "experience": "",
                "experience_bands": ["2-5"],
                "company": "",
                "sources": ["lever"],
                "date_posted": "month",
                "remote_only": False,
                "employment_type": "",
                "verify_live": False,
                "raw_results": True,
            },
            headers=_auth(user),
        )
    assert response.status_code == 200

    rows = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == user.id, SavedSearch.role == "Platform Engineer")
        .order_by(SavedSearch.created_at.desc())
        .all()
    )
    assert len(rows) == before + 1
    assert rows[0].location_label == "Pune"
    assert rows[0].skills == "Python, Go"
    assert rows[0].result_count == 2


def test_search_endpoint_skips_history_when_anonymous(client, db):
    fake_result = {
        "total": 1,
        "jobs": [],
        "queries_used": [],
        "query_count": 0,
        "removed_closed": 0,
        "search_providers": [],
        "google_enabled": False,
        "raw_results": False,
        "variables": {},
    }
    before = db.query(SavedSearch).count()
    with patch("app.routers.search.search_jobs", return_value=fake_result):
        response = client.post(
            "/search",
            json={
                "role": "Anonymous Role",
                "sources": ["lever"],
                "date_posted": "any",
                "remote_only": False,
                "employment_type": "",
                "raw_results": True,
                "verify_live": False,
            },
        )
    assert response.status_code == 200
    assert db.query(SavedSearch).count() == before
