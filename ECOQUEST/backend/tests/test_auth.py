def payload(**overrides):
    values = {
        "full_name": "Maya Student",
        "email": "maya@college.edu",
        "usn": "1XX23CS002",
        "department": "Computer Science",
        "semester": 3,
        "password": "SecurePass123!",
    }
    return {**values, **overrides}


def test_registration_hashes_password_and_does_not_return_hash(client):
    response = client.post("/auth/register", json=payload())
    assert response.status_code == 201
    assert response.json()["role"] == "STUDENT"
    assert "password_hash" not in response.json()


def test_duplicate_email_and_usn_are_rejected(client):
    assert client.post("/auth/register", json=payload()).status_code == 201
    duplicate_email = client.post("/auth/register", json=payload(usn="1XX23CS003"))
    duplicate_usn = client.post("/auth/register", json=payload(email="other@college.edu"))
    assert duplicate_email.status_code == 409
    assert duplicate_usn.status_code == 409


def test_login_current_user_and_wrong_password(client, student):
    assert client.post("/auth/login", json={"email": "asha@college.edu", "password": "wrong-pass"}).status_code == 401
    response = client.get("/auth/me", headers=student["headers"])
    assert response.status_code == 200
    assert response.json()["usn"] == "1XX23CS001"
    assert "password_hash" not in response.json()


def test_invalid_and_expired_tokens_are_rejected(client):
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    from app.core.config import settings

    invalid = client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"})
    expired_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    expired = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert invalid.status_code == 401
    assert expired.status_code == 401


def test_registration_cannot_set_privileged_role(client):
    response = client.post("/auth/register", json=payload(role="ADMIN"))
    assert response.status_code == 201
    assert response.json()["role"] == "STUDENT"
