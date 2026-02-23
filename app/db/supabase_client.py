"""Supabase database client for persisting projects, sessions, and files."""
import asyncio
import json
from typing import Optional, Any
from datetime import datetime
from app.config import settings


class SupabaseClient:
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

    # ── Projects ──────────────────────────────────────────────────────────────

    async def create_project(self, name: str, description: str = "") -> dict:
        def _call():
            return (
                self._get_client()
                .table("projects")
                .insert({"name": name, "description": description, "created_at": datetime.utcnow().isoformat()})
                .execute()
            )
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else {}

    async def get_projects(self) -> list[dict]:
        def _call():
            return self._get_client().table("projects").select("*").order("created_at", desc=True).execute()
        result = await asyncio.to_thread(_call)
        return result.data or []

    async def get_project(self, project_id: str) -> Optional[dict]:
        def _call():
            return self._get_client().table("projects").select("*").eq("id", project_id).execute()
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else None

    async def update_project(self, project_id: str, updates: dict) -> dict:
        updates["updated_at"] = datetime.utcnow().isoformat()
        def _call():
            return self._get_client().table("projects").update(updates).eq("id", project_id).execute()
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else {}

    async def delete_project(self, project_id: str) -> bool:
        def _call():
            return self._get_client().table("projects").delete().eq("id", project_id).execute()
        await asyncio.to_thread(_call)
        return True

    # ── Chat Sessions ──────────────────────────────────────────────────────────

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str = "claude",
        project_id: Optional[str] = None,
    ) -> dict:
        def _call():
            return (
                self._get_client()
                .table("messages")
                .insert({
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "model": model,
                    "project_id": project_id,
                    "created_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else {}

    async def get_session_messages(self, session_id: str) -> list[dict]:
        def _call():
            return (
                self._get_client()
                .table("messages")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at")
                .execute()
            )
        result = await asyncio.to_thread(_call)
        return result.data or []

    async def get_sessions(self, project_id: Optional[str] = None) -> list[dict]:
        def _call():
            q = self._get_client().table("sessions").select("*")
            if project_id:
                q = q.eq("project_id", project_id)
            return q.order("updated_at", desc=True).execute()
        result = await asyncio.to_thread(_call)
        return result.data or []

    async def create_session(
        self, title: str = "New Chat", project_id: Optional[str] = None
    ) -> dict:
        now = datetime.utcnow().isoformat()
        def _call():
            return (
                self._get_client()
                .table("sessions")
                .insert({"title": title, "project_id": project_id, "created_at": now, "updated_at": now})
                .execute()
            )
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else {}

    async def update_session(self, session_id: str, updates: dict) -> dict:
        updates["updated_at"] = datetime.utcnow().isoformat()
        def _call():
            return self._get_client().table("sessions").update(updates).eq("id", session_id).execute()
        result = await asyncio.to_thread(_call)
        return result.data[0] if result.data else {}

    # ── Auto Save ─────────────────────────────────────────────────────────────

    async def auto_save(self, session_id: str, state: dict) -> bool:
        def _call():
            return (
                self._get_client()
                .table("auto_saves")
                .upsert({
                    "session_id": session_id,
                    "state": json.dumps(state),
                    "saved_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )
        await asyncio.to_thread(_call)
        return True

    async def get_auto_save(self, session_id: str) -> Optional[dict]:
        def _call():
            return (
                self._get_client()
                .table("auto_saves")
                .select("*")
                .eq("session_id", session_id)
                .execute()
            )
        result = await asyncio.to_thread(_call)
        if result.data:
            item = result.data[0]
            item["state"] = json.loads(item["state"]) if isinstance(item["state"], str) else item["state"]
            return item
        return None
