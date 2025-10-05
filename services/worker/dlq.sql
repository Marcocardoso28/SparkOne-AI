-- Dead-letter queue and job event audit tables for the worker service.

CREATE TABLE IF NOT EXISTS worker_dlq (
    id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}'::TEXT,
    error_message TEXT NOT NULL,
    scheduled_for TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_worker_dlq_job_name ON worker_dlq (job_name);
CREATE INDEX IF NOT EXISTS idx_worker_dlq_retry_count ON worker_dlq (retry_count);

CREATE TABLE IF NOT EXISTS worker_job_events (
    id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
    runtime_seconds DOUBLE PRECISION NOT NULL,
    payload TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_worker_job_events_job_name ON worker_job_events (job_name);
CREATE INDEX IF NOT EXISTS idx_worker_job_events_created_at ON worker_job_events (created_at DESC);
