from fastapi.testclient import TestClient

from taberu_mate_backend.main import app


def test_health_check() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "TaberuMate API",
        "environment": "local",
        "version": "0.1.0",
    }


def test_root_points_to_docs_and_health() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to TaberuMate API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
