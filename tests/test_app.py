from fastapi.testclient import TestClient

from ml_example.fastapi_app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict() -> None:
    payload = {
        "X_Minimum": 584,
        "X_Maximum": 590,
        "Y_Minimum": 909972,
        "Y_Maximum": 909977,
        "Pixels_Areas": 16,
        "X_Perimeter": 8,
        "Y_Perimeter": 5,
        "Minimum_of_Luminosity": 113,
        "Maximum_of_Luminosity": 140,
        "Steel_Plate_Thickness": 50,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert "confidence" in response.json()
    assert "model_version" in response.json()


def test_model_info() -> None:
    response = client.get("/model-info")
    assert response.status_code == 200
    assert response.json()["name"] == "Steel Fault Predictor"


def test_train_data() -> None:
    response = client.get("/train-data", params={"limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert "rows" in body
    assert "row_count" in body
    assert "total_rows" in body
    assert body["row_count"] <= 10


def test_serving_model_info() -> None:
    response = client.get("/serving-model")
    assert response.status_code == 200
    body = response.json()
    assert "active_version" in body
    assert "mlflow_registered_model" in body
    assert "supported_versions" in body
    assert "2.0" in body["supported_versions"]
    assert "3.0" in body["supported_versions"]


def test_switch_serving_model() -> None:
    current = client.get("/serving-model").json()["active_version"]
    target = "3.0" if current != "3.0" else "2.0"

    try:
        switch_response = client.post("/serving-model", json={"version": target})
        assert switch_response.status_code == 200
        assert switch_response.json()["active_version"] == target

        verify_response = client.get("/serving-model")
        assert verify_response.status_code == 200
        assert verify_response.json()["active_version"] == target
    finally:
        client.post("/serving-model", json={"version": current})
