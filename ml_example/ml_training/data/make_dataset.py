from pathlib import Path

REQUIRED_FILES = [Path("ml_example/data/raw/train.csv"), Path("ml_example/data/raw/test.csv")]


if __name__ == "__main__":
    missing = [path for path in REQUIRED_FILES if not path.exists()]
    if missing:
        missing_list = ", ".join(str(item) for item in missing)
        raise FileNotFoundError(f"Missing raw dataset files: {missing_list}")
    print("Raw steel dataset is already present under ml_example/data/raw")
