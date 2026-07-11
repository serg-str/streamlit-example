from pathlib import Path

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

TARGET_COLUMNS = ["Pastry", "Z_Scratch", "K_Scatch", "Stains", "Dirtiness", "Bumps", "Other_Faults"]


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.mean_thickness = X["Steel_Plate_Thickness"].mean()
        return self

    def transform(self, X):
        X = X.copy()
        X["X_Range"] = X["X_Maximum"] - X["X_Minimum"]
        X["Y_Range"] = X["Y_Maximum"] - X["Y_Minimum"]
        X["Area_Perimeter_Ratio"] = X["Pixels_Areas"] / (X["X_Perimeter"] + X["Y_Perimeter"])
        X["Luminosity_Range"] = X["Maximum_of_Luminosity"] - X["Minimum_of_Luminosity"]
        X["Volume"] = X["X_Range"] * X["Y_Range"] * X["Steel_Plate_Thickness"]
        X["Thickness_Deviation"] = X["Steel_Plate_Thickness"] - self.mean_thickness
        return X


def build_processed_data() -> tuple[Path, Path, float]:
    raw_train_path = Path("ml_example/data/raw/train.csv")
    raw_test_path = Path("ml_example/data/raw/test.csv")
    processed_train_path = Path("ml_example/data/processed/train_processed.csv")
    processed_test_path = Path("ml_example/data/processed/test_processed.csv")

    if not raw_train_path.exists():
        raise FileNotFoundError(f"Missing training data: {raw_train_path}")
    if not raw_test_path.exists():
        raise FileNotFoundError(f"Missing test data: {raw_test_path}")

    train_df = pd.read_csv(raw_train_path)
    test_df = pd.read_csv(raw_test_path)

    feature_engineer = FeatureEngineer()
    train_transformed = feature_engineer.fit_transform(train_df)
    test_transformed = feature_engineer.transform(test_df)

    if set(TARGET_COLUMNS).issubset(train_transformed.columns):
        train_transformed["target_label"] = train_transformed[TARGET_COLUMNS].idxmax(axis=1)

    processed_train_path.parent.mkdir(parents=True, exist_ok=True)
    train_transformed.to_csv(processed_train_path, index=False)
    test_transformed.to_csv(processed_test_path, index=False)

    return processed_train_path, processed_test_path, float(feature_engineer.mean_thickness)


if __name__ == "__main__":
    train_path, test_path, mean_thickness = build_processed_data()
    print(f"Processed training dataset written to {train_path}")
    print(f"Processed test dataset written to {test_path}")
    print(f"Mean steel thickness used for engineering: {mean_thickness:.4f}")
