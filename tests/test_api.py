import pytest
from fastapi.testclient import TestClient

from api.main import app

EXAMPLE = {
    "loan_amnt": 12000,
    "purpose": "debt_consolidation",
    "annual_inc": 55000,
    "fico": 690,
    "dti": 18.5,
    "credit_years": 12,
    "emp_length": "10+ years",
    "home_ownership": "RENT",
    "addr_state": "CA",
    "acc_open_past_24mths": 4,
    "inq_last_6mths": 1,
    "revol_util": 45,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_returns_valid_answer(client):
    response = client.post("/predict", json=EXAMPLE)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["probability"] <= 1
    assert body["decision"] in {"Approve", "Review", "Reject"}
    assert len(body["top_reasons"]) == 5


def test_known_applicant_score(client):
    response = client.post("/predict", json={**EXAMPLE, "issue_date": "2026-11-17"})
    assert response.json()["probability"] == pytest.approx(0.1052, abs=0.001)


def test_decision_follows_policy(client):
    risky = {**EXAMPLE, "loan_amnt": 35000, "annual_inc": 20000, "dti": 40,
             "acc_open_past_24mths": 15, "inq_last_6mths": 5, "fico": 660}
    body = client.post("/predict", json=risky).json()
    p = body["probability"]
    if p >= body["cutoff"]:
        expected = "Reject"
    elif p >= body["review_from"]:
        expected = "Review"
    else:
        expected = "Approve"
    assert body["decision"] == expected
    if expected == "Approve":
        assert body["reasons_against"] == []
    else:
        assert len(body["reasons_against"]) > 0


@pytest.mark.parametrize("change", [
    {"fico": 2000},
    {"fico": "abc"},
    {"loan_amnt": 50000},
    {"annual_inc": 0},
    {"emp_length": "five years"},
    {"addr_state": "XX"},
    {"extra": {"open_accc": 5}},
])
def test_invalid_input_is_rejected(client, change):
    response = client.post("/predict", json={**EXAMPLE, **change})
    assert response.status_code == 422


def test_missing_field_is_rejected(client):
    data = dict(EXAMPLE)
    del data["dti"]
    assert client.post("/predict", json=data).status_code == 422


def test_lowercase_state_is_accepted(client):
    response = client.post("/predict", json={**EXAMPLE, "addr_state": "ca"})
    assert response.status_code == 200