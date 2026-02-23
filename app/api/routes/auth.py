"""
Auth Routes — Supabase Email/Password
======================================
POST /api/auth/register   — Kayıt
POST /api/auth/login      — Giriş
POST /api/auth/logout     — Çıkış
GET  /api/auth/me         — Mevcut kullanıcı (token ile)
POST /api/auth/refresh    — Token yenile
POST /api/auth/reset-password — Şifre sıfırlama maili
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.db.auth_client import AuthClient

router = APIRouter(prefix="/auth", tags=["Auth"])
_auth = AuthClient()
_bearer = HTTPBearer(auto_error=False)


# ── Request Models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "guclu_sifre"}}}


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "guclu_sifre"}}}


class RefreshRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    email: str


# ── Auth Dependency ───────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Bearer token doğrulama bağımlılığı."""
    if not credentials:
        return None
    user = await _auth.get_user(credentials.credentials)
    return user


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """Token zorunlu — yoksa 401 döner."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor.")
    user = await _auth.get_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token.")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register")
async def register(req: RegisterRequest):
    """
    Yeni kullanıcı kaydı.

    - Başarıda access_token + kullanıcı bilgisi döner
    - Email onayı gerekirsa `email_confirmation_required: true` döner
    """
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    if not _auth.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış.")

    result = await _auth.sign_up(req.email, req.password)

    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "message": "Kayıt başarılı.",
        "user": result["user"],
        "session": result["session"],
        "email_confirmation_required": result.get("email_confirmation_required", False),
    }


@router.post("/login")
async def login(req: LoginRequest):
    """
    Email/şifre ile giriş.

    Döner: access_token, refresh_token, kullanıcı bilgisi
    """
    if not _auth.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış.")

    result = await _auth.sign_in(req.email, req.password)

    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result["error"])

    return {
        "message": "Giriş başarılı.",
        "user": result["user"],
        "session": result["session"],
    }


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
):
    """Oturumu kapatır."""
    token = credentials.credentials if credentials else None
    await _auth.sign_out(token)
    return {"message": "Çıkış başarılı."}


@router.get("/me")
async def get_me(user: dict = Depends(require_auth)):
    """Mevcut kullanıcı bilgisini döner (Bearer token zorunlu)."""
    return {"user": user}


@router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    """Refresh token ile yeni access token alır."""
    if not _auth.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış.")

    result = await _auth.refresh_session(req.refresh_token)

    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Token yenileme başarısız."))

    return result


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Şifre sıfırlama maili gönderir."""
    if not _auth.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış.")

    result = await _auth.reset_password(req.email)

    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": result["message"]}
