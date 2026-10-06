import json
from dataclasses import replace

import pytest

from scripts.generate_mock_data import generate, write_dataset
from src.config.settings import Settings
from src.pipeline import run
from src.validation.quality import QualityError


def test_validate_only_never_connects_and_rejects_bad_source(tmp_path, monkeypatch):
    settings = Settings(
        "127.0.0.1",
        1,
        "unused",
        "unused",
        "test_only",
        raw_path=tmp_path / "raw",
        processed_path=tmp_path / "processed",
    )
    write_dataset(generate(42, 20, 10, 10), settings.raw_path)

    def no_connection(settings):
        pytest.fail("Source-only validation must not connect to PostgreSQL")

    monkeypatch.setattr("src.pipeline.engine_for", no_connection)
    assert run(settings, validate_only=True)["passed"]
    broken = generate(42, 20, 10, 10)
    broken["order_items"][0]["quantity"] = 0
    write_dataset(broken, settings.raw_path)
    with pytest.raises(QualityError):
        run(replace(settings), validate_only=True)
    report = json.loads(
        (settings.processed_path / "quality-report.json").read_text(encoding="utf-8")
    )
    assert not report["passed"]
