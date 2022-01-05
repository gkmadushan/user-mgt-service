import importlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from utils.database import Base
from dependencies import get_db, get_token_header


def override_get_token_header():
    return True


app.dependency_overrides[get_token_header] = override_get_token_header

client = TestClient(app)


def test_get_groups():
    response = client.get("/v1/groups")
    assert response.status_code == 200


def test_get_groups_404():
    response = client.get("/v1/groups?group=xxxxxxxx")
    assert response.json()['meta']['total_records'] == 0


def test_get_group_404():
    response = client.get("/v1/groups/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 404


def test_create_group_201():
    response = client.post("/v1/groups", json={
        "id": "4f07cf23-cd0f-42b5-99c4-efa9022adccf",
        "name": "Test Group",
        "description": "Test Group Description"
    })
    assert response.json() == {'success': True}
    assert response.status_code == 200


def test_get_group_200():
    response = client.get("/v1/groups/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 200


def test_update_group_200():
    response = client.put("/v1/groups/4f07cf23-cd0f-42b5-99c4-efa9022adccf", json={
        "name": "Test Group 2",
        "description": "Test Group Description 2"
    })
    assert response.status_code == 200


def test_delete_group_204():
    response = client.delete("/v1/groups/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 204
