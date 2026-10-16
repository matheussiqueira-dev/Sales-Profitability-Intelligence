"""Serialize warehouse writers and publishers across the commit boundary."""

from contextlib import contextmanager

from sqlalchemy import text

PIPELINE_LOCK = 831024915


@contextmanager
def warehouse_lease(engine):
    """Hold a physical session lock through publication, then release before pooling."""
    with engine.connect() as connection:
        locked = connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": PIPELINE_LOCK}
        ).scalar_one()
        try:
            connection.commit()
        except Exception:
            # A commit failure after acquiring a session lock must not return it to the pool.
            connection.invalidate()
            raise
        if not locked:
            raise RuntimeError("Another pipeline is loading this database or publishing exports")
        try:
            yield connection
        finally:
            try:
                connection.rollback()
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": PIPELINE_LOCK})
                connection.commit()
            except Exception:
                connection.invalidate()
                raise
