CREATE TABLE IF NOT EXISTS documents (
    id                 UUID PRIMARY KEY,
    title              TEXT NOT NULL,
    original_filename  TEXT NOT NULL,
    content_type       TEXT NOT NULL,
    category           TEXT NOT NULL,
    technology         TEXT NOT NULL,
    version            TEXT NOT NULL,
    author             TEXT NOT NULL,
    processing_status  TEXT NOT NULL DEFAULT 'uploaded'
        CHECK (processing_status IN ('uploaded', 'processing', 'indexed', 'failed')),
    processing_error   TEXT,
    blob_container     TEXT NOT NULL,
    blob_name          TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents (processing_status);
