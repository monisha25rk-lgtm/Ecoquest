from app.database.base import Base
from app.models.category import Category
from app.models.notification import Notification
from app.services.notification_service import notify_event_published


def test_notification_ownership_read_all_and_unread_count(client, student):
    factory = client.app.state.test_session_factory
    with factory() as db:
        db.add(Notification(user_id=student["user"]["id"], title="Update", message="An update"))
        db.commit()
        notification_id = db.query(Notification).first().id
    response = client.get("/notifications", headers=student["headers"])
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert client.get("/notifications/unread-count", headers=student["headers"]).json()["unread_count"] == 1
    assert client.patch(f"/notifications/{notification_id}/read").status_code == 401
    assert client.patch("/notifications/read-all", headers=student["headers"]).json()["updated_count"] == 1
    assert client.get("/notifications/unread-count", headers=student["headers"]).json()["unread_count"] == 0


def test_publication_notifications_are_idempotent(client, student):
    factory = client.app.state.test_session_factory
    event_table = Base.metadata.tables["events"]
    with factory() as db:
        category = db.query(Category).first()
        result = db.execute(
            event_table.insert().values(title="Published garden", category_id=category.id, status="PUBLISHED", capacity=10)
        )
        event_id = result.inserted_primary_key[0]
        db.commit()
        assert notify_event_published(db, event_id) == 1
        assert notify_event_published(db, event_id) == 0

    result = client.get("/notifications", headers=student["headers"])
    assert result.status_code == 200
    assert result.json()["total"] == 1
    assert result.json()["items"][0]["event_id"] == event_id
