"""Auth + application tracking against Postgres models."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import JobApplication, User
from app.services.auth import create_access_token


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


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
    row = User(
        google_sub="google-sub-1",
        email="seeker@example.com",
        name="Seeker",
        picture_url="https://example.com/a.png",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


class TestAuthStatus:
    def test_reports_google_login_flag(self, client):
        res = client.get("/auth/status")
        assert res.status_code == 200
        body = res.json()
        assert "google_login_enabled" in body
        assert "google_client_id" in body


class TestApplications:
    def test_apply_requires_auth(self, client):
        res = client.post(
            "/applications",
            json={
                "job_url": "https://jobs.lever.co/acme/1",
                "job_title": "Engineer",
            },
        )
        assert res.status_code == 401

    def test_apply_and_list(self, client, user, db):
        payload = {
            "job_url": "https://jobs.lever.co/acme/1",
            "job_title": "Backend Engineer",
            "company": "Acme",
            "location": "Bengaluru",
            "source": "lever",
            "source_name": "Lever",
        }
        created = client.post("/applications", json=payload, headers=_auth(user))
        assert created.status_code == 201
        body = created.json()
        assert body["job_title"] == "Backend Engineer"
        assert body["status"] == "applied"

        # Idempotent: same URL does not create a duplicate.
        again = client.post("/applications", json=payload, headers=_auth(user))
        assert again.status_code == 201
        assert again.json()["id"] == body["id"]
        assert db.query(JobApplication).count() == 1

        listed = client.get("/applications", headers=_auth(user))
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["applications"][0]["company"] == "Acme"

    def test_delete_application(self, client, user):
        created = client.post(
            "/applications",
            json={
                "job_url": "https://boards.greenhouse.io/acme/jobs/9",
                "job_title": "SDE",
            },
            headers=_auth(user),
        ).json()
        deleted = client.delete(
            f"/applications/{created['id']}",
            headers=_auth(user),
        )
        assert deleted.status_code == 204
        listed = client.get("/applications", headers=_auth(user))
        assert listed.json()["total"] == 0

    def test_expired_token_is_rejected(self, client, user):
        expired = jwt.encode(
            {
                "sub": str(user.id),
                "email": user.email,
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        res = client.get(
            "/applications",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert res.status_code == 401
