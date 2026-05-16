CREATE TABLE IF NOT EXISTS industry_jobs (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_industry_jobs_updated_at ON industry_jobs (updated_at);
