from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import Settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryStore:
    def __init__(self):
        self.users: dict[str, dict[str, Any]] = {}
        self.analyses: dict[str, dict[str, Any]] = {}
        self.chat_sessions: dict[str, dict[str, Any]] = {}
        self.chat_messages: list[dict[str, Any]] = []

    async def find_user_by_email(self, email: str):
        return next((user for user in self.users.values() if user["email"] == email), None)

    async def get_user(self, user_id: str):
        return self.users.get(user_id)

    async def create_user(self, full_name: str, email: str, password_hash: str):
        user = {"_id": str(uuid4()), "full_name": full_name, "email": email, "password_hash": password_hash, "created_at": _now()}
        self.users[user["_id"]] = user
        return user

    async def save_analysis(self, user_id: str, resume_name: str, target_role: str, analysis: dict[str, Any], job_description: str = ""):
        report = {"_id": str(uuid4()), "user_id": user_id, "resume_name": resume_name, "target_role": target_role, "job_description": job_description, "analysis": analysis, "ats_score": analysis.get("ats_score"), "created_at": _now()}
        self.analyses[report["_id"]] = report
        return report

    async def list_analyses(self, user_id: str):
        return sorted((item for item in self.analyses.values() if item["user_id"] == user_id), key=lambda item: item["created_at"], reverse=True)

    async def get_analysis(self, user_id: str, analysis_id: str):
        item = self.analyses.get(analysis_id)
        return item if item and item["user_id"] == user_id else None

    async def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        if await self.get_analysis(user_id, analysis_id) is None:
            return False
        del self.analyses[analysis_id]
        return True

    async def create_chat_session(self, user_id: str):
        session = {"_id": str(uuid4()), "user_id": user_id, "session_name": "Career Coach", "created_at": _now()}
        self.chat_sessions[session["_id"]] = session
        return session

    async def get_chat_session(self, user_id: str, session_id: str):
        session = self.chat_sessions.get(session_id)
        return session if session and session["user_id"] == user_id else None

    async def add_chat_message(self, session_id: str, role: str, message: str):
        item = {"_id": str(uuid4()), "session_id": session_id, "role": role, "message": message, "created_at": _now()}
        self.chat_messages.append(item)
        return item

    async def get_chat_messages(self, session_id: str):
        return [item for item in self.chat_messages if item["session_id"] == session_id]

    async def close(self):
        return None


class MongoStore:
    def __init__(self, settings: Settings):
        from motor.motor_asyncio import AsyncIOMotorClient

        self.client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
            connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        )
        self.db = self.client[settings.mongodb_database]
        self.users = self.db.users
        self.analyses = self.db.resume_analyses
        self.chat_sessions = self.db.chat_sessions
        self.chat_messages = self.db.chat_messages

    @staticmethod
    def _public_user(user):
        return user

    async def find_user_by_email(self, email: str):
        return await self.users.find_one({"email": email})

    async def get_user(self, user_id: str):
        return await self.users.find_one({"_id": user_id})

    async def create_user(self, full_name: str, email: str, password_hash: str):
        user = {"_id": str(uuid4()), "full_name": full_name, "email": email, "password_hash": password_hash, "created_at": _now()}
        await self.users.insert_one(user)
        return user

    async def save_analysis(self, user_id: str, resume_name: str, target_role: str, analysis: dict[str, Any], job_description: str = ""):
        report = {"_id": str(uuid4()), "user_id": user_id, "resume_name": resume_name, "target_role": target_role, "job_description": job_description, "analysis": analysis, "ats_score": analysis.get("ats_score"), "created_at": _now()}
        await self.analyses.insert_one(report)
        return report

    async def list_analyses(self, user_id: str):
        return await self.analyses.find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

    async def get_analysis(self, user_id: str, analysis_id: str):
        return await self.analyses.find_one({"_id": analysis_id, "user_id": user_id})

    async def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        result = await self.analyses.delete_one({"_id": analysis_id, "user_id": user_id})
        return result.deleted_count == 1

    async def create_chat_session(self, user_id: str):
        session = {"_id": str(uuid4()), "user_id": user_id, "session_name": "Career Coach", "created_at": _now()}
        await self.chat_sessions.insert_one(session)
        return session

    async def get_chat_session(self, user_id: str, session_id: str):
        return await self.chat_sessions.find_one({"_id": session_id, "user_id": user_id})

    async def add_chat_message(self, session_id: str, role: str, message: str):
        item = {"_id": str(uuid4()), "session_id": session_id, "role": role, "message": message, "created_at": _now()}
        await self.chat_messages.insert_one(item)
        return item

    async def get_chat_messages(self, session_id: str):
        return await self.chat_messages.find({"session_id": session_id}).sort("created_at", 1).to_list(length=100)

    async def close(self):
        self.client.close()


def build_store(settings: Settings):
    return MongoStore(settings) if settings.mongodb_uri else InMemoryStore()


def serialize_report(report: dict[str, Any]) -> dict[str, Any]:
    result = dict(report)
    result["id"] = result.pop("_id")
    result.pop("user_id", None)
    if isinstance(result.get("created_at"), datetime):
        result["created_at"] = result["created_at"].isoformat()
    result["has_job_description"] = bool(result.get("job_description"))
    return result
