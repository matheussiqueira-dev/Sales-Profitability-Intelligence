"""Bootstrap dataset without overwriting any existing source files."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_mock_data import generate, write_dataset  # noqa: E402
from src.config.settings import ROOT  # noqa: E402
from src.validation.schemas import CONTRACTS  # noqa: E402


def main():
    load_dotenv(ROOT / ".env", override=False)
    path = ROOT / os.getenv("DATA_RAW_PATH", "data/raw")
    present = [(path / f"{name}.csv").exists() for name in CONTRACTS]
    if any(present) and not all(present):
        raise ValueError("Partial dataset: preserve files and complete or choose another path")
    if not any(present):
        if path.exists() and any(path.glob("*.csv")):
            raise ValueError("Unrecognized CSV files exist; choose another directory")
        write_dataset(generate(seed=int(os.getenv("RANDOM_SEED", "42"))), path)
    else:
        logging.info("Existing dataset preserved")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    main()
