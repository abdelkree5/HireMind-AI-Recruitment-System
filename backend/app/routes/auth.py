from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.schemas import AuthLoginRequest, AuthRegisterRequest, AuthSessionResponse, AuthUserResponse
from backend.app.services.auth_service import (
    ConflictError,
    authenticate_user,
    bootstrap_auth,
    create_session,
    create_user,
    require_current_user,
    revoke_session,
)

router = APIRouter()


def _extract_token(authorization: str | None, session_token: str | None) -> str:
    if session_token:
        return session_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    raise HTTPException(status_code=401, detail="Authentication token is required.")


@router.on_event("startup")
def _seed_demo_accounts() -> None:
    bootstrap_auth()


@router.post("/register", response_model=AuthSessionResponse)
def register(payload: AuthRegisterRequest) -> AuthSessionResponse:
    try:
        user = create_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            company_name=payload.company_name,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = create_session(user.id)
    return AuthSessionResponse(user=AuthUserResponse(**user.as_dict()), **session)


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: AuthLoginRequest) -> AuthSessionResponse:
    try:
        user = authenticate_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    session = create_session(user.id)
    return AuthSessionResponse(user=AuthUserResponse(**user.as_dict()), **session)


@router.get("/me", response_model=AuthUserResponse)
def me(
    user = Depends(require_current_user),
) -> AuthUserResponse:
    return AuthUserResponse(**user.as_dict())


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> dict[str, str]:
    token = _extract_token(authorization, x_session_token)
    revoke_session(token)
    return {"status": "ok"}
