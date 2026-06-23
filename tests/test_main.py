"""
Tests for the main module
"""

from furever_match.main import app


def test_app_initialization():
    assert app is not None
    assert isinstance(app.config, dict)


def test_health_check():
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "message": "FureverMatch API is running",
    }
