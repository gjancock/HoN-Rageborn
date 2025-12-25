import json
from pathlib import Path

_DATASET_CACHE = {}

# project_root/utilities/datasetLoader.py
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "datasets"

def load_dataset(name: str):
    if name in _DATASET_CACHE:
        return _DATASET_CACHE[name]

    path = DATASET_DIR / f"{name}.json"

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _DATASET_CACHE[name] = data
    return data
