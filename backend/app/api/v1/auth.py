from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, get_current_user
from app.core.config import Environment, get_settings
from app.core.database import get_db
from app.models.auth import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth as svc

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        mobile=user.mobile,
        user_type=user.user_type,
        status=user.status,
        is_email_verified=user.is_email_verified,
        is_mobile_verified=user.is_mobile_verified,
        roles=sorted(r.slug for r in user.roles),
        permissions=sorted(svc.user_permissions(user)),
    )


def _respond(response: Response, session: svc.Session) -> TokenResponse:
    s = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        session.refresh_token,
        max_age=s.refresh_token_expire_days * 86400 if session.remember else None,
        httponly=True,
        secure=s.environment not in (Environment.DEVELOPMENT, Environment.TEST),
        samesite="lax",
        path=f"{s.api_v1_prefix}/auth",
    )
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(access_token=session.access_token, expires_in=session.expires_in, user=_user_out(session.user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    session = await svc.register_customer(db, data, ip=client_ip(request), ua=request.headers.get("user-agent"))
    return _respond(response, session)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    session = await svc.login(
        db,
        data.identifier,
        data.password,
        ip=client_ip(request),
        ua=request.headers.get("user-agent"),
        remember=data.remember_me,
    )
    return _respond(response, session)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    session = await svc.refresh(db, refresh_token, ip=client_ip(request), ua=request.headers.get("user-agent"))
    return _respond(response, session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response, refresh_token: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)
):
    await svc.logout(db, refresh_token)
    response.delete_cookie(REFRESH_COOKIE, path=f"{get_settings().api_v1_prefix}/auth")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)
