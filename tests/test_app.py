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
