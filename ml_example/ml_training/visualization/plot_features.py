from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

if __name__ == "__main__":
    processed_path = Path("ml_example/data/processed/train_processed.csv")
    figure_path = Path("ml_example/visualization/train_processed_feature_hist.png")

    if not processed_path.exists():
        raise FileNotFoundError("Run ml_example.ml_training.features.build_features first")

    df = pd.read_csv(processed_path)
    columns = [
        "X_Range",
        "Y_Range",
        "Area_Perimeter_Ratio",
        "Luminosity_Range",
        "Volume",
        "Thickness_Deviation",
    ]
    df[columns].hist(figsize=(10, 8))
    plt.tight_layout()

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(figure_path)
    print(f"Figure written to {figure_path}")
