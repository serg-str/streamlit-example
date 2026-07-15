from pathlib import Path

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

MLFLOW_DIR = Path("mlruns")
REGISTERED_MODEL_NAME = "steel_fault_predictor"
MODEL_ALIAS_BY_VERSION = {
    "2.0": "version_2_0",
    "3.0": "version_3_0",
}


def configure_mlflow_registry() -> None:
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(MLFLOW_DIR.resolve().as_uri())


def model_alias_for_version(version: str) -> str:
    cleaned = version.strip()
    if cleaned not in MODEL_ALIAS_BY_VERSION:
        supported = ", ".join(sorted(MODEL_ALIAS_BY_VERSION.keys()))
        raise ValueError(
            f"Unsupported model version '{version}' for alias mapping. "
            f"Supported versions: {supported}"
        )
    return MODEL_ALIAS_BY_VERSION[cleaned]


def ensure_registered_model_exists(client: MlflowClient) -> None:
    try:
        client.get_registered_model(REGISTERED_MODEL_NAME)
    except MlflowException:
        client.create_registered_model(REGISTERED_MODEL_NAME)


def ensure_model_alias_for_run(run_id: str, version_label: str) -> dict[str, str]:
    configure_mlflow_registry()
    client = MlflowClient()
    ensure_registered_model_exists(client)

    alias = model_alias_for_version(version_label)

    try:
        existing = client.get_model_version_by_alias(REGISTERED_MODEL_NAME, alias)
        return {
            "registered_model_name": REGISTERED_MODEL_NAME,
            "alias": alias,
            "registered_model_version": str(existing.version),
            "model_uri": f"models:/{REGISTERED_MODEL_NAME}@{alias}",
        }
    except MlflowException:
        pass

    created = mlflow.register_model(
        model_uri=f"runs:/{run_id}/model",
        name=REGISTERED_MODEL_NAME,
    )
    client.set_registered_model_alias(
        name=REGISTERED_MODEL_NAME,
        alias=alias,
        version=str(created.version),
    )

    return {
        "registered_model_name": REGISTERED_MODEL_NAME,
        "alias": alias,
        "registered_model_version": str(created.version),
        "model_uri": f"models:/{REGISTERED_MODEL_NAME}@{alias}",
    }


def get_model_uri_by_version_alias(version_label: str) -> str:
    configure_mlflow_registry()
    alias = model_alias_for_version(version_label)
    client = MlflowClient()
    model_version = client.get_model_version_by_alias(REGISTERED_MODEL_NAME, alias)
    return f"models:/{REGISTERED_MODEL_NAME}/{model_version.version}"
