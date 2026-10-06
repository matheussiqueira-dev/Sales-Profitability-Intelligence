import pandas as pd
import pytest

from scripts.generate_mock_data import generate
from src.validation.quality import validate_sources
from src.validation.schemas import CONTRACTS


@pytest.fixture
def sources():
    return {
        name: pd.DataFrame(rows, columns=list(CONTRACTS[name].columns))
        for name, rows in generate(42, 80, 20, 20).items()
    }


@pytest.fixture
def cleaned(sources):
    return validate_sources(sources)[0]
