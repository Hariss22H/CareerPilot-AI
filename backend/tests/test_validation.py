from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_missing_resume_is_rejected():
    response = client.post("/api/analyze-resume", data={"job_role": "Backend Developer"})
    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "RESUME_REQUIRED"


def test_missing_role_is_rejected():
    response = client.post("/api/analyze-resume", files={"resume": ("resume.pdf", b"not a pdf", "application/pdf")})
    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "JOB_ROLE_INVALID"

