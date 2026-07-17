from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_register_login_profile_and_history_is_user_scoped():
    with TestClient(app) as client:
        registration = client.post("/api/auth/register", json={"full_name": "Test Student", "email": "student@example.com", "password": "secure-pass"})
        assert registration.status_code == 200
        token = registration.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        profile = client.get("/api/auth/profile", headers=headers)
        assert profile.status_code == 200
        assert profile.json()["email"] == "student@example.com"

        history = client.get("/api/history", headers=headers)
        assert history.status_code == 200
        assert history.json() == []

        login = client.post("/api/auth/login", json={"email": "student@example.com", "password": "secure-pass"})
        assert login.status_code == 200


def test_auth_validation_and_protected_routes():
    with TestClient(app) as client:
        weak_password = client.post("/api/auth/register", json={"full_name": "Test Student", "email": "bad@example.com", "password": "short"})
        assert weak_password.status_code == 400
        assert weak_password.json()["error_code"] == "PASSWORD_WEAK"

        unauthenticated = client.get("/api/history")
        assert unauthenticated.status_code == 401
        assert unauthenticated.json()["error_code"] == "AUTH_REQUIRED"


def test_duplicate_email_is_rejected():
    with TestClient(app) as client:
        payload = {"full_name": "Test Student", "email": "duplicate@example.com", "password": "secure-pass"}
        assert client.post("/api/auth/register", json=payload).status_code == 200
        duplicate = client.post("/api/auth/register", json=payload)
        assert duplicate.status_code == 409
        assert duplicate.json()["error_code"] == "EMAIL_EXISTS"
