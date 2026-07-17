import asyncio

from fastapi.testclient import TestClient

import app.main as main
from app.ai_service import SYSTEM_INSTRUCTIONS, _demo_analysis, build_prompt
from app.job_description import extract_job_description
from app.storage import InMemoryStore


def test_job_description_text_is_cleaned_and_added_to_prompt():
    job_description = extract_job_description(b"Backend Developer\nRequires Python, FastAPI, and MongoDB.", "role.txt", "text/plain")
    assert "FastAPI" in job_description
    assert "MongoDB" in build_prompt("Python developer", "Backend Developer", job_description)


def test_resume_rewrite_prompt_requires_material_improvement():
    assert "not merely add spaces" in SYSTEM_INSTRUCTIONS
    assert "Never invent metrics" in SYSTEM_INSTRUCTIONS


def test_cover_letter_uses_a_saved_report(monkeypatch):
    monkeypatch.setattr(main.settings, "openai_api_key", "")
    with TestClient(main.app) as client:
        main.app.state.store = InMemoryStore()
        auth = client.post("/api/auth/register", json={"full_name": "Phase Two Student", "email": "phase2-test@example.com", "password": "secure-pass"})
        token = auth.json()["access_token"]
        user_id = auth.json()["user"]["id"]
        job_description = "Requires Python, FastAPI, and MongoDB."
        analysis = _demo_analysis("Backend Developer", "Python FastAPI project", job_description)
        report = asyncio.run(main.app.state.store.save_analysis(user_id, "resume.pdf", "Backend Developer", analysis.model_dump(mode="json"), job_description))
        response = client.post("/api/generate-cover-letter", headers={"Authorization": f"Bearer {token}"}, json={"report_id": report["_id"]})
        assert response.status_code == 200
        assert len(response.json()["cover_letter"]) > 40
