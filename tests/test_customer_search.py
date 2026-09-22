import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "app")
    )
)

from app import app


def test_customer_search_by_city():
    client = app.test_client()

    response = client.get("/customers/search?q=Hyderabad")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert data["customers"][0]["city"] == "Hyderabad"


def test_customer_search_by_name():
    client = app.test_client()

    response = client.get("/customers/search?q=Ravi")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["customers"][0]["name"] == "Ravi Kumar"


def test_customer_search_requires_query():
    client = app.test_client()

    response = client.get("/customers/search")

    assert response.status_code == 400