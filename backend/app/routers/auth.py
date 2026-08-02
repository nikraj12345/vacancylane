from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.auth import (
    create_access_token,
    get_current_user,
    google_login_configured,
    upsert_user_from_google,
    verify_google_id_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., min_length=20)


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    picture_url: str | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthStatusResponse(BaseModel):
    google_login_enabled: bool
    google_client_id: str


@router.get("/status", response_model=AuthStatusResponse)
def auth_status():
    return AuthStatusResponse(
        google_login_enabled=google_login_configured(),
        google_client_id=settings.google_oauth_client_id,
    )


@router.post("/google", response_model=AuthResponse)
def login_with_google(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    claims = verify_google_id_token(payload.id_token)
    user = upsert_user_from_google(db, claims)
    token = create_access_token(user)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
