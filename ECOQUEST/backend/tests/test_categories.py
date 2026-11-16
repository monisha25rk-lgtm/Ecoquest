from app.database.connection import initialize_database
from app.models.category import CATEGORY_NAMES


def test_all_categories_are_seeded_once(client):
    engine = client.app.state.test_session_factory.kw["bind"]
    first = client.get("/categories")
    initialize_database(engine)
    second = client.get("/categories")
    assert first.status_code == second.status_code == 200
    assert len(first.json()) == len(CATEGORY_NAMES) == 15
    assert [item["name"] for item in first.json()] == list(CATEGORY_NAMES)
    assert len(second.json()) == 15
