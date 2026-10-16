"""Initialize empty/owned schemas without loading data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402
from src.database.lease import warehouse_lease  # noqa: E402
from src.database.loader import initialize  # noqa: E402

if __name__ == "__main__":
    engine = engine_for(Settings.from_env())
    try:
        with warehouse_lease(engine) as connection:
            with connection.begin():
                initialize(connection)
    finally:
        engine.dispose()
