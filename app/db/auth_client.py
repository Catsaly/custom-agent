"""
Auth Client — Supabase Email/Password Authentication
=====================================================
Supabase'in yerleşik auth sistemini sarar.

Kullanım:
    auth = AuthClient()
    result = await auth.sign_in("user@example.com", "password")
    result = await auth.sign_up("user@example.com", "password")
    result = await auth.sign_out(access_token)
    user   = await auth.get_user(access_token)
"""
import asyncio
from typing import Optional
from app.config import settings


class AuthClient:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise RuntimeError("Supabase credentials not configured")
            from supabase import create_client
            self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    @property
    def available(self) -> bool:
        return bool(settings.supabase_url and settings.supabase_key)

    # ── Register ──────────────────────────────────────────────────────────────

    async def sign_up(self, email: str, password: str) -> dict:
        """
        Yeni kullanıcı kaydı yapar.
        Başarıda: {"ok": True, "user": {...}, "session": {...}}
        Hata:      {"ok": False, "error": "..."}
        """
        def _call():
            return self._get_client().auth.sign_up({
                "email": email,
                "password": password,
            })
        try:
            res = await asyncio.to_thread(_call)
            if res.user:
                return {
                    "ok": True,
                    "user": _format_user(res.user),
                    "session": _format_session(res.session),
                    "email_confirmation_required": res.session is None,
                }
            return {"ok": False, "error": "Kayıt başarısız."}
        except Exception as e:
            return {"ok": False, "error": _parse_auth_error(str(e))}

    # ── Login ─────────────────────────────────────────────────────────────────

    async def sign_in(self, email: str, password: str) -> dict:
        """
        Email/şifre ile giriş yapar.
        Başarıda: {"ok": True, "user": {...}, "session": {...}}
        Hata:      {"ok": False, "error": "..."}
        """
        def _call():
            return self._get_client().auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
        try:
            res = await asyncio.to_thread(_call)
            if res.user and res.session:
                return {
                    "ok": True,
                    "user": _format_user(res.user),
                    "session": _format_session(res.session),
                }
            return {"ok": False, "error": "Giriş başarısız."}
        except Exception as e:
            return {"ok": False, "error": _parse_auth_error(str(e))}

    # ── Logout ────────────────────────────────────────────────────────────────

    async def sign_out(self, access_token: Optional[str] = None) -> bool:
        """Oturumu kapatır."""
        def _call():
            client = self._get_client()
            if access_token:
                client.auth.set_session(access_token, "")
            client.auth.sign_out()
        try:
            await asyncio.to_thread(_call)
            return True
        except Exception:
            return False

    # ── Get Current User ──────────────────────────────────────────────────────

    async def get_user(self, access_token: str) -> Optional[dict]:
        """
        Access token ile mevcut kullanıcı bilgisini döner.
        Geçersiz token: None
        """
        def _call():
            return self._get_client().auth.get_user(access_token)
        try:
            res = await asyncio.to_thread(_call)
            if res and res.user:
                return _format_user(res.user)
            return None
        except Exception:
            return None

    # ── Refresh Token ─────────────────────────────────────────────────────────

    async def refresh_session(self, refresh_token: str) -> dict:
        """Refresh token ile yeni access token alır."""
        def _call():
            return self._get_client().auth.refresh_session(refresh_token)
        try:
            res = await asyncio.to_thread(_call)
            if res and res.session:
                return {
                    "ok": True,
                    "session": _format_session(res.session),
                    "user": _format_user(res.user) if res.user else None,
                }
            return {"ok": False, "error": "Token yenileme başarısız."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Password Reset ────────────────────────────────────────────────────────

    async def reset_password(self, email: str) -> dict:
        """Şifre sıfırlama maili gönderir."""
        def _call():
            return self._get_client().auth.reset_password_email(email)
        try:
            await asyncio.to_thread(_call)
            return {"ok": True, "message": f"{email} adresine sıfırlama maili gönderildi."}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_user(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": str(user.created_at) if user.created_at else None,
        "email_confirmed": user.email_confirmed_at is not None,
    }


def _format_session(session) -> Optional[dict]:
    if not session:
        return None
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": session.token_type,
    }


def _parse_auth_error(msg: str) -> str:
    """Supabase hata mesajını Türkçe'ye çevirir."""
    msg_lower = msg.lower()
    if "invalid login" in msg_lower or "invalid credentials" in msg_lower:
        return "Email veya şifre hatalı."
    if "email not confirmed" in msg_lower:
        return "Email adresinizi onaylamanız gerekiyor."
    if "user already registered" in msg_lower or "already exists" in msg_lower:
        return "Bu email zaten kayıtlı."
    if "password" in msg_lower and ("weak" in msg_lower or "short" in msg_lower):
        return "Şifre en az 6 karakter olmalıdır."
    if "rate limit" in msg_lower:
        return "Çok fazla deneme. Lütfen bekleyin."
    if "network" in msg_lower or "connection" in msg_lower:
        return "Bağlantı hatası. Supabase yapılandırmasını kontrol edin."
    return msg
