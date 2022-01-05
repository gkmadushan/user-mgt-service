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


def test_get_users():
    response = client.get("/v1/users")
    assert response.status_code == 200


def test_get_users_404():
    response = client.get("/v1/users?email=xxxxxxxx")
    assert response.json()['meta']['total_records'] == 0


def test_get_user_404():
    response = client.get("/v1/users/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 404


def test_create_user_201():
    response = client.post("/v1/users", json={
        "id": "4f07cf23-cd0f-42b5-99c4-efa9022adccf",
        "email": "test@testuser.com",
        "name": "Test user",
        "role": "fc045343-8fd1-4351-9ec6-27d2ee52b34d",
        "groups": []
    })
    assert response.json() == {'success': True}
    assert response.status_code == 200


def test_get_user_200():
    response = client.get("/v1/users/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 200


def test_update_user_200():
    response = client.put("/v1/users/4f07cf23-cd0f-42b5-99c4-efa9022adccf", json={
        "name": "Test User 2",
        "role": "fc045343-8fd1-4351-9ec6-27d2ee52b34d"
    })
    assert response.status_code == 200


def test_delete_user_204():
    response = client.delete("/v1/users/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 204
