"""
Integration and Unit Tests for Phase 9: FastAPI Layer and Web Endpoints.
Tests health checks, JSON audit endpoint, clean swaps directory, and static SPA serving.
"""

import pytest
from fastapi.testclient import TestClient
from bitecheck.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    """Verifies that the /health endpoint responds with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "BiteCheck India"


def test_swaps_endpoint(client):
    """Verifies that the /api/swaps endpoint returns Indian FMCG categories."""
    response = client.get("/api/swaps")
    assert response.status_code == 200
    swaps = response.json()
    assert "cookies_and_biscuits" in swaps
    assert "noodles_and_pasta" in swaps
    assert len(swaps["cookies_and_biscuits"]) > 0


def test_audit_json_endpoint(client):
    """Verifies that the /api/audit/json endpoint executes the multi-agent graph."""
    payload = {
        "brand_name": "GoodBite",
        "product_name": "Diet Oats Biscuit",
        "front_claims": ["Rich in Oats", "Zero Added Sugar"],
        "ingredients_raw": ["Refined Wheat Flour (Maida) 55%", "Palm Oil", "Maltodextrin", "Oats 4%", "Salt"],
        "net_weight_g": 100.0,
        "serving_size_g": 20.0,
        "nutrition_per_100g": {
            "energy_kcal": 450.0,
            "fat_g": 18.0,
            "saturated_fat_g": 8.0,
            "trans_fat_g": 0.0,
            "carbohydrates_g": 68.0,
            "dietary_fiber_g": 2.0,
            "sugar_g": 1.0,
            "added_sugar_g": 0.0,
            "sodium_mg": 550.0,
            "protein_g": 5.0,
        },
        "fssai_license_number": "10012011000123",
        "dietary_dot": "GREEN_VEG",
    }

    response = client.post("/api/audit/json", json=payload)
    assert response.status_code == 200
    state = response.json()

    assert state["current_step"] == "COMPLETED"
    assert state["scorecard"] is not None
    assert state["transparency_card"] is not None
    assert state["scorecard"]["honesty_score"] < 60
    assert len(state["transparency_card"]["clean_swaps"]) > 0


def test_serve_index_html(client):
    """Verifies that GET / serves the single page application HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BiteCheck" in response.text
    assert "FSSAI Honesty Score" in response.text
