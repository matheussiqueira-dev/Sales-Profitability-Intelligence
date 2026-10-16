import hashlib
import logging
from io import BytesIO
from pathlib import Path

import pandas as pd

from src.validation.schemas import CONTRACTS

LOG = logging.getLogger(__name__)


def read_sources(path: Path) -> dict[str, pd.DataFrame]:
    return read_sources_with_hashes(path)[0]


def read_sources_with_hashes(path: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Fingerprint the parsed bytes; producers must publish a complete batch first."""
    sources = {}
    hashes = {}
    for name in CONTRACTS:
        content = (path / f"{name}.csv").read_bytes()
        hashes[f"{name}.csv"] = hashlib.sha256(content).hexdigest()
        frame = pd.read_csv(BytesIO(content), dtype=str, keep_default_na=False)
        sources[name] = frame
        LOG.info("%s.csv: %s rows loaded", name, len(frame))
    return sources, hashes
