"""Google Sign-In verification and JWT session tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, utcnow

bearer_scheme = HTTPBearer(auto_error=False)


def google_login_configured() -> bool:
    return bool(settings.google_oauth_client_id.strip())


def verify_google_id_token(token: str) -> dict:
    """Validate a Google Identity Services ID token and return its claims."""
    if not google_login_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured. Set GOOGLE_OAUTH_CLIENT_ID.",
        )
    try:
        return id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_oauth_client_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {exc}",
        ) from exc


def upsert_user_from_google(db: Session, claims: dict) -> User:
    sub = claims.get("sub")
    email = claims.get("email")
    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token is missing sub or email",
        )

    user = db.query(User).filter(User.google_sub == sub).one_or_none()
    if user is None:
        user = db.query(User).filter(User.email == email).one_or_none()

    if user is None:
        user = User(
            google_sub=sub,
            email=email,
            name=claims.get("name"),
            picture_url=claims.get("picture"),
        )
        db.add(user)
    else:
        user.google_sub = sub
        user.email = email
        user.name = claims.get("name") or user.name
        user.picture_url = claims.get("picture") or user.picture_url
        user.last_login_at = utcnow()

    db.commit()
    db.refresh(user)
    return user


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with Google to continue",
        )
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
