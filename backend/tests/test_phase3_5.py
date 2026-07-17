import asyncio

from fastapi.testclient import TestClient

import app.main as main
from app.ai_service import _demo_analysis
from app.main import app
from app.storage import InMemoryStore


def test_career_coach_and_pdf_export():
    with TestClient(app) as client:
        app.state.store = InMemoryStore()
        auth = client.post("/api/auth/register", json={"full_name": "Coach Student", "email": "coach@example.com", "password": "secure-pass"})
        token = auth.json()["access_token"]
        user_id = auth.json()["user"]["id"]
        analysis = _demo_analysis("Backend Developer", "Python FastAPI project", "Requires Python and FastAPI.")
        report = asyncio.run(app.state.store.save_analysis(user_id, "resume.pdf", "Backend Developer", analysis.model_dump(mode="json"), "Requires Python and FastAPI."))
        headers = {"Authorization": f"Bearer {token}"}
        chat = client.post("/api/chat", headers=headers, json={"message": "Which skill should I learn first?"})
        assert chat.status_code == 200
        assert client.get("/api/chat/history", headers=headers, params={"session_id": chat.json()["session_id"]}).status_code == 200
        pdf = client.get(f"/api/report/{report['_id']}/pdf", headers=headers)
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")
