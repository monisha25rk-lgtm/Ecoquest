from datetime import datetime, timedelta, timezone

from sqlalchemy import insert

from app.database.base import Base
from app.models.category import Category


def add_event(client, status, title, *, capacity=3, deadline_days=2, organization_id=None):
    factory = client.app.state.test_session_factory
    events = Base.metadata.tables["events"]
    with factory() as db:
        category = db.query(Category).first()
        db.execute(
            insert(events).values(
                title=title,
                description=f"Description for {title}",
                organization_id=organization_id,
                category_id=category.id,
                start_date=datetime.now(timezone.utc) + timedelta(days=4),
                end_date=datetime.now(timezone.utc) + timedelta(days=5),
                venue="Campus",
                registration_deadline=datetime.now(timezone.utc) + timedelta(days=deadline_days),
                capacity=capacity,
                status=status,
                approved_eco_points=10,
            )
        )
        db.commit()
        return db.execute(events.select().where(events.c.title == title)).mappings().one()["id"]


def test_only_published_events_are_discoverable(client):
    published_id = add_event(client, "PUBLISHED", "Water restoration")
    add_event(client, "PENDING", "Hidden proposal")
    add_event(client, "REJECTED", "Rejected proposal")

    response = client.get("/events?search=water")
    assert response.status_code == 200
    assert [event["id"] for event in response.json()["items"]] == [published_id]
    assert client.get("/events/2").status_code == 404


def test_category_filter_and_unavailable_integration(client):
    add_event(client, "PUBLISHED", "Campus garden")
    category_id = client.get("/categories").json()[0]["id"]
    response = client.get(f"/events?category_id={category_id}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_search_matches_organization_name(client):
    factory = client.app.state.test_session_factory
    organizations = Base.metadata.tables["organizations"]
    with factory() as db:
        organization_id = db.execute(
            insert(organizations).values(name="River Care Collective")
        ).inserted_primary_key[0]
        db.commit()
    add_event(client, "PUBLISHED", "Native planting day", organization_id=organization_id)

    response = client.get("/events?search=River%20Care")
    assert response.status_code == 200
    assert response.json()["items"][0]["organization_name"] == "River Care Collective"
