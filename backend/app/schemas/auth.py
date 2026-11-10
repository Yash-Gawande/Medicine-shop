from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserStatus, UserType

_MOBILE_RE = re.compile(r"^(?:\+91|91|0)?([6-9][0-9]{9})$")


def normalize_mobile(value: str) -> str:
    cleaned = re.sub(r"[\s\-()]", "", value)
    m = _MOBILE_RE.match(cleaned)
    if not m:
        raise ValueError("Enter a valid 10-digit Indian mobile number")
    return f"+91{m.group(1)}"


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    mobile: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("mobile")
    @classmethod
    def _mobile(cls, v: str | None) -> str | None:
        return normalize_mobile(v) if v else None

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain letters and numbers")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=255, description="Email or mobile number")
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    mobile: str | None
    user_type: UserType
    status: UserStatus
    is_email_verified: bool
    is_mobile_verified: bool
    roles: list[str]
    permissions: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: UserOut
