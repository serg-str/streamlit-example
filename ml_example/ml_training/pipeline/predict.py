import csv
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote, urlparse

import lightgbm as lgb
import mlflow
import pandas as pd

from ml_example.ml_training.pipeline.mlflow_registry import (
    ensure_model_alias_for_run,
    get_model_uri_by_version_alias,
)
from ml_example.ml_training.pipeline.model_versions import (
    DEFAULT_MODEL_VERSION,
    SERVING_CONFIG_PATH,
    list_model_versions,
    model_paths_for_version,
    validate_model_version,
)

PREDICTION_LOG_PATH = Path("ml_example/reports/prediction_logs.csv")
MLFLOW_DIR = Path("mlruns")
MODEL_VERSION = DEFAULT_MODEL_VERSION
PREDICTION_LOG_COLUMNS = [
    "timestamp",
    "source",
    "prediction",
    "confidence",
    "true_label",
    "latency_ms",
]


def get_serving_model_version() -> str:
    if not SERVING_CONFIG_PATH.exists():
        return DEFAULT_MODEL_VERSION

    try:
        raw = json.loads(SERVING_CONFIG_PATH.read_text(encoding="utf-8"))
        return validate_model_version(str(raw.get("active_version", DEFAULT_MODEL_VERSION)))
    except (json.JSONDecodeError, ValueError):
        return DEFAULT_MODEL_VERSION


def set_serving_model_version(version: str) -> str:
    active_version = validate_model_version(version)
    SERVING_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SERVING_CONFIG_PATH.write_text(
        json.dumps({"active_version": active_version}, indent=2),
        encoding="utf-8",
    )
    return active_version


def get_supported_model_versions() -> list[str]:
    return list_model_versions()


def configure_mlflow() -> None:
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(MLFLOW_DIR.resolve().as_uri())


def _artifact_uri_to_path(artifact_uri: str) -> Path | None:
    parsed = urlparse(artifact_uri)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if not parsed.scheme:
        return Path(artifact_uri)
    return None


def _resolve_model_path(info: dict[str, object], default_model_path: Path) -> Path:
    artifact_uri = str(info.get("model_artifact_uri", "")).strip()
    if artifact_uri:
        artifact_path = _artifact_uri_to_path(artifact_uri)
        if artifact_path is not None and artifact_path.exists():
            return artifact_path

        configure_mlflow()
        downloaded_path = Path(mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri))
        if downloaded_path.exists():
            return downloaded_path

    return default_model_path


def preprocess_input_features(inputs: dict[str, float], mean_thickness: float) -> dict[str, float]:
    x_range = inputs["X_Maximum"] - inputs["X_Minimum"]
    y_range = inputs["Y_Maximum"] - inputs["Y_Minimum"]
    area_perimeter_ratio = inputs["Pixels_Areas"] / (inputs["X_Perimeter"] + inputs["Y_Perimeter"])
    luminosity_range = inputs["Maximum_of_Luminosity"] - inputs["Minimum_of_Luminosity"]
    volume = x_range * y_range * inputs["Steel_Plate_Thickness"]
    thickness_deviation = inputs["Steel_Plate_Thickness"] - mean_thickness

    return {
        "X_Range": float(x_range),
        "Y_Range": float(y_range),
        "Area_Perimeter_Ratio": float(area_perimeter_ratio),
        "Luminosity_Range": float(luminosity_range),
        "Volume": float(volume),
        "Thickness_Deviation": float(thickness_deviation),
    }


def _load_model(model_version: str = MODEL_VERSION):
    validated_version = validate_model_version(model_version)
    model_path, model_info_path = model_paths_for_version(validated_version)

    if not model_path.exists() or not model_info_path.exists():
        from ml_example.ml_training.pipeline.train import train_model

        train_model(version=validated_version)

    info = json.loads(model_info_path.read_text(encoding="utf-8"))
    model = None

    try:
        model_uri = get_model_uri_by_version_alias(validated_version)
        model = mlflow.lightgbm.load_model(model_uri=model_uri)
    except Exception:
        run_id = str(info.get("mlflow_run_id", "")).strip()
        if run_id:
            try:
                ensure_model_alias_for_run(run_id=run_id, version_label=validated_version)
                model_uri = get_model_uri_by_version_alias(validated_version)
                model = mlflow.lightgbm.load_model(model_uri=model_uri)
            except Exception:
                model = None

    if model is None:
        resolved_model_path = _resolve_model_path(info, model_path)
        model = lgb.Booster(model_file=str(resolved_model_path))

    return {
        "model": model,
        "mean_thickness": float(info["mean_thickness"]),
        "feature_columns": list(info["feature_columns"]),
        "classes": list(info["classes"]),
        "model_version": str(info.get("version", validated_version)),
    }


def _append_prediction_log(
    source: str,
    prediction: str,
    confidence: float,
    latency_ms: float | None = None,
) -> None:
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "prediction": prediction,
        "confidence": confidence,
        "true_label": "",
        "latency_ms": latency_ms if latency_ms is not None else "",
    }
    PREDICTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing_rows: list[dict[str, object]] = []
    if PREDICTION_LOG_PATH.exists():
        with PREDICTION_LOG_PATH.open("r", encoding="utf-8", newline="") as src:
            reader = csv.reader(src)
            all_rows = list(reader)

        if all_rows:
            header = all_rows[0]
            has_header = "timestamp" in header and "prediction" in header
            data_rows = all_rows[1:] if has_header else all_rows
            index_by_name = {name: idx for idx, name in enumerate(header)} if has_header else {}

            for raw in data_rows:
                if not raw:
                    continue
                normalized = {col: "" for col in PREDICTION_LOG_COLUMNS}
                if has_header:
                    for col in PREDICTION_LOG_COLUMNS:
                        idx = index_by_name.get(col)
                        if idx is not None and idx < len(raw):
                            normalized[col] = raw[idx]
                else:
                    # Fallback for very old rows without a header.
                    if len(raw) > 0:
                        normalized["timestamp"] = raw[0]
                    if len(raw) > 1:
                        normalized["source"] = raw[1]
                    if len(raw) > 2:
                        normalized["prediction"] = raw[2]
                    if len(raw) > 3:
                        normalized["confidence"] = raw[3]
                    if len(raw) > 4:
                        normalized["latency_ms"] = raw[4]
                existing_rows.append(normalized)

    existing_rows.append({col: row.get(col, "") for col in PREDICTION_LOG_COLUMNS})
    pd.DataFrame(existing_rows, columns=PREDICTION_LOG_COLUMNS).to_csv(
        PREDICTION_LOG_PATH,
        index=False,
    )


def predict_fault_from_inputs(
    X_Minimum: float,
    X_Maximum: float,
    Y_Minimum: float,
    Y_Maximum: float,
    Pixels_Areas: float,
    X_Perimeter: float,
    Y_Perimeter: float,
    Minimum_of_Luminosity: float,
    Maximum_of_Luminosity: float,
    Steel_Plate_Thickness: float,
    source: str = "UI",
    model_version: str = MODEL_VERSION,
) -> dict[str, float | str]:
    start = perf_counter()
    bundle = _load_model(model_version=model_version)
    model = bundle["model"]
    mean_thickness = float(bundle["mean_thickness"])
    feature_columns = list(bundle["feature_columns"])

    engineered = preprocess_input_features(
        {
            "X_Minimum": X_Minimum,
            "X_Maximum": X_Maximum,
            "Y_Minimum": Y_Minimum,
            "Y_Maximum": Y_Maximum,
            "Pixels_Areas": Pixels_Areas,
            "X_Perimeter": X_Perimeter,
            "Y_Perimeter": Y_Perimeter,
            "Minimum_of_Luminosity": Minimum_of_Luminosity,
            "Maximum_of_Luminosity": Maximum_of_Luminosity,
            "Steel_Plate_Thickness": Steel_Plate_Thickness,
        },
        mean_thickness=mean_thickness,
    )
    sample = pd.DataFrame([[engineered[col] for col in feature_columns]], columns=feature_columns)

    probabilities = model.predict(sample)[0]
    best_idx = int(probabilities.argmax())
    classes = list(bundle["classes"])
    prediction_label = str(classes[best_idx])
    confidence = float(probabilities.max())
    class_probabilities = {
        str(label): float(prob)
        for label, prob in sorted(
            zip(classes, probabilities, strict=False), key=lambda x: x[1], reverse=True
        )
    }
    latency_ms = (perf_counter() - start) * 1000.0
    log_latency = latency_ms if source in {"UI", "API"} else None
    _append_prediction_log(
        source=source,
        prediction=prediction_label,
        confidence=confidence,
        latency_ms=log_latency,
    )

    return {
        "prediction": prediction_label,
        "confidence": confidence,
        "model_version": str(bundle["model_version"]),
        "latency_ms": latency_ms,
        "class_probabilities": class_probabilities,
        "X_Range": engineered["X_Range"],
        "Y_Range": engineered["Y_Range"],
        "Area_Perimeter_Ratio": engineered["Area_Perimeter_Ratio"],
        "Luminosity_Range": engineered["Luminosity_Range"],
        "Volume": engineered["Volume"],
        "Thickness_Deviation": engineered["Thickness_Deviation"],
    }


if __name__ == "__main__":
    pred = predict_fault_from_inputs(
        X_Minimum=584,
        X_Maximum=590,
        Y_Minimum=909972,
        Y_Maximum=909977,
        Pixels_Areas=16,
        X_Perimeter=8,
        Y_Perimeter=5,
        Minimum_of_Luminosity=113,
        Maximum_of_Luminosity=140,
        Steel_Plate_Thickness=50,
    )
    print(f"Prediction: {pred}")
