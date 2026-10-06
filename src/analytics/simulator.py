"""Command-line simulation using the latest committed warehouse snapshot."""

import argparse
import json

from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.loader import read_fact
from src.transformation.financial_metrics import simulate_discount


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discount", required=True, help="Fraction, e.g. 0.18 for 18%%")
    args = parser.parse_args()
    engine = engine_for(Settings.from_env())
    try:
        with engine.connect() as connection:
            result = simulate_discount(read_fact(connection), args.discount)
        print(json.dumps(result, indent=2, default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
