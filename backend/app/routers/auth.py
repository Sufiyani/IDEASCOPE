"""
IdeaScope – Authentication router.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_any
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshRequest
from app.services import auth_service
from app.services.auth_service import _user_to_dict

router = APIRouter(tags=["Auth"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(db, body.username, body.password)


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_tokens(db, body.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    body: LogoutRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_any),
):
    auth_service.logout(db, body.refresh_token)
    return Response(status_code=204)


@router.get("/me")
def me(current_user=Depends(get_current_user_any)):
    return _user_to_dict(current_user)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_any),
):
    return auth_service.change_password(db, current_user, body.current_password, body.new_password)
