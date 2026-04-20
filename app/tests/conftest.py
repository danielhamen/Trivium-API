import json
from pathlib import Path

import pytest
from app.repository import DataRepository
from fastapi.testclient import TestClient

from app.main import app, repo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CATEGORIES_PATH = DATA_DIR / "categories.json"
QUESTIONS_PATH = DATA_DIR / "questions.json"


@pytest.fixture(scope="session")
def categories_json():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def questions_json():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def repository() -> DataRepository:
    return DataRepository().fetch()


@pytest.fixture(scope="session")
def client():
    repo.fetch()
    return TestClient(app)
