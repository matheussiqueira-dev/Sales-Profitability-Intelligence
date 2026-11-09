"""Warehouse lease and loader guards with fake connections (no PostgreSQL needed)."""

from contextlib import contextmanager

import pytest

from src.database import loader
from src.database.lease import PIPELINE_LOCK, warehouse_lease


class FakeResult:
    def __init__(self, value=None):
        self.value = value

    def scalar_one(self):
        return self.value

    def one_or_none(self):
        return self.value


class FakeConnection:
    """Records SQL and lets a test make commit or rollback fail."""

    def __init__(self, lock_acquired=True, metadata=None):
        self.lock_acquired = lock_acquired
        self.metadata = metadata
        self.statements = []
        self.commits = 0
        self.invalidated = False
        self.fail_commit_at = None
        self.fail_rollback = False

    def execute(self, clause, params=None):
        sql = str(clause)
        self.statements.append(sql)
        if "pg_try_advisory_lock" in sql:
            assert params == {"key": PIPELINE_LOCK}
            return FakeResult(self.lock_acquired)
        if "pipeline_metadata" in sql and sql.lstrip().upper().startswith("SELECT"):
            return FakeResult(self.metadata)
        return FakeResult()

    def commit(self):
        self.commits += 1
        if self.fail_commit_at == self.commits:
            raise RuntimeError("commit failed")

    def rollback(self):
        if self.fail_rollback:
            raise RuntimeError("rollback failed")

    def invalidate(self):
        self.invalidated = True


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def connect(self):
        yield self.connection


def _ran(connection, fragment):
    return any(fragment in sql for sql in connection.statements)


def test_lease_holds_the_lock_and_releases_it():
    connection = FakeConnection()

    with warehouse_lease(FakeEngine(connection)) as leased:
        assert leased is connection
        assert not _ran(connection, "pg_advisory_unlock")

    assert _ran(connection, "pg_advisory_unlock")
    assert connection.commits == 2
    assert connection.invalidated is False


def test_lease_refuses_when_another_writer_holds_the_lock():
    connection = FakeConnection(lock_acquired=False)

    with pytest.raises(RuntimeError, match="Another pipeline"):
        with warehouse_lease(FakeEngine(connection)):
            pytest.fail("the body must not run without the lock")

    assert not _ran(connection, "pg_advisory_unlock")


def test_lease_invalidates_the_connection_when_the_first_commit_fails():
    connection = FakeConnection()
    connection.fail_commit_at = 1

    with pytest.raises(RuntimeError, match="commit failed"):
        with warehouse_lease(FakeEngine(connection)):
            pytest.fail("the body must not run after a failed commit")

    assert connection.invalidated is True


def test_lease_invalidates_the_connection_when_release_fails():
    connection = FakeConnection()
    connection.fail_rollback = True

    with pytest.raises(RuntimeError, match="rollback failed"):
        with warehouse_lease(FakeEngine(connection)):
            pass

    assert connection.invalidated is True


def test_read_statements_drops_comments_and_empty_statements():
    statements = loader.read_statements("01_create_schemas.sql")

    assert statements
    assert all(statement.strip() for statement in statements)
    assert not any(line.lstrip().startswith("--") for s in statements for line in s.splitlines())


def test_execute_file_runs_every_statement():
    connection = FakeConnection()

    loader.execute_file(connection, "04_create_indexes.sql")

    assert len(connection.statements) == len(loader.read_statements("04_create_indexes.sql"))


class FakeInspector:
    def __init__(self, tables):
        self.tables = tables

    def get_schema_names(self):
        return list(self.tables)

    def get_table_names(self, schema):
        return self.tables[schema]


def _initialize(monkeypatch, tables, metadata=None):
    monkeypatch.setattr(loader, "inspect", lambda _connection: FakeInspector(tables))
    connection = FakeConnection(metadata=metadata)
    loader.initialize(connection)
    return connection


def test_initialize_creates_a_fresh_warehouse(monkeypatch):
    connection = _initialize(monkeypatch, {})

    assert _ran(connection, "schema_migrations")
    assert not _ran(connection, "pipeline_metadata WHERE singleton")


def test_initialize_upgrades_a_version_one_warehouse(monkeypatch):
    tables = {"analytics": ["pipeline_metadata", "fact_sales"], "raw": [], "staging": []}
    connection = _initialize(monkeypatch, tables, metadata=(loader.OWNER, 1))

    migration = loader.read_statements("migrations/002_variable_costs.sql")
    assert all(statement in connection.statements for statement in migration)


@pytest.mark.parametrize(
    ("tables", "metadata", "message"),
    [
        ({"analytics": ["fact_sales"]}, None, "not owned by this project"),
        ({"analytics": ["pipeline_metadata"]}, None, "Unknown warehouse"),
        ({"analytics": ["pipeline_metadata"]}, ("someone-else", 2), "Unknown warehouse"),
        ({"analytics": ["pipeline_metadata"]}, (loader.OWNER, 3), "Unknown warehouse"),
        (
            {"analytics": ["pipeline_metadata"], "raw": ["notes"]},
            (loader.OWNER, 2),
            "Unexpected tables",
        ),
    ],
)
def test_initialize_refuses_schemas_it_does_not_own(monkeypatch, tables, metadata, message):
    with pytest.raises(ValueError, match=message):
        _initialize(monkeypatch, tables, metadata)
