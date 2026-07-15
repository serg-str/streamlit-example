from pathlib import Path

DEFAULT_MODEL_VERSION = "2.0"
MODEL_VERSION_REGISTRY = {
    "2.0": {
        "model_path": Path("ml_example/ml_training/models/steel_fault_lgbm.lgb"),
        "info_path": Path("ml_example/ml_training/models/model_info.json"),
    },
    "3.0": {
        "model_path": Path("ml_example/ml_training/models/steel_fault_lgbm_v3.lgb"),
        "info_path": Path("ml_example/ml_training/models/model_info_v3.json"),
    },
}
SERVING_CONFIG_PATH = Path("ml_example/ml_training/models/serving_config.json")


def list_model_versions() -> list[str]:
    return sorted(MODEL_VERSION_REGISTRY.keys())


def validate_model_version(version: str) -> str:
    cleaned = version.strip()
    if cleaned.lower().startswith("v"):
        cleaned = cleaned[1:]
    if cleaned not in MODEL_VERSION_REGISTRY:
        supported = ", ".join(list_model_versions())
        raise ValueError(f"Unsupported model version '{version}'. Supported versions: {supported}")
    return cleaned


def model_paths_for_version(version: str) -> tuple[Path, Path]:
    valid_version = validate_model_version(version)
    metadata = MODEL_VERSION_REGISTRY[valid_version]
    return metadata["model_path"], metadata["info_path"]
