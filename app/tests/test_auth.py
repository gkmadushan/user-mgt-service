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


def test_refresh_token_400():
    response = client.post("/oauth/refresh-token")
    assert response.status_code == 400


def test_verify_token_405():
    response = client.post("/users/4f07cf23-cd0f-42b5-99c4-efa9022adccf/verify/4f07cf23-cd0f-42b5-99c4-efa9022adccf")
    assert response.status_code == 405
