CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS analytics.pipeline_metadata (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    owner text NOT NULL CHECK (owner = 'sales-profitability-intelligence'),
    contract_version integer NOT NULL CHECK (contract_version IN (1,2)),
    completed_at timestamptz
);
INSERT INTO analytics.pipeline_metadata(singleton, owner, contract_version)
VALUES (true, 'sales-profitability-intelligence', 2) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS analytics.schema_migrations (
    version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT current_timestamp
);
