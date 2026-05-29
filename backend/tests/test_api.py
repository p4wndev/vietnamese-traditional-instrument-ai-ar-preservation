"""
Basic integration tests (no ML models required).
Run with: pytest tests/
"""

import pytest
from fastapi.testclient import TestClient

# Patch heavy model loading before importing app
import app.core.lifespan as lifespan_module

lifespan_module.state = {
    "yolo": None,
    "lenet": None,
    "ontology": None,
    "rag_chain": None,
}


@pytest.fixture(scope="module")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_instruments(client):
    response = client.get("/api/instruments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "description" in data[0]


def test_detect_image_no_file(client):
    response = client.post("/api/detect/image")
    assert response.status_code in (400, 422)


def test_rag_unavailable(client):
    response = client.post("/api/chatbot/rag", json={"question": "What is đàn bầu?"})
    # Expect 503 when RAG chain is not loaded
    assert response.status_code == 503


def test_ontology_invalid_class(client):
    response = client.get("/api/ontology/nonexistent_instrument")
    # Expect 503 (ontology not loaded) or 404 (invalid class)
    assert response.status_code in (404, 503)
