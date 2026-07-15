import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from ml_example.ml_training.pipeline.mlflow_registry import (
    REGISTERED_MODEL_NAME,
)
from ml_example.ml_training.pipeline.model_versions import (
    DEFAULT_MODEL_VERSION,
    model_paths_for_version,
)
from ml_example.ml_training.pipeline.predict import (
    get_serving_model_version,
    get_supported_model_versions,
    predict_fault_from_inputs,
    set_serving_model_version,
)

app = FastAPI(title="ML Example API", version="0.1.0")
RAW_TRAIN_PATH = Path("ml_example/data/raw/train.csv")


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


class ServingModelRequest(BaseModel):
    version: str = Field(..., description="Model version to serve, e.g. 2.0 or 3.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictionRequest) -> dict[str, object]:
    active_version = get_serving_model_version()
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
        model_version=active_version,
    )
    return {
        "prediction": str(result["prediction"]),
        "confidence": float(result["confidence"]),
        "class_probabilities": result.get("class_probabilities", {}),
        "model_version": str(result.get("model_version", active_version)),
    }


@app.get("/model-info")
def model_info(version: str | None = Query(default=None)) -> dict[str, object]:
    requested_version = version.strip() if version else get_serving_model_version()
    try:
        _, info_path = model_paths_for_version(requested_version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if info_path.exists():
        return json.loads(info_path.read_text(encoding="utf-8"))
    return {
        "name": "Steel Fault Predictor",
        "algorithm": "LightGBM",
        "version": requested_version,
        "training_date": "unknown",
        "training_samples": 0,
        "features": 0,
    }


@app.get("/serving-model")
def serving_model() -> dict[str, object]:
    active_version = get_serving_model_version()
    return {
        "active_version": active_version,
        "default_version": DEFAULT_MODEL_VERSION,
        "supported_versions": get_supported_model_versions(),
        "mlflow_registered_model": REGISTERED_MODEL_NAME,
    }


@app.post("/serving-model")
def set_serving_model(payload: ServingModelRequest) -> dict[str, object]:
    try:
        active_version = set_serving_model_version(payload.version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "active_version": active_version,
        "default_version": DEFAULT_MODEL_VERSION,
        "supported_versions": get_supported_model_versions(),
        "mlflow_registered_model": REGISTERED_MODEL_NAME,
    }


@app.get("/train-data")
def train_data(limit: int = Query(default=50000, ge=1, le=200000)) -> dict[str, object]:
    if not RAW_TRAIN_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Missing data file: {RAW_TRAIN_PATH}")

    df = pd.read_csv(RAW_TRAIN_PATH)
    total_rows = int(len(df))
    rows = df.head(limit).where(pd.notnull(df.head(limit)), None).to_dict(orient="records")

    return {
        "rows": rows,
        "row_count": int(len(rows)),
        "total_rows": total_rows,
    }
