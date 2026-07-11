import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ml_example.ml_training.pipeline.predict import MODEL_VERSION, predict_fault_from_inputs

app = FastAPI(title="ML Example API", version="0.1.0")
MODEL_INFO_PATH = Path("ml_example/ml_training/models/model_info.json")


class PredictionRequest(BaseModel):
    X_Minimum: float = Field(...)
    X_Maximum: float = Field(...)
    Y_Minimum: float = Field(...)
    Y_Maximum: float = Field(...)
    Pixels_Areas: float = Field(..., gt=0)
    X_Perimeter: float = Field(..., gt=0)
    Y_Perimeter: float = Field(..., gt=0)
    Minimum_of_Luminosity: float = Field(..., ge=0)
    Maximum_of_Luminosity: float = Field(..., ge=0)
    Steel_Plate_Thickness: float = Field(..., gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictionRequest) -> dict[str, object]:
    result = predict_fault_from_inputs(
        X_Minimum=payload.X_Minimum,
        X_Maximum=payload.X_Maximum,
        Y_Minimum=payload.Y_Minimum,
        Y_Maximum=payload.Y_Maximum,
        Pixels_Areas=payload.Pixels_Areas,
        X_Perimeter=payload.X_Perimeter,
        Y_Perimeter=payload.Y_Perimeter,
        Minimum_of_Luminosity=payload.Minimum_of_Luminosity,
        Maximum_of_Luminosity=payload.Maximum_of_Luminosity,
        Steel_Plate_Thickness=payload.Steel_Plate_Thickness,
        source="API",
    )
    return {
        "prediction": str(result["prediction"]),
        "confidence": float(result["confidence"]),
        "class_probabilities": result.get("class_probabilities", {}),
        "model_version": MODEL_VERSION,
    }


@app.get("/model-info")
def model_info() -> dict[str, object]:
    if MODEL_INFO_PATH.exists():
        return json.loads(MODEL_INFO_PATH.read_text(encoding="utf-8"))
    return {
        "name": "Steel Fault Predictor",
        "algorithm": "LightGBM",
        "version": MODEL_VERSION,
        "training_date": "unknown",
        "training_samples": 0,
        "features": 0,
    }
