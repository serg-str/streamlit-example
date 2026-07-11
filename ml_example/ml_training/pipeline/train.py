import json
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
from lightgbm import LGBMClassifier

from ml_example.ml_training.features.build_features import build_processed_data

MODEL_PATH = Path("ml_example/ml_training/models/steel_fault_lgbm.lgb")
TRAINING_PREDICTIONS_PATH = Path("ml_example/reports/training_predictions.csv")
MODEL_INFO_PATH = Path("ml_example/ml_training/models/model_info.json")
MLFLOW_DIR = Path("mlruns")
MLFLOW_EXPERIMENT_NAME = "steel-fault-predictor"
FEATURE_COLUMNS = [
    "X_Range",
    "Y_Range",
    "Area_Perimeter_Ratio",
    "Luminosity_Range",
    "Volume",
    "Thickness_Deviation",
]


def configure_mlflow() -> str:
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    tracking_uri = MLFLOW_DIR.resolve().as_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    return tracking_uri


def train_model() -> Path:
    processed_train_path, _, mean_thickness = build_processed_data()
    train_df = pd.read_csv(processed_train_path)

    if "target_label" not in train_df.columns:
        raise ValueError("Processed training data missing target_label column")

    model_df = train_df.dropna(subset=FEATURE_COLUMNS + ["target_label"]).copy()
    X_train = model_df[FEATURE_COLUMNS]
    y_train = model_df["target_label"]

    model = LGBMClassifier(
        objective="multiclass",
        random_state=42,
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    train_probabilities = model.predict_proba(X_train)
    train_prediction_labels = model.predict(X_train)
    confidence = train_probabilities.max(axis=1)

    training_predictions = model_df[["id", "target_label"]].copy()
    training_predictions["prediction"] = train_prediction_labels
    training_predictions["true_label"] = training_predictions["target_label"]
    training_predictions["confidence"] = confidence
    training_predictions["latency_ms"] = ""
    training_predictions["source"] = "TRAINING"
    training_predictions["timestamp"] = datetime.utcnow().isoformat()

    TRAINING_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    training_predictions.to_csv(TRAINING_PREDICTIONS_PATH, index=False)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(MODEL_PATH))

    tracking_uri = configure_mlflow()
    train_accuracy = float((train_prediction_labels == y_train).mean())
    timestamp = datetime.utcnow()

    run_name = f"steel-fault-train-{timestamp.strftime('%Y%m%d-%H%M%S')}"
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(
            {
                "objective": "multiclass",
                "random_state": 42,
                "n_estimators": 200,
                "learning_rate": 0.05,
                "num_leaves": 31,
                "class_weight": "balanced",
                "feature_count": len(FEATURE_COLUMNS),
            }
        )
        mlflow.log_metric("train_accuracy", train_accuracy)
        mlflow.log_metric("training_samples", float(len(model_df)))
        mlflow.log_artifact(str(MODEL_PATH), artifact_path="model")

        model_artifact_uri = mlflow.get_artifact_uri(f"model/{MODEL_PATH.name}")

    model_info = {
        "name": "Steel Fault Predictor",
        "algorithm": "LightGBM",
        "version": "v2.0",
        "training_date": timestamp.strftime("%Y-%m-%d"),
        "training_samples": int(len(model_df)),
        "features": int(len(FEATURE_COLUMNS)),
        "feature_columns": FEATURE_COLUMNS,
        "mean_thickness": float(mean_thickness),
        "classes": [str(item) for item in model.classes_],
        "model_path": str(MODEL_PATH),
        "mlflow_tracking_uri": tracking_uri,
        "mlflow_experiment": MLFLOW_EXPERIMENT_NAME,
        "mlflow_run_id": run.info.run_id,
        "model_artifact_uri": model_artifact_uri,
    }
    MODEL_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_INFO_PATH.write_text(json.dumps(model_info, indent=2), encoding="utf-8")
    return MODEL_PATH


if __name__ == "__main__":
    model_path = train_model()
    print(f"Model saved to {model_path}")
