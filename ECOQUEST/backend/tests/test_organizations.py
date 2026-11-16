from io import BytesIO

from app.models.user import User
from app.services.auth_service import hash_password
from app.services import person2_service


def seed_user(client, role="ORGANIZER", email="organizer@college.edu"):
    session = client.app.state.test_session_factory()
    user = User(
        full_name="Organizing Lead", email=email, usn=f"ORG{email.split('@')[0][:8].upper()}",
        department="Computer Science", semester=5, password_hash=hash_password("SecurePass123!"), role=role,
    )
    session.add(user); session.commit(); session.refresh(user); user_id = user.id; session.close()
    login = client.post("/auth/login", json={"email": email, "password": "SecurePass123!"})
    assert login.status_code == 200
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


def organization_form(**overrides):
    values = {
        "organization_name": "Green Campus Collective",
        "organization_type": "College Club",
        "description": "A student-led group organizing environmental and community activities.",
        "official_email": "green@college.edu",
        "contact_number": "+91 9876543210",
        "department_affiliation": "Computer Science Department",
    }
    return {**values, **overrides}


def test_organization_registration_requires_authenticated_organizer(client):
    response = client.post("/organizations/register", data=organization_form())
    assert response.status_code == 401


def test_organization_registration_persists_pending_profile_and_document(client, tmp_path, monkeypatch):
    user_id, headers = seed_user(client)
    monkeypatch.setattr(person2_service, "UPLOAD_ROOT", tmp_path / "uploads")
    response = client.post(
        "/organizations/register", headers=headers, data=organization_form(),
        files={"supporting_document": ("approval.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["owner_id"] == user_id
    assert body["status"] == "PENDING"
    assert body["organization_type"] == "College Club"
    assert body["supporting_document_original_name"] == "approval.pdf"
    session = client.app.state.test_session_factory()
    stored_path = session.get(person2_service.Organization, body["id"]).supporting_document_path
    session.close()
    assert stored_path and (tmp_path / "uploads" / stored_path).exists()
    status_response = client.get("/organizations/me", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["id"] == body["id"]


def test_organization_registration_rejects_invalid_type_and_duplicate(client):
    _, headers = seed_user(client, email="first@college.edu")
    invalid = client.post("/organizations/register", headers=headers, data=organization_form(organization_type="Invalid"))
    assert invalid.status_code == 422
    assert client.post("/organizations/register", headers=headers, data=organization_form()).status_code == 201
    duplicate = client.post("/organizations/register", headers=headers, data=organization_form(organization_name="Another Name"))
    assert duplicate.status_code == 409


def test_admin_can_approve_registered_organization(client):
    _, organizer_headers = seed_user(client, email="approval-owner@college.edu")
    created = client.post("/organizations/register", headers=organizer_headers, data=organization_form(organization_name="Approval Group"))
    assert created.status_code == 201
    _, admin_headers = seed_user(client, role="ADMIN", email="admin@college.edu")
    decision = client.patch(
        f"/organizations/{created.json()['id']}/decision", headers=admin_headers,
        json={"status": "APPROVED", "review_note": "Verified by faculty."},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "APPROVED"
