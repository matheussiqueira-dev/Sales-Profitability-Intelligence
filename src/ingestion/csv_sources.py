import logging
from pathlib import Path

import pandas as pd

from src.validation.schemas import CONTRACTS

LOG = logging.getLogger(__name__)


def read_sources(path: Path) -> dict[str, pd.DataFrame]:
    sources = {}
    for name in CONTRACTS:
        frame = pd.read_csv(path / f"{name}.csv", dtype=str, keep_default_na=False)
        sources[name] = frame
        LOG.info("%s.csv: %s rows loaded", name, len(frame))
    return sources
