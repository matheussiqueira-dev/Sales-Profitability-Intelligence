import hashlib
import json

import pandas as pd
import pytest

from scripts.generate_mock_data import generate, write_dataset
from src.analytics.publication import (
    PublicationError,
    atomic_output,
    publish_snapshot,
    save_json,
    verify_publication,
)
from src.config.settings import Settings
from src.database.loader import DIMENSIONS
from src.ingestion.csv_sources import read_sources_with_hashes


def test_hashes_describe_parsed_bytes_even_if_source_changes(tmp_path, monkeypatch):
    write_dataset(generate(42, 20, 10, 10), tmp_path)
    original = (tmp_path / "customers.csv").read_bytes()
    parse = pd.read_csv

    def mutate_after_read(*args, **kwargs):
        (tmp_path / "customers.csv").write_text("changed after capture", encoding="utf-8")
        return parse(*args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", mutate_after_read)
    frames, hashes = read_sources_with_hashes(tmp_path)
    assert len(frames["customers"]) == 10
    assert hashes["customers.csv"] == hashlib.sha256(original).hexdigest()
    assert (
        hashes["customers.csv"]
        != hashlib.sha256((tmp_path / "customers.csv").read_bytes()).hexdigest()
    )


def test_atomic_failure_preserves_previous_file_and_cleans_temporary(tmp_path):
    path = tmp_path / "snapshot.csv"
    path.write_text("previous complete file", encoding="utf-8")
    with pytest.raises(OSError, match="disk full"):
        with atomic_output(path) as temporary:
            temporary.write_text("partial", encoding="utf-8")
            raise OSError("disk full")
    assert path.read_text() == "previous complete file"
    assert list(tmp_path.iterdir()) == [path]
    save_json(tmp_path / "status.json", {"status": "published"})
    assert json.loads((tmp_path / "status.json").read_text()) == {"status": "published"}


@pytest.fixture
def publication_settings(tmp_path):
    return Settings("localhost", 1, "publication_test", "unused", "unused", processed_path=tmp_path)


def test_completion_marker_has_hashes_and_test_database_never_exports_web(
    publication_settings, monkeypatch
):
    monkeypatch.setattr(
        "src.analytics.publication.generate_insights", lambda _: {"alerts_count": 0}
    )

    def reject_web(*args):
        pytest.fail("Test databases must never write to the public web snapshot")

    monkeypatch.setattr("src.analytics.publication.export_web_snapshot", reject_web)
    frame = pd.DataFrame({"value": ["1.23"]})
    result = publish_snapshot(
        publication_settings, {}, frame, {}, {"passed": True}, "2026-10-08T12:00:00Z"
    )
    path = publication_settings.processed_path
    assert result["status"] == "published"
    assert result["web_snapshot"] is None
    assert (
        result["sha256"]["fact_sales.csv"]
        == hashlib.sha256((path / "fact_sales.csv").read_bytes()).hexdigest()
    )
    assert json.loads((path / "publication.json").read_text()) == result


def test_publication_failure_never_marks_bundle_complete(publication_settings, monkeypatch):
    monkeypatch.setattr(
        "src.analytics.publication.generate_insights", lambda _: {"alerts_count": 0}
    )
    path = publication_settings.processed_path / "fact_sales.csv"
    path.write_text("previous snapshot", encoding="utf-8")

    def fail_csv(self, destination, **kwargs):
        destination.write_text("partial", encoding="utf-8")
        raise OSError("disk full")

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail_csv)
    with pytest.raises(PublicationError, match="without reloading"):
        publish_snapshot(
            publication_settings, {}, pd.DataFrame(), {}, {"passed": True}, "committed"
        )
    assert path.read_text() == "previous snapshot"
    marker = json.loads((publication_settings.processed_path / "publication.json").read_text())
    assert marker["status"] == "publishing"
    assert not list(publication_settings.processed_path.glob(".*"))


def test_divergent_snapshot_cannot_publish(publication_settings):
    with pytest.raises(ValueError, match="Only reconciled"):
        publish_snapshot(publication_settings, {}, None, {}, {"passed": False}, "committed")
    assert not (publication_settings.processed_path / "publication.json").exists()


def test_csv_consumer_preflight_rejects_modified_or_incomplete_bundle(tmp_path):
    hashes = {}
    for name in [*DIMENSIONS, "fact_sales"]:
        path = tmp_path / f"{name}.csv"
        path.write_text("complete", encoding="utf-8")
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    marker = {"status": "published", "sha256": hashes}
    save_json(tmp_path / "publication.json", marker)
    assert verify_publication(tmp_path) == marker
    (tmp_path / "fact_sales.csv").write_text("corrupted", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_publication(tmp_path)
    save_json(tmp_path / "publication.json", {"status": "publishing"})
    with pytest.raises(ValueError, match="incomplete"):
        verify_publication(tmp_path)
